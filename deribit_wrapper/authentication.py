from __future__ import absolute_import, annotations

import json
import time
import uuid
import warnings
from typing import overload

from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import DeribitBase
from .exceptions import DeribitClientWarning
from .utilities import ParamsType, ScopeType, seconds_to_hms


class Authentication(DeribitBase):
    __AUTH = '/public/auth'

    __GET_TIME = '/public/get_time'
    __STATUS = '/public/status'
    __TEST = '/public/test'

    def __init__(self, env: str = 'prod', client_id: str = None, client_secret: str = None):
        super().__init__(env=env)
        self._client_id = None
        self._client_secret = None
        self.set_credentials(client_id, client_secret)
        self._access_token = None
        self._token_expiry = None
        self._refresh_token = None

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return self._client_secret

    def set_credentials(self, client_id: str, client_secret: str):
        if not client_id or not client_secret:
            txt = 'Client ID or Client Secret not provided. Only \'public\' requests will be available.'
            warnings.warn(txt, DeribitClientWarning)
        self._client_id = client_id
        self._client_secret = client_secret

    @property
    def _session(self) -> Session:
        session = Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @overload
    def _request(self, uri: str, params: ParamsType, give_results: bool = True) -> dict | list[dict]:
        ...

    @overload
    def _request(self, uri: str, params: ParamsType, give_results: False) -> Response:
        ...

    def _request(self, uri: str, params: ParamsType, give_results: bool = True) -> dict | list[dict] | Response:
        data = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': uri,
            'params': params
        }
        headers = None
        if uri.startswith('/private'):
            token = self.access_token
            headers = {'Authorization': 'bearer ' + token}
        r = self._session.post(url=self.api_url, data=json.dumps(data), headers=headers)

        if give_results:
            ret = r.json()
            if 'result' in ret:
                ret = ret['result']
            elif 'error' in ret:
                ret = ret['error']
                error_code = ret.get('code')
                error_data = ret.get('data', {})

                # Error 10028: too many requests
                if error_code == 10028:
                    wait = error_data.get('wait', 1)
                    print(f'Too many requests for URI {uri}. Waiting {seconds_to_hms(wait)}...')
                    for i in range(wait):
                        time.sleep(1)
                        print(f"Wait {seconds_to_hms(wait - i)}...", end='\r', flush=True)
                    print()
                    ret = self._request(uri, params, give_results=give_results)

                # Error 13009: unauthorized
                elif error_code == 13009:
                    reason = error_data.get('reason')
                    if reason == 'invalid_token':
                        max_attempts = 3
                        for i in range(max_attempts):
                            print(f'Invalid token. Trying to get a new one. Attempt {i + 1} of {max_attempts}...')
                            ret = self._request(uri, params, give_results=give_results)

                # Error 13028: temporarily unavailable
                elif error_code == 13028:
                    max_attempts = 60
                    for i in range(max_attempts):
                        print(f'Temporarily unavailable. Waiting 1 minute [{i + 1}/{max_attempts}]...')
                        time.sleep(60)
                        ret = self._request(uri, params, give_results=give_results)
                        if ret.get('code') != 13028:
                            break
                    if ret.get('code') == 13028:
                        raise Exception('Service temporarily unavailable.')

                # Error -32602: invalid params
                elif error_code == -32602:
                    param = error_data.get('param')
                    reason = error_data.get('reason')
                    print(f'Invalid params for request {uri} with param {param}: {reason}')

                else:
                    print(f'Error code {error_code} for request {uri} with params {params}.')
                    print(ret)
            else:
                raise Exception(ret)

            if not isinstance(ret, dict) and not isinstance(ret, list):
                ret = {'result': ret}

        else:
            ret = r

        return ret

    @property
    def access_token(self) -> str:
        self.refresh_token_if_expired()
        return self._access_token

    def is_token_expired(self) -> bool:
        if self._token_expiry is None or self._access_token is None:
            return True
        current_time = int(time.time())
        buffer = 60
        return current_time >= self._token_expiry - buffer

    def refresh_token_if_expired(self):
        if self.is_token_expired():
            self.get_new_token()

    def create_new_scope(self, session_name: str = None, account: ScopeType = None,
                         trade: ScopeType = None, wallet: ScopeType = None, block_trade: ScopeType = None,
                         expires_in: int = 0, ip: str = '') -> str:
        scope_parts = []

        if session_name is None:
            unique_part = uuid.uuid4()
            timestamp = int(time.time())
            session_name = f'{self.instance_name}_{timestamp}_{unique_part.hex}'
        scope_parts.append(f'session:{session_name}')

        if account:
            scope_parts.append(f'account:{account}')

        if trade:
            scope_parts.append(f'trade:{trade}')

        if wallet:
            scope_parts.append(f'wallet:{wallet}')

        if block_trade:
            scope_parts.append(f'block_trade:{block_trade}')

        if expires_in > 0:
            scope_parts.append(f'expires:{expires_in}')

        if ip:
            scope_parts.append(f'ip:{ip}')

        final_scope = ' '.join(scope_parts)
        return final_scope

    def get_new_token(self, use_refresh_token_if_available: bool = True, expires_in: int = 0) -> str:
        assert self.client_id and self.client_secret, 'Cannot generate new token without Client ID and Client Secret'
        uri = self.__AUTH
        scope = self.create_new_scope(expires_in=expires_in)
        if use_refresh_token_if_available and self._refresh_token:
            params = {
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token,
                'scope': scope,
            }
        else:
            params = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': scope,
            }
        r = self._request(uri, params)
        self._access_token = r['access_token']
        self._token_expiry = int(time.time()) + r['expires_in']
        self._refresh_token = r['refresh_token']
        return self._access_token

    def get_time(self) -> int:
        uri = self.__GET_TIME
        r = self._request(uri, {})
        return r

    def get_status(self) -> dict:
        uri = self.__STATUS
        r = self._request(uri, {})
        return r

    def get_locked_currencies(self) -> list[str]:
        return self.get_status().get('locked_currencies', [])

    def get_locked_indices(self) -> list[str]:
        return self.get_status().get('locked_indices', [])

    def test(self) -> dict:
        uri = self.__TEST
        r = self._request(uri, {})
        return r

    def get_api_version(self) -> str:
        return self.test()['version']
