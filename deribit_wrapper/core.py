"""Public entry point exposing the fully assembled Deribit client."""

from __future__ import absolute_import, annotations

import json
import logging
from typing import Any

from .trading import Trading

logging.getLogger("urllib3").setLevel(logging.ERROR)


class DeribitClient(Trading):
    """Deribit API client combining market data, account management, and trading."""

    def __init__(
        self,
        env: str = "prod",
        client_id: str = None,
        client_secret: str = None,
        private_key: str | bytes | Any | None = None,
        auth_method: str = "credentials",
        progress_bar_desc: str = None,
        simulated: bool = True,
    ):
        """Create a client; simulated=True keeps orders local instead of sending them."""
        super().__init__(
            client_id=client_id,
            client_secret=client_secret,
            env=env,
            private_key=private_key,
            auth_method=auth_method,
            progress_bar_desc=progress_bar_desc,
            simulated=simulated,
        )


if __name__ == "__main__":
    client = DeribitClient()
    ret_client = client.get_currencies()
    print(json.dumps(ret_client, indent=2))
