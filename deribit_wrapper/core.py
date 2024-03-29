from __future__ import absolute_import, annotations

import json
import logging
import time
from datetime import datetime
from typing import List, Tuple, Union

import pandas as pd
import requests
from progressbar import progressbar
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .utilities import from_dt_to_ts, from_ts_to_dt

OrdersType = List[Union[Tuple[str, float], Tuple[str, float, float]]]
DatetimeType = Union[datetime, str, float]
StrikeType = Union[str, float]

DEFAULT_START = '2000-01-01'
DEFAULT_END = 'now'

logging.getLogger("urllib3").setLevel(logging.ERROR)


def name_instrument(currency: str, expiry: DatetimeType, strike: StrikeType = None, opt_type: str = None) -> str:
    c = currency
    t = pd.to_datetime(expiry).strftime('%e%b%y').strip()
    if strike is None or opt_type is None:
        name = '{c}-{t}'
        name = name.format(c=c, t=t)
    else:
        k = int(strike)
        ot = 'c' if opt_type == 'call' else 'p'
        name = '{c}-{t}-{k:d}-{ot}'
        name = name.format(c=c, t=t, k=k, ot=ot)
    name = name.upper()
    return name


def name_option(currency: str, expiry: DatetimeType, strike: StrikeType, opt_type: str) -> str:
    name = name_instrument(currency, expiry, strike, opt_type)
    return name


def name_future(currency: str, expiry: DatetimeType) -> str:
    name = name_instrument(currency, expiry)
    return name


class DeribitClient(object):
    __ENVS = {
        'test': 'https://test.deribit.com',
        'prod': 'https://www.deribit.com'
    }
    __API_URL = '/api/v2'
    __GET_CONTRACT_SIZE_URI = '/public/get_contract_size'
    __GET_CURRENCY_URI = '/public/get_currencies'
    __GET_TICKER_URI = '/public/ticker'
    __GET_BOOK_BY_CURRENCY_URI = '/public/get_book_summary_by_currency'
    __GET_BOOK_BY_INSTRUMENT_URI = '/public/get_book_summary_by_instrument'
    __GET_INSTRUMENTS_URI = '/public/get_instruments'
    __GET_INSTRUMENT_URI = '/public/get_instrument'
    __GET_MARKET_DATA_HISTORY = '/public/get_tradingview_chart_data'
    __AUTH = '/public/auth'
    __GET_ACCOUNT_SUMMARY = '/private/get_account_summary'
    __GET_POSITIONS = '/private/get_positions'
    __GET_TRANSACTION_LOG = '/private/get_transaction_log'
    __GET_TRADE_BY_ORDER = '/private/get_user_trades_by_order'
    __GET_ORDER_STATE = '/private/get_order_state'
    __BUY = '/private/buy'
    __SELL = '/private/sell'
    __GET_MARGINS = '/private/get_margins'

    HEADERS = {'Content-Type': 'application/json'}

    def __init__(self, client_id: str = None, client_secret: str = None, simulated: bool = True, env: str = 'prod',
                 progress_bar_desc: str = None):
        super().__init__()
        self._env = env
        self.client_id = client_id
        self.client_secret = client_secret
        self.simulated = simulated
        self.progress_bar_desc = progress_bar_desc

    @property
    def _session(self):
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @property
    def env(self):
        return self._env

    @env.setter
    def env(self, value):
        logging.warning(f'Changing environment from {self.env} to {value}. You have 10 seconds to abort...')
        for _ in range(10):
            time.sleep(1)
        self._env = value
        logging.warning(f'Environment changed to {self.env}.')

    @property
    def api_url(self):
        env_url = self.__ENVS[self.env]
        url = env_url + self.__API_URL
        return url

    def _request(self, uri: str, params: dict[str:str | int | float], give_results: bool = True):
        data = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': uri,
            'params': params
        }
        headers = None
        if uri.startswith('/private'):
            token = self._get_new_token()
            headers = {'Authorization': 'bearer ' + token}
        r = self._session.post(url=self.api_url, data=json.dumps(data), headers=headers)
        if give_results:
            ret = r.json()
            if 'result' in ret:
                ret = ret['result']
            elif 'error' in ret:
                ret = ret['error']
                error_code = ret.get('code')
                if error_code == 10028:
                    print('Too many requests. Waiting 1 second...')
                    time.sleep(1)
                    ret = self._request(uri, params, give_results=give_results)
                elif error_code == 13009:
                    max_attempts = 3
                    for i in range(max_attempts):
                        print(f'Invalid token. Trying to get a new one. Attempt {i + 1} of {max_attempts}...')
                        ret = self._request(uri, params, give_results=give_results)
                else:
                    print(f'Error code {error_code} for request {uri} with params {params}.')
                    print(ret)
            else:
                raise Exception(ret)
        else:
            ret = r
        return ret

    def _get_new_token(self) -> str:
        assert self.client_id and self.client_secret, 'Cannot generate new token without Client ID and Client Secret'
        uri = self.__AUTH
        params = {
            'grant_type': 'client_credentials',
            'scope': 'session:first_test',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        r = self._request(uri, params)
        token = r['access_token']
        return token

    def get_contract_size(self, asset: str):
        uri = self.__GET_CONTRACT_SIZE_URI
        params = {'instrument_name': asset}
        r = self._request(uri, params)
        try:
            ret = r['contract_size']
        except KeyError:
            logging.warning('No result found for asset {}.'.format(asset))
            return {}
        return ret

    def get_currencies(self) -> list[dict]:
        r = self._session.get(self.api_url + self.__GET_CURRENCY_URI)
        ret = r.json()['result']
        return ret

    @property
    def currencies(self) -> list[str]:
        df = pd.DataFrame(self.get_currencies())
        currency = list(df['currency'])
        return currency

    def get_complete_market_book(self) -> pd.DataFrame:
        uri = self.__GET_BOOK_BY_CURRENCY_URI
        params = {'currency': ''}
        currencies = self.currencies
        ret = pd.DataFrame()
        for currency in currencies:
            params['currency'] = currency
            r = self._request(uri, params)
            df_temp = pd.DataFrame(r)
            df_temp.dropna(axis=1, how='all', inplace=True)
            ret = pd.concat([ret, df_temp], ignore_index=True)
        return ret

    def get_market_book(self, currency: str = None, instrument: list[str] = None) -> pd.DataFrame:
        ret = None
        if currency is not None:
            pass
        elif instrument is not None:
            uri = self.__GET_BOOK_BY_INSTRUMENT_URI
            params = {'instrument_name': ''}
            ret = pd.DataFrame()
            for i in instrument:
                params['instrument_name'] = i
                r = self._request(uri, params)
                df_temp = pd.DataFrame(r)
                df_temp.dropna(axis=1, how='all', inplace=True)
                ret = pd.concat([ret, df_temp], ignore_index=True)
        else:
            pass
        return ret

    def get_instruments(self, currencies: str | list[str] = None, kind: str = None,
                        as_list: bool = False) -> pd.DataFrame | list[str]:
        uri = self.__GET_INSTRUMENTS_URI
        params = {
            'currency': '',
            'expired': False
        }
        if kind is not None:
            params['kind'] = kind
        if currencies is None:
            currencies = self.currencies
        else:
            currencies = [currencies] if isinstance(currencies, str) else currencies
        ret = pd.DataFrame()
        for currency in currencies:
            params['currency'] = currency
            params['expired'] = False
            r = self._request(uri, params)
            ret = pd.concat([ret, pd.DataFrame(r)], ignore_index=True)
            params['expired'] = True
            r = self._request(uri, params)
            ret = pd.concat([ret, pd.DataFrame(r)], ignore_index=True)
        if not ret.empty:
            ret.drop_duplicates(subset=['instrument_name'], inplace=True)
            ret.sort_values(by=['kind', 'base_currency', 'expiration_timestamp'], inplace=True)
        if as_list:
            ret = ret['instrument_name'].to_list() if not ret.empty else []
        return ret

    def get_instrument(self, instrument: str) -> dict:
        uri = self.__GET_INSTRUMENT_URI
        params = {'instrument_name': instrument}
        r = self._request(uri, params)
        ret = r
        return ret

    def get_min_trade_amount(self, instrument: str) -> float:
        r = self.get_instrument(instrument)
        ret = r['min_trade_amount']
        return ret

    def get_kind(self, instrument: str) -> str:
        r = self.get_instrument(instrument)
        ret = r['kind']
        return ret

    def get_expiry_timestamp(self, instrument: str) -> int:
        r = self.get_instrument(instrument)
        ret = r['expiration_timestamp']
        return ret

    def get_expiry_date(self, instrument: str) -> datetime:
        ts = self.get_expiry_timestamp(instrument)
        ret = from_ts_to_dt(ts)
        return ret

    def get_future_instruments(self, currencies: str | list[str] = None,
                               as_list: bool = False) -> pd.DataFrame | list[str]:
        df = self.get_instruments(currencies=currencies, kind='future', as_list=as_list)
        return df

    def get_option_instruments(self, currencies: str | list[str] = None,
                               as_list: bool = False) -> pd.DataFrame | list[str]:
        df = self.get_instruments(currencies=currencies, kind='option', as_list=as_list)
        return df

    def get_nth_future(self, currency: str, n: int, ref_date: datetime = None) -> str:
        ref_date = ref_date or pd.Timestamp.now()
        margin = ref_date + pd.DateOffset(days=1, hours=1)
        futures = self.get_future_instruments(currencies=currency)
        ret = None
        if not futures.empty:
            df = futures[futures['quote_currency'] != 'USDC']
            df = df[df['is_active']]
            df.dropna(subset=['expiration_timestamp'])
            df = df[df['expiration_timestamp'] >= from_dt_to_ts(margin)]
            if not df.empty:
                ret = df.nsmallest(n, columns='expiration_timestamp')['instrument_name'].iloc[-1]
        return ret

    def get_first_future(self, currency: str, ref_date: datetime = None) -> str:
        return self.get_nth_future(currency, n=1, ref_date=ref_date)

    def get_closest_strike_by_future(self, future: str) -> float:
        last_price = self.last_price(future)
        instrument = self.get_instrument(future)
        currency = instrument['base_currency']
        expiry_ts = instrument['expiration_timestamp']
        df = self.get_option_instruments(currencies=currency)
        df = df[df['expiration_timestamp'] == expiry_ts]
        df['diff'] = abs(df['strike'] - last_price)
        df = df.nsmallest(1, columns='diff')
        ret = df['strike'].iloc[0]
        return ret

    def get_closest_strike(self, currency: str, expiry: DatetimeType) -> float:
        future = name_future(currency, expiry)
        ret = self.get_closest_strike_by_future(future)
        return ret

    def min_trade_amount(self, instruments: str | list[str] = None) -> pd.DataFrame:
        df = self.get_instruments()
        df.set_index('instrument_name', inplace=True)
        if instruments is not None:
            df = df.loc[instruments, :]
        return df['min_trade_amount']

    def check_min_trade_amount(self, orders: OrdersType) -> pd.DataFrame:
        instruments = [t[0] for t in orders]
        size = [abs(t[1]) for t in orders]
        ret = size >= self.min_trade_amount(instruments)
        return ret.all()

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

    def last_price(self, asset: str) -> float:
        ticker = self.get_ticker(asset)
        ret = ticker['last_price']
        if ret is None:
            ret = ticker['mark_price']
            logging.warning(f'Using mark price instead of last price for asset {asset}.')
        return ret

    def mid_price(self, asset: str) -> float:
        ticker = self.get_ticker(asset)
        bid = ticker['best_bid_price']
        ask = ticker['best_ask_price']
        if bid is None and ask is None:
            mark = ticker['mark_price']
            bid = mark
            ask = mark
            logging.warning(f'Using mark price instead of mid price for asset {asset}.')
        elif bid is None:
            bid = ask
            logging.warning(f'No bid available for mid calculation for asset {asset}.')
        elif ask is None:
            ask = bid
            logging.warning(f'No ask available for mid calculation for asset {asset}.')
        ret = (bid + ask) / 2
        return ret

    def get_ticker(self, asset: str) -> dict:
        uri = self.__GET_TICKER_URI
        params = {'instrument_name': asset}
        ret = self._request(uri, params)
        return ret

    def get_market_data_history(self, asset: str, start_date: str | datetime = None, end_date: str | datetime = None,
                                resolution: str = '1D') -> pd.DataFrame:
        start_date = start_date or DEFAULT_START
        end_date = end_date or DEFAULT_END
        uri = self.__GET_MARKET_DATA_HISTORY
        start_dt = from_dt_to_ts(pd.to_datetime(start_date))
        end_dt = from_dt_to_ts(pd.to_datetime(end_date))
        params = {'instrument_name': asset,
                  'start_timestamp': start_dt,
                  'end_timestamp': end_dt,
                  'resolution': resolution}
        ret = self._request(uri, params)
        status = ret.pop('status', None)
        df = pd.DataFrame(ret)
        if status == 'ok':
            df['datetime'] = df['ticks'].apply(from_ts_to_dt)
            df['date'] = df['datetime'].dt.date
            df.set_index('date', inplace=True)
        else:
            print(status, 'no data found for asset', asset)
        return df

    def get_market_data(self, assets: list[str] = None, start_date: str | datetime = None,
                        end_date: str | datetime = None) -> pd.DataFrame:
        start_date = start_date or DEFAULT_START
        end_date = end_date or DEFAULT_END
        if assets is None:
            assets = self.get_instruments(as_list=True)
        df = pd.DataFrame()
        prefix = f'{self.progress_bar_desc}: Market data' if self.progress_bar_desc else 'Market data'
        for asset in progressbar(assets, prefix=prefix, redirect_stdout=True):
            ret = self.get_market_data_history(asset, start_date, end_date)
            ret['instrument_name'] = asset
            ret.set_index('instrument_name', append=True, inplace=True)
            df = pd.concat([df, ret])
        df.sort_index(inplace=True)
        return df

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


if __name__ == '__main__':
    client = DeribitClient()
    ret_client = client.get_currencies()
    print(json.dumps(ret_client, indent=2))
