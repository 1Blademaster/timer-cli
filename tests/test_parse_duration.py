"""Tests for parseDurationString: duration must match fully, no trailing garbage."""

from timer.__main__ import parseDurationString


def test_valid_durations_still_parse():
    assert parseDurationString("25m") == (True, [None, "25m", None])
    assert parseDurationString("1h30m") == (True, ["1h", "30m", None])
    assert parseDurationString("15m30s") == (True, [None, "15m", "30s"])
    assert parseDurationString("2h") == (True, ["2h", None, None])
    assert parseDurationString("45s") == (True, [None, None, "45s"])


def test_trailing_garbage_is_rejected():
    # Previously `re.match` accepted a valid prefix and silently ignored
    # the rest, so "10mXYZ" was treated as a 10 minute timer.
    for bad in ["10mXYZ", "1h30", "5mabc", "25m ", "1h2m3sx", "--help"]:
        ok, _ = parseDurationString(bad)
        assert ok is False, f"{bad!r} should be rejected"


def test_empty_and_invalid_are_rejected():
    ok, _ = parseDurationString("")
    assert ok is False
    ok, _ = parseDurationString("hello")
    assert ok is False
