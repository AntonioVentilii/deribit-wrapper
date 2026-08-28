import pandas as pd
import pytest

from deribit_wrapper.trading import Trading


@pytest.fixture
def trading():
    client = Trading(
        env="test",
        client_id="dummy_id",
        client_secret="dummy_secret",
        simulated=True,
    )
    return client


@pytest.fixture
def live_trading():
    client = Trading(
        env="test",
        client_id="dummy_id",
        client_secret="dummy_secret",
        simulated=False,
    )
    return client


def record_requests(mocker, client, response=None):
    calls = []

    def fake_request(uri, params, give_results=True):
        calls.append((uri, dict(params)))
        if callable(response):
            return response(uri, params)
        return {} if response is None else response

    mocker.patch.object(client, "_request", side_effect=fake_request)
    return calls


def test_simulated_buy_order(mocker, trading):
    mocker.patch.object(trading, "get_kind", return_value="future")
    mocker.patch.object(trading, "last_price", return_value=42000.0)
    ret = trading._order("BTC-PERPETUAL", 10)
    assert ret["side"] == "buy"
    assert ret["amount"] == 10
    assert ret["price"] == 42000.0
    assert ret["instrument_name"] == "BTC-PERPETUAL"
    assert "SIMULATION" in ret["info"]


def test_simulated_sell_order_uses_limit_price(mocker, trading):
    mocker.patch.object(trading, "get_kind", return_value="future")
    last_price = mocker.patch.object(trading, "last_price")
    ret = trading._order("BTC-PERPETUAL", -5, limit=41000.0)
    assert ret["side"] == "sell"
    assert ret["amount"] == 5
    assert ret["price"] == 41000.0
    last_price.assert_not_called()


def test_zero_amount_order_is_noop(trading):
    assert trading._order("BTC-PERPETUAL", 0) == {}


def test_simulated_order_never_hits_api(mocker, trading):
    calls = record_requests(mocker, trading)
    mocker.patch.object(trading, "get_kind", return_value="future")
    mocker.patch.object(trading, "last_price", return_value=42000.0)
    trading._order("BTC-PERPETUAL", 1)
    assert calls == []


def test_live_buy_order_params(mocker, live_trading):
    calls = record_requests(mocker, live_trading)
    ret = live_trading._order("BTC-PERPETUAL", 10)
    assert len(calls) == 1
    uri, params = calls[0]
    assert uri == "/private/buy"
    assert params["instrument_name"] == "BTC-PERPETUAL"
    assert params["amount"] == 10
    assert params["type"] == "market"
    assert ret == {}


def test_live_sell_limit_order_params(mocker, live_trading):
    calls = record_requests(mocker, live_trading)
    live_trading._order("BTC-PERPETUAL", -10, limit=45000.0, label="my-label")
    uri, params = calls[0]
    assert uri == "/private/sell"
    assert params["amount"] == 10
    assert params["type"] == "limit"
    assert params["price"] == 45000.0
    assert params["label"] == "my-label"


def test_live_order_empty_label_dropped(mocker, live_trading):
    calls = record_requests(mocker, live_trading)
    live_trading._order("BTC-PERPETUAL", 1, label="")
    _, params = calls[0]
    assert "label" not in params


def test_order_swallows_exceptions(mocker, trading):
    mocker.patch.object(trading, "check_min_trade_amount", return_value=True)
    mocker.patch.object(trading, "_order", side_effect=RuntimeError("boom"))
    ret = trading.order("BTC-PERPETUAL", 1)
    assert ret == {"error": "boom"}


def test_market_order_delegates_to_order(mocker, trading):
    order = mocker.patch.object(trading, "order", return_value={"ok": True})
    ret = trading.market_order("BTC-PERPETUAL", 3, label="x")
    order.assert_called_once_with("BTC-PERPETUAL", 3, label="x", reduce_only=False)
    assert ret == {"ok": True}


def test_bulk_order_mixes_market_and_limit(mocker, trading):
    mocker.patch.object(trading, "check_min_trade_amount", return_value=True)
    submitted = []
    mocker.patch.object(
        trading,
        "_order",
        side_effect=lambda asset, amount, limit=None, label=None: submitted.append(
            (asset, amount, limit)
        ),
    )
    trading.bulk_order([("BTC-PERPETUAL", 1), ("ETH-PERPETUAL", -2, 2500.0)])
    assert submitted == [
        ("BTC-PERPETUAL", 1, None),
        ("ETH-PERPETUAL", -2, 2500.0),
    ]


def test_error_handler_retries_as_reduce_only(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"code": 10009})
    ret = live_trading._order_with_error_handling(
        "/private/buy", {"instrument_name": "BTC-PERPETUAL", "amount": 1}
    )
    assert len(calls) == 2
    assert calls[1][1]["reduce_only"] is True
    assert ret == {"code": 10009}


def test_error_handler_no_error_passthrough(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"order": {"id": 1}})
    ret = live_trading._order_with_error_handling("/private/buy", {"amount": 1})
    assert len(calls) == 1
    assert ret == {"order": {"id": 1}}


def test_instrument_margin_buy_and_sell(mocker, trading):
    mocker.patch.object(
        trading, "instrument_margins", return_value={"buy": 0.1, "sell": 0.2}
    )
    assert trading.instrument_margin("BTC-PERPETUAL", amount=1) == 0.1
    assert trading.instrument_margin("BTC-PERPETUAL", amount=-1) == 0.2
    assert trading.instrument_buy_margin("BTC-PERPETUAL") == 0.1
    assert trading.instrument_sell_margin("BTC-PERPETUAL") == 0.2


def test_instrument_margins_fetches_price_if_missing(mocker, trading):
    calls = record_requests(mocker, trading, response={"buy": 0.1, "sell": 0.2})
    mocker.patch.object(trading, "last_price", return_value=40000.0)
    trading.instrument_margins("BTC-PERPETUAL", amount=2)
    uri, params = calls[0]
    assert uri == "/private/get_margins"
    assert params == {
        "instrument_name": "BTC-PERPETUAL",
        "amount": 2,
        "price": 40000.0,
    }


def test_close_position_market(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={})
    live_trading.close_position("BTC-PERPETUAL")
    uri, params = calls[0]
    assert uri == "/private/close_position"
    assert params == {"instrument_name": "BTC-PERPETUAL", "type": "market"}


def test_close_position_limit(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={})
    live_trading.close_position("BTC-PERPETUAL", limit=42000.0)
    _, params = calls[0]
    assert params["type"] == "limit"
    assert params["price"] == 42000.0


def test_cancel_orders_by_label_without_currency(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"cancelled": 1})
    ret = live_trading.cancel_orders(label="my-label")
    assert calls == [("/private/cancel_by_label", {"label": "my-label"})]
    assert ret == {"cancelled": 1}


def test_cancel_orders_by_label_per_currency(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"cancelled": 1})
    ret = live_trading.cancel_orders(label="my-label", currency=["BTC", "ETH"])
    assert [params["currency"] for _, params in calls] == ["BTC", "ETH"]
    assert set(ret) == {"BTC", "ETH"}


def test_cancel_orders_by_kind_and_type(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"cancelled": 2})
    ret = live_trading.cancel_orders(currency="BTC", kind="option", order_type="limit")
    uri, params = calls[0]
    assert uri == "/private/cancel_all_by_kind_or_type"
    assert params == {"currency": "BTC", "kind": "option", "type": "limit"}
    assert ret == {"BTC": {"cancelled": 2}}


def test_get_open_orders_returns_dataframe(mocker, trading):
    record_requests(
        mocker,
        trading,
        response=[{"order_id": "1", "price": 100.0}, {"order_id": "2", "price": 101.0}],
    )
    df = trading.get_open_orders()
    assert isinstance(df, pd.DataFrame)
    assert list(df["order_id"]) == ["1", "2"]


def test_get_orders_one_request_per_id(mocker, trading):
    calls = record_requests(mocker, trading, response={"order_id": "x"})
    df = trading.get_orders(["a", "b", "c"])
    assert [params["order_id"] for _, params in calls] == ["a", "b", "c"]
    assert len(df) == 3


def test_close_position_simulated_does_not_call_api(mocker, trading):
    calls = record_requests(mocker, trading)
    last_price = mocker.patch.object(trading, "last_price", return_value=42000.0)
    ret = trading.close_position("BTC-PERPETUAL")
    assert calls == []
    # last_price would issue a real ticker request, so a market close must not use it
    last_price.assert_not_called()
    assert "price" not in ret
    assert "SIMULATION" in ret["info"]
    assert ret["instrument_name"] == "BTC-PERPETUAL"


def test_close_position_simulated_uses_limit_price(mocker, trading):
    record_requests(mocker, trading)
    last_price = mocker.patch.object(trading, "last_price")
    ret = trading.close_position("BTC-PERPETUAL", limit=41000.0)
    assert ret["type"] == "limit"
    assert ret["price"] == 41000.0
    last_price.assert_not_called()


def test_cancel_orders_simulated_does_not_call_api(mocker, trading):
    calls = record_requests(mocker, trading)
    ret = trading.cancel_orders(currency="BTC", kind="option")
    assert calls == []
    # same per-currency shape as live mode
    assert set(ret) == {"BTC"}
    assert "SIMULATION" in ret["BTC"]["info"]


def test_cancel_orders_simulated_shape_matches_live(mocker, trading, live_trading):
    record_requests(mocker, trading)
    record_requests(mocker, live_trading, response={"ok": 1})
    simulated = trading.cancel_orders(currency=["BTC", "ETH"])
    live = live_trading.cancel_orders(currency=["BTC", "ETH"])
    assert set(simulated) == set(live)


def test_cancel_by_label_simulated_shape_matches_live(mocker, trading, live_trading):
    record_requests(mocker, trading)
    record_requests(mocker, live_trading, response={"ok": 1})
    simulated = trading.cancel_orders(label="x", currency=["BTC", "ETH"])
    live = live_trading.cancel_orders(label="x", currency=["BTC", "ETH"])
    assert set(simulated) == set(live)


def test_cancel_by_label_simulated_does_not_call_api(mocker, trading):
    calls = record_requests(mocker, trading)
    ret = trading.cancel_orders(label="my-label")
    assert calls == []
    assert "SIMULATION" in ret["info"]
    assert ret["label"] == "my-label"


def test_simulated_trading_never_touches_private_endpoints(mocker, trading):
    """Simulated calls may read public data, but must never hit /private."""
    calls = record_requests(
        mocker, trading, response=lambda uri, params: [{"currency": "BTC"}]
    )
    trading.cancel_orders()
    trading.cancel_orders(label="x")
    trading.close_position("BTC-PERPETUAL")
    private = [uri for uri, _ in calls if uri.startswith("/private")]
    assert private == []


def test_cancel_orders_simulated_no_currency_uses_account_currencies(mocker, trading):
    calls = record_requests(mocker, trading)
    mocker.patch.object(
        type(trading),
        "currencies",
        new_callable=mocker.PropertyMock,
        return_value=["BTC", "ETH"],
    )
    ret = trading.cancel_orders()
    assert calls == []
    assert set(ret) == {"BTC", "ETH"}


def test_close_position_live_still_executes(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"ok": 1})
    live_trading.close_position("BTC-PERPETUAL")
    assert calls[0][0] == "/private/close_position"


def test_cancel_orders_live_still_executes(mocker, live_trading):
    calls = record_requests(mocker, live_trading, response={"ok": 1})
    live_trading.cancel_orders(currency="BTC")
    assert calls[0][0] == "/private/cancel_all_by_kind_or_type"


def test_error_handler_logs_instead_of_printing(mocker, live_trading, caplog, capsys):
    """Test that handled errors go to logging, not the caller's stdout."""
    record_requests(mocker, live_trading, response={"code": 99999})
    with caplog.at_level("ERROR", logger="deribit_wrapper.trading"):
        live_trading._order_with_error_handling("/private/buy", {"amount": 1})
    assert "99999" in caplog.text
    assert capsys.readouterr().out == ""
