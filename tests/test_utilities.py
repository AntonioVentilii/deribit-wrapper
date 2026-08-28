from datetime import datetime

from deribit_wrapper.utilities import from_dt_to_ts, from_ts_to_dt, seconds_to_hms

# NOTE: from_dt_to_ts converts naive datetimes via the LOCAL timezone
# (datetime.timestamp), while from_ts_to_dt converts timestamps to naive UTC
# datetimes (pd.to_datetime). Absolute-epoch assertions would therefore only
# hold on UTC machines, so these tests check timezone-independent invariants.


def test_from_dt_to_ts_milliseconds_is_seconds_times_1000():
    ms = from_dt_to_ts("2024-01-01")
    s = from_dt_to_ts("2024-01-01", milliseconds=False)
    assert ms == s * 1000


def test_from_dt_to_ts_str_and_datetime_agree():
    assert from_dt_to_ts(datetime(2024, 1, 1)) == from_dt_to_ts("2024-01-01")


def test_from_dt_to_ts_is_monotonic():
    assert from_dt_to_ts("2024-01-02") > from_dt_to_ts("2024-01-01")


def test_from_ts_to_dt_milliseconds():
    dt = from_ts_to_dt(1704067200000)
    assert dt == datetime(2024, 1, 1)


def test_from_ts_to_dt_seconds():
    dt = from_ts_to_dt(1704067200, milliseconds=False)
    assert dt == datetime(2024, 1, 1)


def test_from_ts_to_dt_clips_overflow_instead_of_raising():
    dt = from_ts_to_dt(2**62)
    assert dt is not None


def test_seconds_to_hms():
    assert seconds_to_hms(0) == "0h 00m 00s"
    assert seconds_to_hms(59) == "0h 00m 59s"
    assert seconds_to_hms(60) == "0h 01m 00s"
    assert seconds_to_hms(3661) == "1h 01m 01s"
    assert seconds_to_hms(7325) == "2h 02m 05s"
