import locale

import pandas as pd
import pytest

from deribit_wrapper.exceptions import PriceUnavailableError
from deribit_wrapper.market_data import (
    MarketData,
    name_future,
    name_instrument,
    name_option,
)


@pytest.fixture(autouse=True)
def _force_c_time_locale():
    """Pin LC_TIME to the C locale so %b renders English month abbreviations."""
    previous = locale.setlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, "C")
    yield
    locale.setlocale(locale.LC_TIME, previous)


@pytest.fixture
def market_data():
    return MarketData(env="test", client_id="dummy_id", client_secret="dummy_secret")


def make_request_mock(mocker, market_data, responses):
    """Patch _request to answer by URI from a dict, recording calls."""
    calls = []

    def fake_request(uri, params, give_results=True):
        calls.append((uri, dict(params)))
        value = responses[uri]
        return value(params) if callable(value) else value

    mocker.patch.object(market_data, "_request", side_effect=fake_request)
    return calls


def test_name_future():
    assert name_future("BTC", "2024-03-29") == "BTC-29MAR24"


def test_name_future_single_digit_day_not_padded():
    assert name_future("ETH", "2024-03-05") == "ETH-5MAR24"


def test_name_option_call_with_integer_strike():
    assert name_option("BTC", "2024-03-29", 50000.0, "call") == "BTC-29MAR24-50000-C"


def test_name_option_put_with_decimal_strike():
    assert name_option("ETH", "2024-03-29", 2450.5, "put") == "ETH-29MAR24-2450.5-P"


def test_name_instrument_without_strike_is_future_name():
    assert name_instrument("BTC", "2024-03-29") == name_future("BTC", "2024-03-29")


def test_get_contract_size(mocker, market_data):
    make_request_mock(
        mocker, market_data, {"/public/get_contract_size": {"contract_size": 10}}
    )
    assert market_data.get_contract_size("BTC-PERPETUAL") == 10


def test_get_contract_size_missing_key_returns_empty(mocker, market_data):
    make_request_mock(mocker, market_data, {"/public/get_contract_size": {}})
    assert market_data.get_contract_size("UNKNOWN") == {}


def test_currencies_sorted(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_currencies": [
                {"currency": "ETH"},
                {"currency": "BTC"},
                {"currency": "USDC"},
            ]
        },
    )
    assert market_data.currencies == ["BTC", "ETH", "USDC"]


def test_get_instrument_getters(mocker, market_data):
    instrument = {
        "instrument_name": "BTC-29MAR24",
        "base_currency": "BTC",
        "min_trade_amount": 0.1,
        "kind": "future",
        "expiration_timestamp": 1711699200000,
    }
    make_request_mock(mocker, market_data, {"/public/get_instrument": instrument})
    assert market_data.get_base_currency("BTC-29MAR24") == "BTC"
    assert market_data.get_min_trade_amount("BTC-29MAR24") == 0.1
    assert market_data.get_kind("BTC-29MAR24") == "future"
    assert market_data.get_expiry_timestamp("BTC-29MAR24") == 1711699200000
    assert market_data.get_expiry_date("BTC-29MAR24") == pd.Timestamp(
        "2024-03-29 08:00:00"
    )


def test_get_instruments_dedups_expired_and_active(mocker, market_data):
    rows = [
        {
            "instrument_name": "BTC-29MAR24",
            "kind": "future",
            "base_currency": "BTC",
            "expiration_timestamp": 2,
        },
        {
            "instrument_name": "BTC-28JUN24",
            "kind": "future",
            "base_currency": "BTC",
            "expiration_timestamp": 3,
        },
    ]
    # same payload returned for expired=False and expired=True: must dedup
    make_request_mock(mocker, market_data, {"/public/get_instruments": rows})
    df = market_data.get_instruments(currencies="BTC")
    assert len(df) == 2
    assert list(df["instrument_name"]) == ["BTC-29MAR24", "BTC-28JUN24"]


def test_get_instruments_as_list(mocker, market_data):
    rows = [
        {
            "instrument_name": "BTC-29MAR24",
            "kind": "future",
            "base_currency": "BTC",
            "expiration_timestamp": 2,
        }
    ]
    make_request_mock(mocker, market_data, {"/public/get_instruments": rows})
    assert market_data.get_instruments(currencies="BTC", as_list=True) == [
        "BTC-29MAR24"
    ]


def test_get_instruments_as_list_empty(mocker, market_data):
    make_request_mock(mocker, market_data, {"/public/get_instruments": []})
    assert market_data.get_instruments(currencies="BTC", as_list=True) == []


def test_get_instruments_kind_forwarded(mocker, market_data):
    calls = make_request_mock(mocker, market_data, {"/public/get_instruments": []})
    market_data.get_instruments(currencies="BTC", kind="option")
    assert all(params["kind"] == "option" for _, params in calls)


def test_last_price(mocker, market_data):
    make_request_mock(mocker, market_data, {"/public/ticker": {"last_price": 42000.5}})
    assert market_data.last_price("BTC-PERPETUAL") == 42000.5


def test_last_price_falls_back_to_mark_price(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {"/public/ticker": {"last_price": None, "mark_price": 41000.0}},
    )
    assert market_data.last_price("BTC-PERPETUAL") == 41000.0


def test_last_price_unavailable_raises(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {"/public/ticker": {"last_price": None, "mark_price": None}},
    )
    with pytest.raises(PriceUnavailableError):
        market_data.last_price("BTC-PERPETUAL")


def test_mid_price(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {"/public/ticker": {"best_bid_price": 100.0, "best_ask_price": 102.0}},
    )
    assert market_data.mid_price("BTC-PERPETUAL") == 101.0


def test_mid_price_only_bid(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {"/public/ticker": {"best_bid_price": 100.0, "best_ask_price": None}},
    )
    assert market_data.mid_price("BTC-PERPETUAL") == 100.0


def test_mid_price_only_ask(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {"/public/ticker": {"best_bid_price": None, "best_ask_price": 102.0}},
    )
    assert market_data.mid_price("BTC-PERPETUAL") == 102.0


def test_mid_price_falls_back_to_mark(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {
            "/public/ticker": {
                "best_bid_price": None,
                "best_ask_price": None,
                "mark_price": 99.0,
            }
        },
    )
    assert market_data.mid_price("BTC-PERPETUAL") == 99.0


def test_check_min_trade_amount_passes(mocker, market_data):
    def fresh_df():
        # min_trade_amount() calls set_index(inplace=True) on the returned
        # frame, so each call needs its own copy
        return pd.DataFrame(
            {"instrument_name": ["BTC-PERPETUAL"], "min_trade_amount": [10.0]}
        )

    mocker.patch.object(
        market_data, "get_instruments", side_effect=lambda *a, **k: fresh_df()
    )
    assert market_data.check_min_trade_amount([("BTC-PERPETUAL", 10)])
    assert market_data.check_min_trade_amount([("BTC-PERPETUAL", -20)])


def test_check_min_trade_amount_fails_below_minimum(mocker, market_data):
    df = pd.DataFrame(
        {"instrument_name": ["BTC-PERPETUAL"], "min_trade_amount": [10.0]}
    )
    mocker.patch.object(market_data, "get_instruments", return_value=df)
    assert not market_data.check_min_trade_amount([("BTC-PERPETUAL", 5)])


def test_get_nth_future_picks_nearest_valid_expiry(mocker, market_data):
    ref = pd.Timestamp("2024-01-01")
    far = pd.Timestamp("2024-06-28").timestamp() * 1000
    near = pd.Timestamp("2024-03-29").timestamp() * 1000
    too_close = pd.Timestamp("2024-01-01T12:00").timestamp() * 1000
    df = pd.DataFrame(
        {
            "instrument_name": ["BTC-1JAN24", "BTC-29MAR24", "BTC-28JUN24"],
            "quote_currency": ["USD", "USD", "USD"],
            "is_active": [True, True, True],
            "expiration_timestamp": [too_close, near, far],
        }
    )
    mocker.patch.object(market_data, "get_future_instruments", return_value=df)
    assert market_data.get_first_future("BTC", ref_date=ref) == "BTC-29MAR24"
    assert market_data.get_nth_future("BTC", n=2, ref_date=ref) == "BTC-28JUN24"


def test_get_nth_future_empty_returns_none(mocker, market_data):
    mocker.patch.object(
        market_data, "get_future_instruments", return_value=pd.DataFrame()
    )
    assert market_data.get_first_future("BTC") is None


def test_get_market_data_history(mocker, market_data):
    ticks = [1704067200000, 1704153600000]
    make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_tradingview_chart_data": {
                "status": "ok",
                "ticks": ticks,
                "open": [100.0, 101.0],
                "close": [101.0, 102.0],
            }
        },
    )
    df = market_data.get_market_data_history(
        "BTC-PERPETUAL", start_date="2024-01-01", end_date="2024-01-02"
    )
    assert df.index.name == "date"
    assert len(df) == 2
    assert list(df["close"]) == [101.0, 102.0]


def test_get_market_data_history_no_data(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {"/public/get_tradingview_chart_data": {"status": "no_data"}},
    )
    df = market_data.get_market_data_history("BTC-PERPETUAL")
    assert df.empty


def test_get_market_book_by_currency(mocker, market_data):
    calls = make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_book_summary_by_currency": [
                {"instrument_name": "BTC-PERPETUAL", "mark_price": 42000.0}
            ]
        },
    )
    df = market_data.get_market_book(currency="BTC")
    assert calls == [("/public/get_book_summary_by_currency", {"currency": "BTC"})]
    assert list(df["instrument_name"]) == ["BTC-PERPETUAL"]


def test_get_market_book_by_currency_list(mocker, market_data):
    calls = make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_book_summary_by_currency": lambda params: [
                {"instrument_name": f"{params['currency']}-PERPETUAL"}
            ]
        },
    )
    df = market_data.get_market_book(currency=["BTC", "ETH"])
    assert [params["currency"] for _, params in calls] == ["BTC", "ETH"]
    assert list(df["instrument_name"]) == ["BTC-PERPETUAL", "ETH-PERPETUAL"]


def test_get_market_book_by_instrument(mocker, market_data):
    calls = make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_book_summary_by_instrument": lambda params: [
                {"instrument_name": params["instrument_name"]}
            ]
        },
    )
    df = market_data.get_market_book(instrument=["BTC-PERPETUAL", "ETH-PERPETUAL"])
    assert [params["instrument_name"] for _, params in calls] == [
        "BTC-PERPETUAL",
        "ETH-PERPETUAL",
    ]
    assert list(df["instrument_name"]) == ["BTC-PERPETUAL", "ETH-PERPETUAL"]


def test_get_market_book_single_instrument_string(mocker, market_data):
    make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_book_summary_by_instrument": [
                {"instrument_name": "BTC-PERPETUAL"}
            ]
        },
    )
    df = market_data.get_market_book(instrument="BTC-PERPETUAL")
    assert list(df["instrument_name"]) == ["BTC-PERPETUAL"]


def test_get_market_book_without_args_raises(market_data):
    with pytest.raises(ValueError, match="Either 'currency' or 'instrument'"):
        market_data.get_market_book()


def test_get_complete_market_book_covers_all_currencies(mocker, market_data):
    mocker.patch.object(
        type(market_data),
        "currencies",
        new_callable=mocker.PropertyMock,
        return_value=["BTC", "ETH"],
    )
    calls = make_request_mock(
        mocker,
        market_data,
        {
            "/public/get_book_summary_by_currency": lambda params: [
                {"instrument_name": f"{params['currency']}-PERPETUAL"}
            ]
        },
    )
    df = market_data.get_complete_market_book()
    assert [params["currency"] for _, params in calls] == ["BTC", "ETH"]
    assert len(df) == 2
