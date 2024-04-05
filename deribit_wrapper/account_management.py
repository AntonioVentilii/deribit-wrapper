from __future__ import absolute_import, annotations

import time
from datetime import datetime

import pandas as pd

from dev_scripts.utilities_dev import create_multilevel_df
from .market_data import MarketData
from .utilities import DEFAULT_END, DEFAULT_START, MarginModelType, MarketOrderType, from_dt_to_ts, seconds_to_hms


class AccountManagement(MarketData):
    __GET_ACCOUNT_SUMMARY = '/private/get_account_summary'
    __LIST_API_KEYS = '/private/list_api_keys'
    __CREATE_API_KEY = '/private/create_api_key'
    __EDIT_API_KEY = '/private/edit_api_key'
    __ENABLE_API_KEY = '/private/enable_api_key'
    __DISABLE_API_KEY = '/private/disable_api_key'
    __REMOVE_API_KEY = '/private/remove_api_key'
    __CHANGE_API_KEY_NAME = '/private/change_api_key_name'
    __CHANGE_API_KEY_SCOPE = '/private/change_scope_in_api_key'
    __GET_SUBACCOUNTS = '/private/get_subaccounts'
    __CREATE_SUBACCOUNT = '/private/create_subaccount'
    __CHANGE_SUBACCOUNT_NAME = '/private/change_subaccount_name'
    __REMOVE_SUBACCOUNT = '/private/remove_subaccount'
    __CHANGE_MARGIN_MODEL = '/private/change_margin_model'
    __TOGGLE_PORTFOLIO_MARGIN = '/private/toggle_portfolio_margin'
    __GET_POSITIONS = '/private/get_positions'
    __GET_TRANSACTION_LOG = '/private/get_transaction_log'
    __GET_PORTFOLIO_MARGINS = '/private/get_portfolio_margins'

    def __init__(self, client_id: str = None, client_secret: str = None, env: str = 'prod',
                 progress_bar_desc: str = None):
        super().__init__(client_id=client_id, client_secret=client_secret, env=env,
                         progress_bar_desc=progress_bar_desc)

    def get_account_summary(self, currency: str | list[str] = None, subaccount_id: int = None) -> pd.DataFrame:
        uri = self.__GET_ACCOUNT_SUMMARY
        params = {'currency': '', 'extended': True}
        if subaccount_id is not None:
            params['subaccount_id'] = subaccount_id
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        df = pd.DataFrame()
        for c in currency:
            params['currency'] = c
            r = self._request(uri, params)
            r = {k: [v] for k, v in r.items()}
            df = pd.concat([df, pd.DataFrame(r)], ignore_index=True)
        if 'currency' in df.columns:
            cols = df.columns.tolist()
            cols = ['currency'] + [col for col in cols if col != 'currency']
            df = df[cols].copy()
        return df

    def get_margin_model(self, currency: str | list[str] = None, subaccount_id: int = None) -> pd.DataFrame:
        df = self.get_account_summary(currency=currency, subaccount_id=subaccount_id)
        df = df[['currency', 'margin_model', 'portfolio_margining_enabled', 'cross_collateral_enabled']]
        return df

    def list_api_keys(self) -> pd.DataFrame:
        uri = self.__LIST_API_KEYS
        r = self._request(uri, {})
        df = pd.DataFrame(r)
        return df

    def get_api_key(self, api_key_id: str) -> dict:
        keys = self.list_api_keys()
        key = keys[keys['id'] == api_key_id].to_dict(orient='records')
        return key[0]

    def create_api_key(self, max_scope: str, name: str = None) -> dict:
        uri = self.__CREATE_API_KEY
        params = {'max_scope': max_scope}
        if name is not None:
            params['name'] = name
        r = self._request(uri, params)
        return r

    def edit_api_key(self, api_key_id: str, max_scope: str, name: str = None) -> dict:
        uri = self.__EDIT_API_KEY
        params = {'id': api_key_id, 'max_scope': max_scope}
        if name is not None:
            params['name'] = name
        r = self._request(uri, params)
        return r

    def enable_api_key(self, api_key_id: str) -> dict:
        uri = self.__ENABLE_API_KEY
        params = {'id': api_key_id}
        r = self._request(uri, params)
        return r

    def disable_api_key(self, api_key_id: str) -> dict:
        uri = self.__DISABLE_API_KEY
        params = {'id': api_key_id}
        r = self._request(uri, params)
        return r

    def remove_api_key(self, api_key_id: str) -> dict:
        uri = self.__REMOVE_API_KEY
        params = {'id': api_key_id}
        r = self._request(uri, params)
        return r

    def _get_subaccounts(self, with_portfolio: bool = False) -> list[dict]:
        uri = self.__GET_SUBACCOUNTS
        params = {'with_portfolio': with_portfolio}
        r = self._request(uri, params)
        return r

    def get_subaccounts(self) -> pd.DataFrame:
        r = self._get_subaccounts()
        df = pd.DataFrame(r)
        return df

    def get_subaccounts_with_portfolio(self) -> list[dict]:
        r = self._get_subaccounts(with_portfolio=True)
        return r

    def get_subaccount(self, subaccount_id: int, with_portfolio: bool = False) -> dict:
        r = self._get_subaccounts(with_portfolio=with_portfolio)
        for subaccount in r:
            if subaccount['id'] == subaccount_id:
                return subaccount
        raise ValueError(f'Subaccount {subaccount_id} not found.')

    def create_subaccount(self) -> dict:
        uri = self.__CREATE_SUBACCOUNT
        r = self._request(uri, {})
        return r

    def change_subaccount_name(self, subaccount_id: int, name: str) -> dict:
        if len(name) > 32:
            raise Exception(f"Subaccount name '{name}' is too long, maximum 32 characters.")
        uri = self.__CHANGE_SUBACCOUNT_NAME
        params = {'sid': subaccount_id, 'name': name}
        r = self._request(uri, params)
        error_code = r.get('code')

        # Error code 12002: already taken
        if error_code == 12002:
            data = r.get('data')
            if data == 'already_taken':
                raise Exception(f"Subaccount name '{name}' is already taken.")
            elif data == 'wrong_format':
                raise Exception(f"Subaccount name '{name}' has wrong format.")
            else:
                raise Exception(f"Error changing subaccount name to '{name}': {data}.")

        return r

    def remove_subaccount(self, subaccount_id: int, wait_if_over_limit: bool = False) -> dict:
        uri = self.__REMOVE_SUBACCOUNT
        params = {'subaccount_id': subaccount_id}
        r = self._request(uri, params)
        error_code = r.get('code')
        error_data = r.get('data', {})

        # Error code 12006: remove subaccount over limit
        if error_code == 12006:
            wait = error_data.get('wait', 1)
            if wait_if_over_limit:
                print(f"Waiting {seconds_to_hms(wait)} before removing subaccount {subaccount_id}.")
                for i in range(wait):
                    time.sleep(1)
                    print(f"Wait {seconds_to_hms(wait - i)}...", end='\r', flush=True)
                print()
                r = self._request(uri, params)
            else:
                raise Exception(f"Wait {wait} seconds before removing subaccount {subaccount_id}.")

        # Error code 12007: subaccount not removable
        elif error_code == 12007:
            reason = error_data.get('reason')
            raise Exception(f"Subaccount {subaccount_id} is not removable: {reason}.")

        # Error code 13009: unauthorized
        elif error_code == 13009:
            reason = error_data.get('reason')
            if reason == 'already_removed':
                raise Exception(f'Subaccount {subaccount_id} already removed.')
            else:
                raise Exception(f'Unauthorized to remove subaccount {subaccount_id}: {reason}.')

        return r

    def _change_margin_model(self, margin_model: MarginModelType, subaccount_id: int = None,
                             dry_run: bool = False) -> pd.DataFrame:
        uri = self.__CHANGE_MARGIN_MODEL
        params = {'margin_model': margin_model, 'dry_run': dry_run}
        if subaccount_id is not None:
            params['subaccount_id'] = subaccount_id
        r = self._request(uri, params)
        if isinstance(r, dict):
            error_code = r.get('code')
            error_data = r.get('data', {})
        else:
            error_code = None
            error_data = {}

        # Error -32602: invalid params
        if error_code == -32602:
            param = error_data.get('param')
            reason = error_data.get('reason')
            if param == 'margin_model':
                raise Exception(f'Invalid margin model {margin_model}: {reason}')
            else:
                raise Exception(f'Invalid params for request {uri} with param {param}: {reason}')

        df = create_multilevel_df(r)
        return df

    def change_margin_model(self, margin_model: MarginModelType, subaccount_id: int = None) -> pd.DataFrame:
        return self._change_margin_model(margin_model, subaccount_id=subaccount_id, dry_run=False)

    def check_if_margin_model_change_is_possible(self, margin_model: MarginModelType,
                                                 subaccount_id: int = None) -> bool:
        df = self._change_margin_model(margin_model, subaccount_id=subaccount_id, dry_run=True)
        df['check_initial_margin'] = df[('new_state', 'initial_margin_rate')] < 1
        df['check_maintenance_margin'] = df[('new_state', 'maintenance_margin_rate')] < 1
        check = df[['check_initial_margin', 'check_maintenance_margin']].all().all()
        return check

    def get_positions(self, currency: str | list[str] = None, kind: str = None,
                      subaccount_id: int = None) -> pd.DataFrame:
        uri = self.__GET_POSITIONS
        params = {'currency': ''}
        if kind is not None:
            params['kind'] = kind
        if currency is None:
            currency = self.currencies
        elif not isinstance(currency, list):
            currency = [currency]
        if subaccount_id is not None:
            params['subaccount_id'] = subaccount_id
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
        results = pd.DataFrame()
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
