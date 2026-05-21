"""HTTP client for the transport API."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from .constants import API_URL

# Spring's Jackson default serializes LocalDateTime with nanosecond precision;
# Python's fromisoformat only supports up to microseconds before 3.11. Trim
# the fractional part to 6 digits.
_NANO_RE = re.compile(r"(\.\d{6})\d+$")

# (connect, read) — short connect catches DNS/TCP issues fast; longer read
# tolerates a momentarily slow VPS.
_HTTP_TIMEOUT_SECONDS = (5.0, 8.0)


@dataclass(frozen=True)
class Line:
    line: str
    stop: str
    direction: str
    next_departures_minutes: tuple[int, ...]


@dataclass(frozen=True)
class Velib:
    station_name: str
    mechanical: int
    electrical: int


@dataclass(frozen=True)
class Weather:
    temperature_c: float
    weather_code: int
    wind_speed_kmh: float
    precipitation_mm: float
    is_day: bool


@dataclass(frozen=True)
class Snapshot:
    lines: tuple[Line, ...]
    velib: Velib
    weather: Weather
    disruptions: tuple[str, ...]
    generated_at: datetime


def fetch() -> Snapshot:
    if not API_URL:
        raise RuntimeError(
            "DASHBOARD_API_URL is not set. Export it in your shell, or on the "
            "Pi set it in /etc/default/ratp-dashboard (see deploy/install.sh)."
        )
    response = requests.get(
        API_URL,
        headers={"Accept": "application/json"},
        timeout=_HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return _parse(response.json())


def _parse(payload: dict[str, Any]) -> Snapshot:
    velib = payload.get("velib") or {}
    weather = payload.get("weather") or {}
    return Snapshot(
        lines=tuple(
            Line(
                line=item.get("line", "?"),
                stop=item.get("stop", ""),
                direction=item.get("direction", ""),
                next_departures_minutes=tuple(item.get("nextDeparturesMinutes") or ()),
            )
            for item in (payload.get("lines") or ())
        ),
        velib=Velib(
            station_name=velib.get("stationName", "—"),
            mechanical=int(velib.get("mechanical") or 0),
            electrical=int(velib.get("electrical") or 0),
        ),
        weather=Weather(
            temperature_c=float(weather.get("temperatureC") or 0.0),
            weather_code=int(weather.get("weatherCode") or 0),
            wind_speed_kmh=float(weather.get("windSpeedKmh") or 0.0),
            precipitation_mm=float(weather.get("precipitationMm") or 0.0),
            is_day=bool(weather.get("isDay", True)),
        ),
        disruptions=tuple(payload.get("disruptions") or ()),
        generated_at=_parse_datetime(payload.get("generatedAt") or ""),
    )


def _parse_datetime(value: str) -> datetime:
    if not value:
        return datetime.now()
    return datetime.fromisoformat(_NANO_RE.sub(r"\1", value))
