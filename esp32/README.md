# esp32

ESP32 dashboard (planned, not started yet).

Data source: `docs/api.md` (shared contract with the other targets).

## Decisions to make

- **Toolchain**: PlatformIO + Arduino framework, or native ESP-IDF?
- **Display**: exact model (Waveshare ePaper, LilyGo T5, T-Display S3, etc.) —
  drives palette and render dimensions
- **Connectivity**: Wi-Fi in station mode (credentials in encrypted flash or via a
  captive portal)
- **Refresh**: minute-by-minute, deep sleep between cycles when on battery

## Plan

- Minimal HTTP client against the endpoint, JSON parsing via ArduinoJson
- Renderer dedicated to the chosen display format
- OTA updates if needed
- Freshness indicator when the last data is older than 5 min (see `docs/api.md`)
