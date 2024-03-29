from __future__ import absolute_import, annotations

import json
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .base import DeribitBase


class Authentication(DeribitBase):
    __AUTH = '/public/auth'

    def __init__(self, env: str = 'prod', client_id: str = None, client_secret: str = None):
        super().__init__(env=env)
        if not client_id or not client_secret:
            print('Client ID or Client Secret not provided. Token will not be generated. Private requests will fail.')
        self.client_id = client_id
        self.client_secret = client_secret

    @property
    def _session(self):
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

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
