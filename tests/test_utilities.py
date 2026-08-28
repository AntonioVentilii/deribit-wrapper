from datetime import datetime, timezone

from deribit_wrapper.utilities import from_dt_to_ts, from_ts_to_dt, seconds_to_hms


def test_from_dt_to_ts_milliseconds():
    assert from_dt_to_ts("2024-01-01") == 1704067200000


def test_from_dt_to_ts_seconds():
    assert from_dt_to_ts("2024-01-01", milliseconds=False) == 1704067200


def test_from_dt_to_ts_str_and_datetime_agree():
    assert from_dt_to_ts(datetime(2024, 1, 1)) == from_dt_to_ts("2024-01-01")


def test_from_dt_to_ts_naive_datetime_is_utc():
    assert from_dt_to_ts(datetime(2024, 1, 1), milliseconds=False) == 1704067200


def test_from_dt_to_ts_aware_datetime_is_converted():
    aware = datetime(2024, 1, 1, 1, tzinfo=timezone.utc)
    assert from_dt_to_ts(aware, milliseconds=False) == 1704067200 + 3600


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


def test_roundtrip():
    dt = datetime(2023, 6, 15, 12, 30)
    assert from_ts_to_dt(from_dt_to_ts(dt)) == dt


def test_roundtrip_from_timestamp():
    ts = 1704067200000
    assert from_dt_to_ts(from_ts_to_dt(ts)) == ts


def test_seconds_to_hms():
    assert seconds_to_hms(0) == "0h 00m 00s"
    assert seconds_to_hms(59) == "0h 00m 59s"
    assert seconds_to_hms(60) == "0h 01m 00s"
    assert seconds_to_hms(3661) == "1h 01m 01s"
    assert seconds_to_hms(7325) == "2h 02m 05s"


def test_from_dt_to_ts_keeps_millisecond_precision():
    assert from_dt_to_ts("2024-01-01 00:00:00.123") == 1704067200123


def test_from_dt_to_ts_seconds_truncates_subseconds():
    assert from_dt_to_ts("2024-01-01 00:00:00.999", milliseconds=False) == 1704067200
