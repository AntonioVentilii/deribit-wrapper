from __future__ import absolute_import, annotations

from datetime import datetime
from typing import List, Literal, Tuple, Union, get_args

import numpy as np
import pandas as pd

ParamsType = dict[str, Union[str, int, float]]

MarketOrderType = Tuple[str, float]
LimitOrderType = Tuple[str, float, float]
OrdersType = List[Union[MarketOrderType, LimitOrderType]]
DatetimeType = Union[datetime, str, float]
StrikeType = Union[str, float]

ScopeType = Literal["read", "read_write", "none"]
SCOPES = list(get_args(ScopeType))

MarginModelType = Literal["cross_pm", "cross_sm", "segregated_pm", "segregated_sm"]
MARGIN_MODELS = list(get_args(MarginModelType))

DEFAULT_START = "2000-01-01"
DEFAULT_END = "now"


def from_ts_to_dt(timestamp: int | float, milliseconds: bool = True) -> datetime:
    ts = timestamp * 1e9
    if milliseconds:
        ts /= int(1e3)
    ts = np.minimum(ts, pd.Timestamp.max.timestamp() * 1e9 - 1e3)
    dt = pd.to_datetime(ts)
    return dt


def from_dt_to_ts(date: str | datetime, milliseconds: bool = True) -> int:
    # naive datetimes are interpreted as UTC, matching from_ts_to_dt and the
    # UTC epoch timestamps used by the Deribit API; the integer nanosecond
    # value avoids float rounding and keeps millisecond precision
    ns = int(pd.to_datetime(date, utc=True).value)
    if milliseconds:
        return ns // 10**6
    return ns // 10**9


def seconds_to_hms(seconds: int) -> str:
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m:02d}m {s:02d}s"
