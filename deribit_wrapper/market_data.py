from __future__ import absolute_import, annotations

import logging
from datetime import datetime

import pandas as pd
from progressbar import progressbar

from .authentication import Authentication
from .utilities import DEFAULT_END, DEFAULT_START, DatetimeType, OrdersType, StrikeType, from_dt_to_ts, from_ts_to_dt


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


class MarketData(Authentication):
    __GET_CONTRACT_SIZE_URI = '/public/get_contract_size'
    __GET_CURRENCY_URI = '/public/get_currencies'
    __GET_TICKER_URI = '/public/ticker'
    __GET_BOOK_BY_CURRENCY_URI = '/public/get_book_summary_by_currency'
    __GET_BOOK_BY_INSTRUMENT_URI = '/public/get_book_summary_by_instrument'
    __GET_INSTRUMENTS_URI = '/public/get_instruments'
    __GET_INSTRUMENT_URI = '/public/get_instrument'
    __GET_MARKET_DATA_HISTORY = '/public/get_tradingview_chart_data'

    def __init__(self, env: str = 'prod', client_id: str = None, client_secret: str = None,
                 progress_bar_desc: str = None):
        super().__init__(env=env, client_id=client_id, client_secret=client_secret)
        self.progress_bar_desc = progress_bar_desc

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
        ret = self._request(self.__GET_CURRENCY_URI, {})
        return ret

    @property
    def currencies(self) -> list[str]:
        df = pd.DataFrame(self.get_currencies())
        currency_list = list(df['currency'])
        sorted_currency_list = sorted(currency_list)
        return sorted_currency_list

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

    def get_base_currency(self, instrument: str) -> str:
        r = self.get_instrument(instrument)
        ret = r['base_currency']
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

    def get_ticker(self, asset: str) -> dict:
        uri = self.__GET_TICKER_URI
        params = {'instrument_name': asset}
        ret = self._request(uri, params)
        return ret

    def last_price(self, asset: str) -> float:
        ticker = self.get_ticker(asset)
        ret = ticker.get('last_price')
        if ret is None:
            ret = ticker.get('mark_price')
            logging.warning(f'Using mark price instead of last price for asset {asset}.')
        if ret is None:
            raise Exception(f'No price available for asset {asset}.')
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
