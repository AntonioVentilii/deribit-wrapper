from __future__ import absolute_import, annotations

from datetime import datetime
from typing import List, Tuple, Union

import numpy as np
import pandas as pd

MarketOrderType = Tuple[str, float]
LimitOrderType = Tuple[str, float, float]
OrdersType = List[Union[MarketOrderType, LimitOrderType]]
DatetimeType = Union[datetime, str, float]
StrikeType = Union[str, float]

DEFAULT_START = '2000-01-01'
DEFAULT_END = 'now'


def from_ts_to_dt(timestamp: int | float, milliseconds: bool = True) -> datetime:
    ts = timestamp * 1e9
    if milliseconds:
        ts /= int(1e3)
    ts = np.minimum(ts, pd.Timestamp.max.timestamp() * 1e9 - 1e3)
    dt = pd.to_datetime(ts)
    return dt


def from_dt_to_ts(date: str | datetime, milliseconds: bool = True) -> int:
    dt = pd.to_datetime(date)
    ts = int(datetime.timestamp(dt))
    if milliseconds:
        ts *= int(1e3)
    return ts
