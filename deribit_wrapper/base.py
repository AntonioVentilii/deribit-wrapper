"""Base class holding the Deribit environment and API URL configuration."""

from __future__ import absolute_import, annotations

import logging
import time


class DeribitBase:
    """Hold the Deribit environment (test or prod) and derive the API URL."""

    __ENVS = {"test": "https://test.deribit.com", "prod": "https://www.deribit.com"}
    __API_URL = "/api/v2"
    _instance_count = 0  # Class variable to keep track of the instance number

    def __init__(self, env: str = "prod", instance_name: str = None):
        """Create a client for the given environment, optionally naming the instance."""
        super().__init__()
        if env not in self.__ENVS:
            raise ValueError(
                f"Environment '{env}' not supported. Supported environments: {self.__ENVS.keys()}"
            )
        self._env = env
        if instance_name is None:
            DeribitBase._instance_count += 1
            self.instance_name = f"Instance_{DeribitBase._instance_count}"
        else:
            self.instance_name = instance_name

    @property
    def env(self):
        """Return the current environment key ('test' or 'prod')."""
        return self._env

    @env.setter
    def env(self, value):
        logging.warning(
            "Changing environment from %s to %s. You have 10 seconds to abort...",
            self.env,
            value,
        )
        for _ in range(10):
            time.sleep(1)
        self._env = value
        logging.warning("Environment changed to %s.", self.env)

    @property
    def api_url(self):
        """Return the full JSON-RPC API URL for the current environment."""
        env_url = self.__ENVS[self.env]
        url = env_url + self.__API_URL
        return url
