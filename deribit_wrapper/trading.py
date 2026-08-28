"""Trading operations: orders, margins, cancellations, and trade history."""

from __future__ import absolute_import, annotations

import logging

import time
from datetime import datetime

from typing import Optional, Any

import pandas as pd
from progressbar import progressbar

from .account_management import AccountManagement
from .utilities import DEFAULT_END, DEFAULT_START, OrdersType

logger = logging.getLogger(__name__)

SIMULATION_INFO = "SIMULATION MODE - no trade executed"


class Trading(AccountManagement):
    """Place, query, and cancel orders; simulated=True builds order results locally instead of submitting them."""

    __GET_TRADE_BY_ORDER = "/private/get_user_trades_by_order"
    __GET_ORDER_STATE = "/private/get_order_state"
    __GET_OPEN_ORDERS = "/private/get_open_orders"
    __BUY = "/private/buy"
    __SELL = "/private/sell"
    __CANCEL_ALL_BY_KIND_OR_TYPE = "/private/cancel_all_by_kind_or_type"
    __CANCEL_BY_LABEL = "/private/cancel_by_label"
    __CLOSE_POSITION = "/private/close_position"
    __GET_MARGINS = "/private/get_margins"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        env: str = "prod",
        private_key: str | bytes | Any | None = None,
        auth_method: str = "credentials",
        private_key_password: str | bytes | None = None,
        progress_bar_desc: Optional[str] = None,
        simulated: bool = True,
    ):
        """Create a trading client; simulated=True disables live order placement."""
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            env=env,
            private_key=private_key,
            auth_method=auth_method,
            private_key_password=private_key_password,
            progress_bar_desc=progress_bar_desc,
        )
        self.simulated = simulated

    def instrument_margins(
        self, instrument: str, amount: float | int = 1, price: Optional[float] = None
    ) -> dict:
        """Return buy and sell margins for an instrument at a price."""
        if price is None:
            price = self.last_price(instrument)
        uri = self.__GET_MARGINS
        params = {"instrument_name": instrument, "amount": amount, "price": price}
        ret = self._request(uri, params)
        return ret

    def instrument_margin(
        self, instrument: str, amount: float | int = 1, price: Optional[float] = None
    ) -> float:
        """Return the buy margin for positive amounts and the sell margin otherwise."""
        side = "buy" if amount > 0 else "sell"
        return self.instrument_margins(instrument, amount=abs(amount), price=price)[
            side
        ]

    def instrument_buy_margin(
        self, instrument: str, amount: float | int = 1, price: Optional[float] = None
    ) -> float:
        """Return the buy margin for an instrument."""
        return self.instrument_margins(instrument, amount=amount, price=price)["buy"]

    def instrument_sell_margin(
        self, instrument: str, amount: float | int = 1, price: Optional[float] = None
    ) -> float:
        """Return the sell margin for an instrument."""
        return self.instrument_margins(instrument, amount=amount, price=price)["sell"]

    def get_trade_by_order(self, order_ids: list[str | int]) -> pd.DataFrame:
        """Return the trades belonging to the given order ids as a DataFrame."""
        uri = self.__GET_TRADE_BY_ORDER
        results = []
        prefix = (
            f"{self.progress_bar_desc}: Trades by order"
            if self.progress_bar_desc
            else "Trades by order"
        )
        for order_id in progressbar(order_ids, prefix=prefix, redirect_stdout=True):
            params = {"order_id": order_id}
            results += self._request(uri, params)
        ret = pd.DataFrame(results)
        return ret

    def get_orders(self, order_ids: list[str | int]) -> pd.DataFrame:
        """Return the state of the given orders as a DataFrame."""
        uri = self.__GET_ORDER_STATE
        results = []
        prefix = (
            f"{self.progress_bar_desc}: Orders" if self.progress_bar_desc else "Orders"
        )
        for order_id in progressbar(order_ids, prefix=prefix, redirect_stdout=True):
            params = {"order_id": order_id}
            results.append(self._request(uri, params))
        ret = pd.DataFrame(results)
        return ret

    def get_open_orders(self) -> pd.DataFrame:
        """Return all open orders as a DataFrame."""
        uri = self.__GET_OPEN_ORDERS
        r = self._request(uri, {})
        df = pd.DataFrame(r)
        return df

    def add_order_data(self, trades: pd.DataFrame) -> pd.DataFrame:
        """Merge order details onto a trades DataFrame by order id."""
        order_ids = list(set(trades["order_id"]))
        orders = self.get_orders(order_ids)
        trades = trades.merge(
            orders,
            how="left",
            on="order_id",
            suffixes=(None, "_duplicate_from_orders_data"),
        )
        return trades

    def get_trade_history(
        self,
        start: Optional[str | datetime] = None,
        end: Optional[str | datetime] = None,
        currency: Optional[str | list[str]] = None,
        include_order_data: bool = False,
    ) -> pd.DataFrame:
        """Return trades for a period, optionally enriched with order data."""
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        results = self.get_transaction_log(start, end, currency, query="trade")
        if not results.empty:
            if include_order_data:
                results = self.add_order_data(results)
            results.sort_values("timestamp", inplace=True)
            results["id"] = results["id"].astype(int, errors="ignore")
        return results

    def get_entire_trade_history(
        self, include_order_data: bool = False
    ) -> pd.DataFrame:
        """Return the full trade history of the account."""
        return self.get_trade_history(include_order_data=include_order_data)

    def _error_handler(
        self,
        ret: dict,
        uri: str,
        params: dict,
        exclude_codes: Optional[list[int]] = None,
    ) -> dict:
        exclude_codes = exclude_codes or []
        code = ret.get("code")

        if code in exclude_codes:
            return ret

        # 0: no error
        if code == 0 or code is None:
            pass

        # 10009: not enough funds
        elif code == 10009:
            if params.get("reduce_only"):
                logger.warning("Not enough funds. Already tried as reduce only.")
            else:
                logger.warning("Not enough funds. Attempt as reduce only...")
                params["reduce_only"] = True
                ret = self._order_with_error_handling(
                    uri, params, exclude_codes=[10009]
                )

        else:
            logger.error("Error code %s not handled yet.", code)

        return ret

    def _order_with_error_handling(
        self,
        uri: str,
        params: dict,
        handle_error: bool = True,
        exclude_codes: Optional[list[int]] = None,
    ) -> dict:
        ret = self._request(uri, params)
        if handle_error:
            ret = self._error_handler(ret, uri, params, exclude_codes=exclude_codes)
        return ret

    def _order(
        self,
        asset: str,
        amount: float | int,
        limit: Optional[float | int] = None,
        label: Optional[str] = None,
        reduce_only: bool = False,
    ) -> dict:
        label = None if label == "" else label
        if amount > 0:
            uri = self.__BUY
            side = "buy"
        elif amount < 0:
            uri = self.__SELL
            side = "sell"
        else:
            return {}
        if self.simulated:
            ret = {
                "info": SIMULATION_INFO,
                "timestamp": int(time.time() * 1e3),
                "kind": self.get_kind(asset),
                "instrument_name": asset,
                "side": side,
                "amount": abs(amount),
                "price": limit or self.last_price(asset),
                "fee": 0,
                "label": label,
            }
        else:
            params = {
                "instrument_name": asset,
                "amount": abs(amount),
                "type": "market",
                "reduce_only": reduce_only,
            }
            if limit is not None:
                params["type"] = "limit"
                params["price"] = limit
            if label is not None:
                params["label"] = label
            ret = self._order_with_error_handling(uri, params)
        return ret

    def order(
        self,
        asset: str,
        amount: float | int,
        limit: Optional[float | int] = None,
        label: Optional[str] = None,
        reduce_only: bool = False,
    ) -> dict:
        """Place an order after a minimum-size check; placement errors are returned as {'error': ...}."""
        self.check_min_trade_amount([(asset, amount)])
        try:
            ret = self._order(
                asset, amount, limit=limit, label=label, reduce_only=reduce_only
            )
        # pylint: disable=broad-except
        except Exception as e:
            ret = {"error": str(e)}
        return ret

    def market_order(
        self,
        asset: str,
        amount: float | int,
        label: Optional[str] = None,
        reduce_only: bool = False,
    ) -> dict:
        """Place a market order for the given amount."""
        ret = self.order(asset, amount, label=label, reduce_only=reduce_only)
        return ret

    def bulk_order(self, orders: OrdersType, label: Optional[str] = None) -> list[dict]:
        """Place multiple market or limit orders sequentially."""
        self.check_min_trade_amount(orders)
        ret = []
        for order in orders:
            if len(order) == 2:
                asset, amount = order
                limit = None
            else:
                asset, amount, limit = order
            ret.append(self._order(asset, amount, limit=limit, label=label))
        return ret

    def close_position(self, asset: str, limit: Optional[float | int] = None) -> dict:
        """Close a position at market, or at a limit price if given; simulated when simulated=True."""
        if self.simulated:
            ret = {
                "info": SIMULATION_INFO,
                "timestamp": int(time.time() * 1e3),
                "instrument_name": asset,
                "type": "market" if limit is None else "limit",
            }
            # a market close has no price to report, and looking one up would
            # issue a real ticker request in simulation mode
            if limit is not None:
                ret["price"] = limit
            return ret
        uri = self.__CLOSE_POSITION
        params = {
            "instrument_name": asset,
            "type": "market",
        }
        if limit is not None:
            params["type"] = "limit"
            params["price"] = limit
        ret = self._request(uri, params)
        return ret

    def _cancel_by_label(
        self, label: str, currency: Optional[str | list[str]] = None
    ) -> dict:
        if self.simulated:
            simulated = {"info": SIMULATION_INFO, "label": label}
            if currency is None:
                return simulated
            currencies = [currency] if not isinstance(currency, list) else currency
            return {c: {**simulated, "currency": c} for c in currencies}
        uri = self.__CANCEL_BY_LABEL
        params = {
            "label": label,
        }
        if currency is None:
            return self._request(uri, params)
        if not isinstance(currency, list):
            currency = [currency]
        r = {}
        for c in currency:
            params["currency"] = c
            r[c] = self._request(uri, params)
        return r

    def cancel_orders(
        self,
        currency: Optional[str | list[str]] = None,
        kind: Optional[str] = None,
        order_type: Optional[str] = None,
        label: Optional[str] = None,
    ) -> dict:
        """Cancel orders by label, or by currency, kind, and type."""
        if label is not None:
            return self._cancel_by_label(label, currency)
        if self.simulated:
            simulated = {"info": SIMULATION_INFO, "kind": kind, "type": order_type}
            # resolving currency=None reads the public currency list, exactly as
            # live mode does, so the simulated result keeps the same keys; no
            # private endpoint is touched
            currencies = self.currencies if currency is None else currency
            if not isinstance(currencies, list):
                currencies = [currencies]
            return {c: {**simulated, "currency": c} for c in currencies}
        uri = self.__CANCEL_ALL_BY_KIND_OR_TYPE
        params = {
            "currency": "",
        }
        if kind is not None:
            params["kind"] = kind
        if order_type is not None:
            params["type"] = order_type
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        r = {}
        for c in currency:
            params["currency"] = c
            r[c] = self._request(uri, params)
        return r
