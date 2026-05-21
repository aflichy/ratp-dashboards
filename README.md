# ratp-dashboards

Monorepo of my dashboards that consume the `GET https://antoineflichy.fr/api/spring/transport`
endpoint to display upcoming transit departures, the state of a Vélib' station, and the
weather around Châtillon.

Each target (ePaper on Pi, iOS widget, ESP32) lives in its own subdirectory with its own
toolchain. The API contract is centralized in `docs/api.md` so that a backend change can
propagate cleanly to every dashboard.

## Targets

| Target             | Status      | Stack                          | Details                              |
|--------------------|-------------|--------------------------------|--------------------------------------|
| **pi-epaper/**     | in progress | Python · Pillow · Waveshare    | Raspberry Pi + 2.9" ePaper, 296×128  |
| **ios-widget/**    | planned     | Swift · WidgetKit              | iPhone Home Screen widget            |
| **esp32/**         | planned     | C++ · PlatformIO (likely)      | ESP32 + display (model TBD)          |

## Architecture

```
                       ┌──────────────────────────────┐
                       │  antoineflichy.fr (Spring)   │
                       │  /api/spring/transport       │
                       └──────────────┬───────────────┘
                                      │ JSON / minute
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
       ┌────────────┐          ┌────────────┐          ┌────────────┐
       │ pi-epaper  │          │ ios-widget │          │   esp32    │
       │ Waveshare  │          │ iPhone     │          │  ESP32 +   │
       │  2.9"      │          │ widget     │          │  display   │
       └────────────┘          └────────────┘          └────────────┘
```

## Shared conventions

- **API contract**: `docs/api.md` (JSON shape, WMO codes, semantics of each field)
- **Freshness**: every target must show a visual indicator when the last successful fetch
  is older than 5 minutes
- **Refresh cadence**: minute-by-minute for always-on targets (Pi, ESP32); on system demand
  for the iOS widget

## Getting started

See the README of the target you're interested in:
- [pi-epaper/README.md](pi-epaper/README.md) — Raspberry Pi + Waveshare 2.9"
- [ios-widget/README.md](ios-widget/README.md) — iOS widget
- [esp32/README.md](esp32/README.md) — ESP32

For the data contract: [docs/api.md](docs/api.md).
