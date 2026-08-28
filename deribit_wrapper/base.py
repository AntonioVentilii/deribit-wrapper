"""Base class holding the Deribit environment and API URL configuration."""

from __future__ import absolute_import, annotations

import logging
from typing import Optional


class DeribitBase:
    """Hold the Deribit environment (test or prod) and derive the API URL."""

    __ENVS = {"test": "https://test.deribit.com", "prod": "https://www.deribit.com"}
    __API_URL = "/api/v2"
    _instance_count = 0  # Class variable to keep track of the instance number

    def __init__(self, env: str = "prod", instance_name: Optional[str] = None):
        """Create a client for the given environment, optionally naming the instance."""
        super().__init__()
        if env not in self.__ENVS:
            raise ValueError(
                f"Environment '{env}' not supported. "
                f"Supported environments: {', '.join(self.__ENVS)}."
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
        if value not in self.__ENVS:
            raise ValueError(
                f"Environment '{value}' not supported. "
                f"Supported environments: {', '.join(self.__ENVS)}."
            )
        if value == self._env:
            return
        self._env = value
        logging.warning("Environment changed to %s.", self.env)

    @property
    def api_url(self):
        """Return the full JSON-RPC API URL for the current environment."""
        env_url = self.__ENVS[self.env]
        url = env_url + self.__API_URL
        return url
