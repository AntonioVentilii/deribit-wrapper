import pandas as pd
import pytest

from deribit_wrapper.account_management import AccountManagement
from deribit_wrapper.exceptions import (
    SubaccountAlreadyRemoved,
    SubaccountError,
    SubaccountNameAlreadyTaken,
    SubaccountNameWrongFormat,
    SubaccountNotRemovable,
    WaitRequiredError,
)


@pytest.fixture
def account():
    return AccountManagement(
        env="test", client_id="dummy_id", client_secret="dummy_secret"
    )


def record_requests(mocker, client, response=None):
    calls = []

    def fake_request(uri, params, give_results=True):
        calls.append((uri, dict(params)))
        if callable(response):
            return response(uri, dict(params))
        return {} if response is None else response

    mocker.patch.object(client, "_request", side_effect=fake_request)
    return calls


def test_get_account_summary_single_currency(mocker, account):
    record_requests(
        mocker, account, response={"currency": "BTC", "equity": 1.5, "balance": 1.4}
    )
    df = account.get_account_summary(currency="BTC")
    assert len(df) == 1
    assert df.columns[0] == "currency"
    assert df["equity"].iloc[0] == 1.5


def test_get_account_summary_multiple_currencies(mocker, account):
    record_requests(
        mocker,
        account,
        response=lambda uri, params: {"currency": params["currency"], "equity": 1.0},
    )
    df = account.get_account_summary(currency=["BTC", "ETH"])
    assert list(df["currency"]) == ["BTC", "ETH"]


def test_get_account_summary_forwards_subaccount_id(mocker, account):
    calls = record_requests(
        mocker, account, response={"currency": "BTC", "equity": 1.0}
    )
    account.get_account_summary(currency="BTC", subaccount_id=7)
    assert calls[0][1]["subaccount_id"] == 7


def test_get_margin_model_selects_columns(mocker, account):
    summary = pd.DataFrame(
        {
            "currency": ["BTC"],
            "margin_model": ["segregated_sm"],
            "portfolio_margining_enabled": [False],
            "cross_collateral_enabled": [False],
            "equity": [1.0],
        }
    )
    mocker.patch.object(account, "get_account_summary", return_value=summary)
    df = account.get_margin_model()
    assert list(df.columns) == [
        "currency",
        "margin_model",
        "portfolio_margining_enabled",
        "cross_collateral_enabled",
    ]


def test_list_api_keys(mocker, account):
    record_requests(
        mocker,
        account,
        response=[{"id": 1, "name": "key1"}, {"id": 2, "name": "key2"}],
    )
    df = account.list_api_keys()
    assert list(df["id"]) == [1, 2]


def test_get_api_key(mocker, account):
    keys = pd.DataFrame([{"id": 1, "name": "key1"}, {"id": 2, "name": "key2"}])
    mocker.patch.object(account, "list_api_keys", return_value=keys)
    key = account.get_api_key(2)
    assert key == {"id": 2, "name": "key2"}


def test_create_api_key_params(mocker, account):
    calls = record_requests(mocker, account, response={"id": 3})
    account.create_api_key("trade:read_write", name="bot")
    assert calls == [
        ("/private/create_api_key", {"max_scope": "trade:read_write", "name": "bot"})
    ]


def test_api_key_lifecycle_params(mocker, account):
    calls = record_requests(mocker, account, response={})
    account.enable_api_key(5)
    account.disable_api_key(5)
    account.remove_api_key(5)
    assert [uri for uri, _ in calls] == [
        "/private/enable_api_key",
        "/private/disable_api_key",
        "/private/remove_api_key",
    ]
    assert all(params == {"id": 5} for _, params in calls)


def test_get_subaccounts(mocker, account):
    record_requests(mocker, account, response=[{"id": 1, "email": "a@b.c"}, {"id": 2}])
    df = account.get_subaccounts()
    assert list(df["id"]) == [1, 2]


def test_get_subaccount_found(mocker, account):
    record_requests(mocker, account, response=[{"id": 1}, {"id": 2, "email": "x"}])
    assert account.get_subaccount(2) == {"id": 2, "email": "x"}


def test_get_subaccount_missing_raises(mocker, account):
    record_requests(mocker, account, response=[{"id": 1}])
    with pytest.raises(ValueError, match="Subaccount 99 not found"):
        account.get_subaccount(99)


def test_change_subaccount_name_too_long_raises(account):
    with pytest.raises(ValueError, match="too long"):
        account.change_subaccount_name(1, "x" * 33)


def test_change_subaccount_name_success(mocker, account):
    calls = record_requests(mocker, account, response={"result": "ok"})
    ret = account.change_subaccount_name(1, "new-name")
    assert calls == [
        ("/private/change_subaccount_name", {"sid": 1, "name": "new-name"})
    ]
    assert ret == {"result": "ok"}


def test_change_subaccount_name_already_taken(mocker, account):
    record_requests(mocker, account, response={"code": 12002, "data": "already_taken"})
    with pytest.raises(SubaccountNameAlreadyTaken):
        account.change_subaccount_name(1, "taken")


def test_change_subaccount_name_wrong_format(mocker, account):
    record_requests(mocker, account, response={"code": 12002, "data": "wrong_format"})
    with pytest.raises(SubaccountNameWrongFormat):
        account.change_subaccount_name(1, "bad name")


def test_change_subaccount_name_other_12002(mocker, account):
    record_requests(mocker, account, response={"code": 12002, "data": "other"})
    with pytest.raises(SubaccountError):
        account.change_subaccount_name(1, "name")


def test_remove_subaccount_success(mocker, account):
    calls = record_requests(mocker, account, response={"result": "ok"})
    ret = account.remove_subaccount(4)
    assert calls == [("/private/remove_subaccount", {"subaccount_id": 4})]
    assert ret == {"result": "ok"}


def test_remove_subaccount_wait_required(mocker, account):
    record_requests(mocker, account, response={"code": 12006, "data": {"wait": 30}})
    with pytest.raises(WaitRequiredError, match="30 seconds"):
        account.remove_subaccount(4)


def test_remove_subaccount_not_removable(mocker, account):
    record_requests(
        mocker, account, response={"code": 12007, "data": {"reason": "has_balance"}}
    )
    with pytest.raises(SubaccountNotRemovable, match="has_balance"):
        account.remove_subaccount(4)


def test_remove_subaccount_already_removed(mocker, account):
    record_requests(
        mocker,
        account,
        response={"code": 13009, "data": {"reason": "already_removed"}},
    )
    with pytest.raises(SubaccountAlreadyRemoved):
        account.remove_subaccount(4)


def test_remove_subaccount_unauthorized(mocker, account):
    record_requests(
        mocker, account, response={"code": 13009, "data": {"reason": "denied"}}
    )
    with pytest.raises(SubaccountError, match="denied"):
        account.remove_subaccount(4)


def test_get_positions_per_currency(mocker, account):
    calls = record_requests(
        mocker,
        account,
        response=lambda uri, params: [
            {"instrument_name": f"{params['currency']}-PERPETUAL", "size": 1}
        ],
    )
    df = account.get_positions(currency=["BTC", "ETH"], kind="future")
    assert [params["currency"] for _, params in calls] == ["BTC", "ETH"]
    assert all(params["kind"] == "future" for _, params in calls)
    assert list(df["instrument_name"]) == ["BTC-PERPETUAL", "ETH-PERPETUAL"]


def test_get_transaction_log_paginates(mocker, account):
    pages = [
        {"logs": [{"id": 1, "type": "trade"}], "continuation": 123},
        {"logs": [{"id": 2, "type": "trade"}], "continuation": None},
    ]
    calls = record_requests(
        mocker, account, response=lambda uri, params: pages[len(calls) - 1]
    )
    df = account.get_transaction_log(
        start="2024-01-01", end="2024-01-31", currency="BTC", query="trade"
    )
    assert len(calls) == 2
    assert "continuation" not in calls[0][1]
    assert calls[1][1]["continuation"] == 123
    assert list(df["id"]) == [1, 2]


def test_get_transaction_log_query_and_range_params(mocker, account):
    calls = record_requests(
        mocker, account, response={"logs": [], "continuation": None}
    )
    account.get_transaction_log(
        start="2024-01-01", end="2024-01-31", currency="BTC", query="trade"
    )
    _, params = calls[0]
    assert params["query"] == "trade"
    assert params["currency"] == "BTC"
    assert params["start_timestamp"] == 1704067200000
    assert params["end_timestamp"] == 1706659200000


def test_get_delivery_log_uses_delivery_query(mocker, account):
    log = mocker.patch.object(
        account, "get_transaction_log", return_value=pd.DataFrame()
    )
    account.get_delivery_log(start="2024-01-01", end="2024-01-31", currency="BTC")
    log.assert_called_once_with("2024-01-01", "2024-01-31", "BTC", query="delivery")


def test_get_flow_history_uses_deposit_and_transfer(mocker, account):
    log = mocker.patch.object(
        account, "get_transaction_log", return_value=pd.DataFrame()
    )
    account.get_flow_history(start="2024-01-01", end="2024-01-31")
    log.assert_called_once_with(
        "2024-01-01", "2024-01-31", None, query=["deposit", "transfer"]
    )


def test_get_portfolio_margins_groups_by_base_currency(mocker, account):
    mocker.patch.object(
        account,
        "get_base_currency",
        side_effect=lambda instrument: instrument.split("-")[0],
    )
    calls = record_requests(mocker, account, response={"margin": 1.0})
    ret = account.get_portfolio_margins(
        [("BTC-PERPETUAL", 1.0), ("BTC-29MAR24", 2.0), ("ETH-PERPETUAL", 3.0)]
    )
    assert set(ret) == {"BTC", "ETH"}
    by_currency = {params["currency"]: params for _, params in calls}
    assert by_currency["BTC"]["simulated_positions"] == {
        "BTC-PERPETUAL": 1.0,
        "BTC-29MAR24": 2.0,
    }
    assert by_currency["ETH"]["simulated_positions"] == {"ETH-PERPETUAL": 3.0}


def test_check_if_margin_model_change_is_possible(mocker, account):
    columns = pd.MultiIndex.from_tuples(
        [("new_state", "initial_margin_rate"), ("new_state", "maintenance_margin_rate")]
    )
    ok = pd.DataFrame([[0.5, 0.3]], columns=columns)
    mocker.patch.object(account, "_change_margin_model", return_value=ok)
    assert account.check_if_margin_model_change_is_possible("cross_pm")

    not_ok = pd.DataFrame([[1.5, 0.3]], columns=columns)
    mocker.patch.object(account, "_change_margin_model", return_value=not_ok)
    assert not account.check_if_margin_model_change_is_possible("cross_pm")


def test_get_api_key_not_found_raises_value_error(mocker, account):
    keys = pd.DataFrame([{"id": 1, "name": "key1"}])
    mocker.patch.object(account, "list_api_keys", return_value=keys)
    with pytest.raises(ValueError, match="API key 99 not found"):
        account.get_api_key(99)


def test_get_api_key_empty_list_raises_value_error(mocker, account):
    mocker.patch.object(account, "list_api_keys", return_value=pd.DataFrame())
    with pytest.raises(ValueError, match="not found"):
        account.get_api_key(1)
