from __future__ import absolute_import, annotations

import time
from datetime import datetime

import pandas as pd
from progressbar import progressbar

from .account_management import AccountManagement
from .utilities import DEFAULT_END, DEFAULT_START, OrdersType


class Trading(AccountManagement):
    __GET_TRADE_BY_ORDER = '/private/get_user_trades_by_order'
    __GET_ORDER_STATE = '/private/get_order_state'
    __BUY = '/private/buy'
    __SELL = '/private/sell'
    __GET_MARGINS = '/private/get_margins'

    def __init__(self, client_id: str = None, client_secret: str = None, env: str = 'prod',
                 progress_bar_desc: str = None, simulated: bool = True):
        super().__init__(client_id=client_id, client_secret=client_secret, env=env,
                         progress_bar_desc=progress_bar_desc)
        self.simulated = simulated

    def instrument_margins(self, instrument: str, amount: float | int = 1, price: float = None) -> dict:
        if price is None:
            price = self.last_price(instrument)
        uri = self.__GET_MARGINS
        params = {'instrument_name': instrument, 'amount': amount, 'price': price}
        ret = self._request(uri, params)
        return ret

    def instrument_margin(self, instrument: str, amount: float | int = 1, price: float = None) -> float:
        side = 'buy' if amount > 0 else 'sell'
        return self.instrument_margins(instrument, amount=abs(amount), price=price)[side]

    def instrument_buy_margin(self, instrument: str, amount: float | int = 1, price: float = None) -> float:
        return self.instrument_margins(instrument, amount=amount, price=price)['buy']

    def instrument_sell_margin(self, instrument: str, amount: float | int = 1, price: float = None) -> float:
        return self.instrument_margins(instrument, amount=amount, price=price)['sell']

    def get_trade_by_order(self, order_ids: list[str | int]) -> pd.DataFrame:
        uri = self.__GET_TRADE_BY_ORDER
        results = []
        prefix = f'{self.progress_bar_desc}: Trades by order' if self.progress_bar_desc else 'Trades by order'
        for order_id in progressbar(order_ids, prefix=prefix, redirect_stdout=True):
            params = {'order_id': order_id}
            results += self._request(uri, params)
        ret = pd.DataFrame(results)
        return ret

    def get_orders(self, order_ids: list[str | int]) -> pd.DataFrame:
        uri = self.__GET_ORDER_STATE
        results = []
        prefix = f'{self.progress_bar_desc}: Orders' if self.progress_bar_desc else 'Orders'
        for order_id in progressbar(order_ids, prefix=prefix, redirect_stdout=True):
            params = {'order_id': order_id}
            results.append(self._request(uri, params))
        ret = pd.DataFrame(results)
        return ret

    def get_trade_history(self, start: str | datetime = None, end: str | datetime = None,
                          currency: str | list[str] = None, include_order_data: bool = False) -> pd.DataFrame:
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        results = self.get_transaction_log(start, end, currency, query='trade')
        if not results.empty:
            if include_order_data:
                order_ids = list(set(results['order_id']))
                orders = self.get_orders(order_ids)
                results = results.merge(orders, how='left', on='order_id', suffixes=(None, '_duplicate'))
        results.sort_values('timestamp', inplace=True)
        return results

    def get_entire_trade_history(self, include_order_data: bool = False) -> pd.DataFrame:
        return self.get_trade_history(include_order_data=include_order_data)

    def _order(self, asset: str, amount: float | int, limit: float | int = None, label: str = None,
               reduce_only: bool = False) -> dict:
        label = None if label == '' else label
        if amount > 0:
            uri = self.__BUY
            side = 'buy'
        elif amount < 0:
            uri = self.__SELL
            side = 'sell'
        else:
            return {}
        if self.simulated:
            ret = {
                'info': 'SIMULATION MODE - no trade executed',
                'timestamp': int(time.time() * 1e3),
                'kind': self.get_kind(asset),
                'instrument_name': asset,
                'side': side,
                'amount': abs(amount),
                'price': limit or self.last_price(asset),
                'fee': 0,
                'label': label
            }
        else:
            params = {
                'instrument_name': asset,
                'amount': abs(amount),
                'type': 'market',
                'reduce_only': reduce_only,
            }
            if limit is not None:
                params['type'] = 'limit'
                params['price'] = limit
            if label is not None:
                params['label'] = label
            r = self._request(uri, params)
            ret = r
            while ret.get('code') == 10041:
                time.sleep(1)
                r = self._request(uri, params)
                ret = r
        return ret

    def order(self, asset: str, amount: float | int, limit: float | int = None, label: str = None,
              reduce_only: bool = False) -> dict:
        self.check_min_trade_amount([(asset, amount)])
        try:
            ret = self._order(asset, amount, limit=limit, label=label, reduce_only=reduce_only)
        except Exception as e:
            ret = {'error': str(e)}
        return ret

    def market_order(self, asset: str, amount: float | int, label: str = None, reduce_only: bool = False) -> dict:
        ret = self.order(asset, amount, label=label, reduce_only=reduce_only)
        return ret

    def bulk_order(self, orders: OrdersType, label: str = None) -> list[dict]:
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
