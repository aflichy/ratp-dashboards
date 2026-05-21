"""Tests for the API client parser."""

from datetime import datetime

from dashboard.client import _parse, _parse_datetime


def _full_payload() -> dict:
    return {
        "lines": [
            {"line": "T6", "stop": "Centre", "direction": "X", "nextDeparturesMinutes": [1, 11]},
        ],
        "velib": {"stationName": "Foo", "mechanical": 3, "electrical": 2},
        "weather": {
            "temperatureC": 21.2,
            "weatherCode": 2,
            "windSpeedKmh": 5.1,
            "precipitationMm": 0.0,
            "isDay": True,
        },
        "disruptions": [],
        "generatedAt": "2026-05-21T11:19:21.232490504",
    }


def test_parse_happy_path():
    snap = _parse(_full_payload())
    assert len(snap.lines) == 1
    assert snap.lines[0].line == "T6"
    assert snap.lines[0].next_departures_minutes == (1, 11)
    assert snap.velib.station_name == "Foo"
    assert snap.velib.mechanical == 3
    assert snap.weather.temperature_c == 21.2
    assert snap.weather.is_day is True


def test_parse_velib_null_falls_back_to_dashes():
    payload = _full_payload()
    payload["velib"] = None
    snap = _parse(payload)
    assert snap.velib.station_name == "—"
    assert snap.velib.mechanical == 0
    assert snap.velib.electrical == 0


def test_parse_weather_null_uses_safe_defaults():
    payload = _full_payload()
    payload["weather"] = None
    snap = _parse(payload)
    assert snap.weather.temperature_c == 0.0
    assert snap.weather.weather_code == 0
    assert snap.weather.is_day is True


def test_parse_missing_lines():
    payload = _full_payload()
    payload["lines"] = None
    snap = _parse(payload)
    assert snap.lines == ()


def test_parse_line_with_null_departures():
    payload = _full_payload()
    payload["lines"][0]["nextDeparturesMinutes"] = None
    snap = _parse(payload)
    assert snap.lines[0].next_departures_minutes == ()


def test_parse_disruptions_null_treated_as_empty():
    payload = _full_payload()
    payload["disruptions"] = None
    snap = _parse(payload)
    assert snap.disruptions == ()


def test_parse_datetime_truncates_nanoseconds():
    parsed = _parse_datetime("2026-05-21T11:19:21.232490504")
    assert isinstance(parsed, datetime)
    assert parsed.year == 2026
    assert parsed.microsecond == 232490


def test_parse_datetime_handles_empty_string():
    parsed = _parse_datetime("")
    assert isinstance(parsed, datetime)
