"""Shared type aliases, constants, and conversion helpers."""

from __future__ import absolute_import, annotations

from datetime import datetime
from typing import Any, List, Literal, MutableMapping, Tuple, Union, get_args

import numpy as np
import pandas as pd

# a request payload: values are whatever the JSON-RPC endpoint accepts
ParamsType = MutableMapping[str, Any]

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
    """Convert an epoch timestamp (ms by default) to a naive UTC datetime."""
    ts = timestamp * 1e9
    if milliseconds:
        ts /= int(1e3)
    ts = np.minimum(ts, pd.Timestamp.max.timestamp() * 1e9 - 1e3)
    dt = pd.to_datetime(ts)
    return dt


def from_dt_to_ts(date: str | datetime, milliseconds: bool = True) -> int:
    """Convert a datetime or date string to an epoch timestamp (ms by default); naive inputs are treated as UTC."""
    # naive datetimes are interpreted as UTC, matching from_ts_to_dt and the
    # UTC epoch timestamps used by the Deribit API; the integer nanosecond
    # value avoids float rounding and keeps millisecond precision
    ns = int(pd.to_datetime(date, utc=True).value)
    if milliseconds:
        return ns // 10**6
    return ns // 10**9


def seconds_to_hms(seconds: int) -> str:
    """Format a duration in seconds as 'Xh MMm SSs'."""
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m:02d}m {s:02d}s"


def flatten_dict(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    """Flatten a nested dict, joining keys with the given separator."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def create_multilevel_df(data: dict | list[dict]) -> pd.DataFrame:
    """Build a MultiIndex-column DataFrame from nested dicts."""
    sep = "___"
    if isinstance(data, dict):
        data = [data]
    flattened_data = [flatten_dict(item, sep=sep) for item in data]
    df = pd.DataFrame(flattened_data)
    if df.columns.empty:
        return df
    multiindex_columns = [tuple(col.split(sep)) for col in df.columns]
    df.columns = pd.MultiIndex.from_tuples(multiindex_columns)
    return df
