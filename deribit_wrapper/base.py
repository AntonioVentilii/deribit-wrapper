from __future__ import absolute_import, annotations

import logging
import time


class DeribitBase(object):
    __ENVS = {
        'test': 'https://test.deribit.com',
        'prod': 'https://www.deribit.com'
    }
    __API_URL = '/api/v2'

    def __init__(self, env: str = 'prod'):
        super().__init__()
        if env not in self.__ENVS:
            raise ValueError(f'Environment \'{env}\' not supported. Supported environments: {self.__ENVS.keys()}')
        self._env = env

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
