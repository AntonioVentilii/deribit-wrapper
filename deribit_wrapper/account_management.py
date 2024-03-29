from __future__ import absolute_import, annotations

from datetime import datetime

import pandas as pd

from .market_data import MarketData
from .utilities import DEFAULT_END, DEFAULT_START, MarketOrderType, from_dt_to_ts


class AccountManagement(MarketData):
    __GET_ACCOUNT_SUMMARY = '/private/get_account_summary'
    __GET_POSITIONS = '/private/get_positions'
    __GET_TRANSACTION_LOG = '/private/get_transaction_log'
    __GET_PORTFOLIO_MARGINS = '/private/get_portfolio_margins'

    def __init__(self, client_id: str = None, client_secret: str = None, env: str = 'prod',
                 progress_bar_desc: str = None):
        super().__init__(client_id=client_id, client_secret=client_secret, env=env,
                         progress_bar_desc=progress_bar_desc)

    def get_account_summary(self, currency: str | list[str] = None) -> pd.DataFrame:
        uri = self.__GET_ACCOUNT_SUMMARY
        params = {'currency': '', 'extended': True}
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        ret = pd.DataFrame()
        for c in currency:
            params['currency'] = c
            r = self._request(uri, params)
            r = {k: [v] for k, v in r.items()}
            ret = pd.concat([ret, pd.DataFrame(r)], ignore_index=True)
        return ret

    def get_positions(self, currency: str | list[str] = None, kind: str = None) -> pd.DataFrame:
        uri = self.__GET_POSITIONS
        params = {'currency': ''}
        if kind is not None:
            params['kind'] = kind
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        ret = pd.DataFrame()
        for c in currency:
            params['currency'] = c
            r = self._request(uri, params)
            ret = ret.append(pd.DataFrame(r), ignore_index=True)
        return ret

    def get_transaction_log(self, start: str | datetime = None, end: str | datetime = None,
                            currency: str | list[str] = None, query: str | list[str] = None) -> pd.DataFrame:
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        uri = self.__GET_TRANSACTION_LOG
        params = {}
        if not isinstance(query, list):
            query = [query]
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        start_ts = from_dt_to_ts(pd.to_datetime(start, utc=True))
        end_ts = from_dt_to_ts(pd.to_datetime(end, utc=True))
        params['start_timestamp'] = start_ts
        params['end_timestamp'] = end_ts
        results = pd.DataFrame(columns=['timestamp'])
        for q in query:
            if q is not None:
                params['query'] = q
            for c in currency:
                params['currency'] = c
                params.pop('continuation', None)
                continuation = True
                while continuation is not None:
                    ret = self._request(uri, params)
                    new_results = pd.DataFrame(ret['logs'])
                    new_results_filtered = new_results.dropna(axis=1, how='all')
                    results = pd.concat([results, new_results_filtered])
                    if 'profit_as_cashflow' in results.columns:
                        results = results.astype({'profit_as_cashflow': bool})
                    continuation = ret['continuation']
                    params['continuation'] = continuation
        results.reset_index(drop=True, inplace=True)
        return results

    def get_delivery_log(self, start: str | datetime = None, end: str | datetime = None,
                         currency: str | list[str] = None) -> pd.DataFrame:
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        return self.get_transaction_log(start, end, currency, query='delivery')

    def get_flow_history(self, start: str | datetime = None, end: str | datetime = None,
                         currency: str | list[str] = None) -> pd.DataFrame:
        start = start or DEFAULT_START
        end = end or DEFAULT_END
        return self.get_transaction_log(start, end, currency, query=['deposit', 'transfer'])

    def get_portfolio_margins(self, orders: list[MarketOrderType], add_positions: bool = True) -> dict:
        uri = self.__GET_PORTFOLIO_MARGINS
        data = {}
        for instrument, amount in orders:
            currency = self.get_base_currency(instrument)
            if currency not in data:
                data[currency] = {}
            data[currency][instrument] = amount
        ret = {}
        for currency, simulated_positions in data.items():
            params = {
                'currency': currency,
                'simulated_positions': simulated_positions,
                'add_positions': add_positions,
            }
            r = self._request(uri, params)
            ret[currency] = r
        return ret
