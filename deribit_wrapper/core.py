from __future__ import absolute_import, annotations

import json
import logging

from .trading import Trading

logging.getLogger("urllib3").setLevel(logging.ERROR)


class DeribitClient(Trading):
    def __init__(self, env: str = 'prod', client_id: str = None, client_secret: str = None,
                 progress_bar_desc: str = None, simulated: bool = True):
        super().__init__(client_id=client_id, client_secret=client_secret, env=env,
                         progress_bar_desc=progress_bar_desc, simulated=simulated)


if __name__ == '__main__':
    client = DeribitClient()
    ret_client = client.get_currencies()
    print(json.dumps(ret_client, indent=2))
