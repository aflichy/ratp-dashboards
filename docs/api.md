# API — `/api/spring/transport`

Source of truth for the data contract consumed by every dashboard
(`pi-epaper`, `ios-widget`, `esp32`). Any backend change should update this document,
and every target should align.

## Endpoint

```
GET https://antoineflichy.fr/api/spring/transport
Accept: application/json
```

HTTP 200, `Content-Type: application/json`. No authentication. Spring backend with a
server-side refresh on a one-minute cadence.

## Shape

```json
{
  "lines": [
    {
      "line": "T6",
      "stop": "Centre de Châtillon",
      "direction": "Châtillon-Montrouge",
      "nextDeparturesMinutes": [1, 11]
    }
  ],
  "velib": {
    "stationName": "Henri Barbusse / Gabriel Péri",
    "mechanical": 0,
    "electrical": 0
  },
  "weather": {
    "temperatureC": 21.2,
    "weatherCode": 2,
    "windSpeedKmh": 5.1,
    "precipitationMm": 0.0,
    "isDay": true
  },
  "disruptions": [],
  "generatedAt": "2026-05-21T11:19:21.232490504"
}
```

## Fields

### `lines[]`

Backend-ordered array. Each entry is one (line, direction) tuple at a stop.

| Field                   | Type      | Notes                                                     |
|-------------------------|-----------|-----------------------------------------------------------|
| `line`                  | string    | RATP line code: `"T6"`, `"388"`, `"394"`, etc.            |
| `stop`                  | string    | Stop name as exposed by the API                           |
| `direction`             | string    | Terminus for this direction                               |
| `nextDeparturesMinutes` | int[0..2] | Minutes until the next 2 departures. May be empty.        |

### `velib`

Current state of the tracked Vélib' station. Can return 0 across the board if the
station is empty (treat as "no bikes available", not an error).

| Field         | Type    | Notes                              |
|---------------|---------|------------------------------------|
| `stationName` | string  | Official station name              |
| `mechanical`  | int     | Mechanical bikes available         |
| `electrical`  | int     | E-bikes available                  |

### `weather`

Local snapshot weather (source: Open-Meteo, fetched server-side).

| Field             | Type    | Notes                                                                       |
|-------------------|---------|-----------------------------------------------------------------------------|
| `temperatureC`    | float   | Temperature in °C                                                           |
| `weatherCode`     | int     | WMO code (see table below)                                                  |
| `windSpeedKmh`    | float   | Wind speed in km/h                                                          |
| `precipitationMm` | float   | Precipitation in mm for the current hour                                    |
| `isDay`           | bool    | `true` during daylight hours (drives sun-vs-moon icon)                      |

#### WMO codes

| Code(s)               | Meaning                              |
|-----------------------|--------------------------------------|
| 0                     | Clear sky                            |
| 1, 2                  | Mainly clear / partly cloudy         |
| 3                     | Overcast                             |
| 45, 48                | Fog                                  |
| 51, 53, 55            | Drizzle (light → dense)              |
| 56, 57                | Freezing drizzle                     |
| 61, 63, 65            | Rain (slight → heavy)                |
| 66, 67                | Freezing rain                        |
| 71, 73, 75            | Snow (slight → heavy)                |
| 77                    | Snow grains                          |
| 80, 81, 82            | Rain showers (slight → violent)      |
| 85, 86                | Snow showers                         |
| 95                    | Thunderstorm                         |
| 96, 99                | Thunderstorm with hail               |

Heavy-intensity codes (warrants a stronger visual rendering): 55, 57, 65, 67, 82.

Official reference: [open-meteo.com/en/docs#weathervariables](https://open-meteo.com/en/docs#weathervariables).

### `disruptions[]`

Array of strings describing active disruptions on the tracked lines. Usually empty.
Free-form format on the backend for now — to be formalized when a real case shows up.

### `generatedAt`

Java `LocalDateTime` (Jackson default) with nanosecond precision. **No explicit timezone** —
assume UTC, the backend runs in UTC.

```
2026-05-21T11:19:21.232490504
```

Gotchas:
- Python `datetime.fromisoformat()` before 3.11 doesn't handle nanoseconds. Truncate to 6
  digits or use a more lenient parser.
- To compare against a local "now", convert both sides to UTC explicitly.

## Expected freshness

The backend refreshes every minute. Client-side:

- Track the timestamp of the last successful fetch locally.
- If more than **5 minutes** have passed without a successful refresh, surface a visual
  indicator (hollow circle, "stale" badge, warning glyph) — without masking the previous
  data.
- **Never** show a full-screen error: the last known data is still more useful than nothing.

## Client robustness

The backend is self-hosted and may return null or empty sub-objects when an upstream
source fails (Vélib' API down, etc.). Recommendations:

- Read every field with a default (`.get(..., default)`).
- Don't crash when `lines`, `velib`, or `weather` is `null` or absent.
- Treat `disruptions: []` and `disruptions: null` identically.
