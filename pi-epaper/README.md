# pi-epaper

ePaper dashboard for Raspberry Pi + Waveshare 2.9". Currently targets the monochrome
296×128 variant.

Data contract: [../docs/api.md](../docs/api.md).

## Preview

```
┌─────────────────────────────────────────────────────┐
│ ☁☀ 21°  V —                              13:20      │  ← top bar (24px)
├─────────────────────────────────────────────────────┤
│ ▌T6 ▐  Châtillon-Montrouge                1'  11'   │
│ ▌394▐  Issy Val de Seine                  4'  21'   │
│ ▌388▐  Porte d'Orléans                   27'  39'   │
│ ▌388▐  Bourg-la-Reine                    26'  41'   │
└─────────────────────────────────────────────────────┘
```

A hollow circle appears to the left of the clock when the last successful API fetch is
older than 5 minutes.

## Approach

The renderer (`dashboard/render.py`) is **fully hardware-agnostic**: it produces a 296×128
1-bit PIL image. The `display.py` module (Pi-only) takes that image and pushes it to the
panel via the Waveshare driver. This separation lets you iterate on the layout from Mac
without touching the Pi, then push the exact same render to the screen.

## Dev (Mac)

Requires Python 3.9+ and `pip`. Work from inside `pi-epaper/`:

```bash
cd pi-epaper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Point the client at your endpoint (or skip and use --offline below)
export DASHBOARD_API_URL=https://your-host/api/spring/transport

# Render from the live API
python -m dashboard preview

# Render offline (static fixture, no network — no env var needed)
python -m dashboard preview --offline

# Custom output path
python -m dashboard preview -o /tmp/test.png

open preview.png
```

The PNG is at the panel's real resolution (296×128). Open it at 100% to see what the
display will show.

> **Fonts**: on macOS the loader falls back to Arial/Helvetica when DejaVu Sans isn't
> installed. For a render identical to the Pi's:
> `brew tap homebrew/cask-fonts && brew install --cask font-dejavu`.

## Tests

Unit tests cover the JSON parser, the renderer's pure helpers, and a no-crash sweep over
every WMO code the renderer handles.

```bash
cd pi-epaper
pip install -r requirements-dev.txt
python -m pytest tests/
```

No hardware needed — the tests don't import `display.py`.

## Deploy (Raspberry Pi)

### Hardware requirements

- Raspberry Pi (tested on 3B+/4/Zero 2 W) running Raspberry Pi OS Bookworm
- Waveshare 2.9" ePaper module (see [Identify the panel](#identify-the-panel))
- SPI wiring (standard Waveshare HAT — just plug onto the GPIO header)
- SPI enabled: `sudo raspi-config` → Interface Options → SPI → Enable, then reboot

### Setup

```bash
git clone git@github.com:aflichy/ratp-dashboards.git ~/ratp-dashboards
cd ~/ratp-dashboards/pi-epaper
bash deploy/install.sh
```

`install.sh` will:
1. Install system packages (`python3-venv`, `fonts-dejavu-core`, `libopenjp2-7`)
2. Verify the SPI kernel module is loaded
3. Create a venv and install Python deps (pinned to specific versions in `requirements.txt`)
4. Clone the official Waveshare repo (pinned to a known commit) and pip-install it
5. Prompt for `DASHBOARD_API_URL` (on first run only) and write `/etc/default/ratp-dashboard`
6. Drop the `ratp-dashboard.service` systemd unit in place and start it

To change the endpoint later, edit `/etc/default/ratp-dashboard` and `sudo systemctl restart ratp-dashboard`.

The service ships with conservative systemd hardening enabled by default
(`NoNewPrivileges`, `PrivateTmp`, kernel/cgroup protections, etc.). Stricter
filesystem isolation (`ProtectSystem=strict`, `ProtectHome=read-only`) is wired
in but commented out — uncomment in `deploy/ratp-dashboard.service` once verified
on real hardware (the Waveshare driver hits `/dev/spidev0.0` and `/dev/gpiomem`).

### Operations

```bash
# Status
sudo systemctl status ratp-dashboard

# Live logs
journalctl -u ratp-dashboard -f

# Restart after a code change
sudo systemctl restart ratp-dashboard

# One-shot test (no daemon)
.venv/bin/python -m dashboard run --once

# Stop cleanly (puts the panel to sleep)
sudo systemctl stop ratp-dashboard
```

### Timezone

The clock shows the Pi's local time. Set it to Europe/Paris:
```bash
sudo timedatectl set-timezone Europe/Paris
```

## Identify the panel

`dashboard/display.py` loads the `epd2in9_V2` driver by default. If your screen is a
different variant, change the `_MODEL` constant.

| Waveshare reference      | Python module    | Colors                | Refresh   |
|--------------------------|------------------|-----------------------|-----------|
| 2.9inch e-Paper V2       | `epd2in9_V2`     | B&W                   | ~2 s      |
| 2.9inch e-Paper V4       | `epd2in9_V4`     | B&W (partial refresh) | ~0.3 s    |
| 2.9inch e-Paper (B) V4   | `epd2in9b_V4`    | B&W + red             | ~15 s     |

How to identify:
1. **Silk-screen on the back of the PCB** — the reference is printed (e.g. `2.9inch e-Paper V2`)
2. **Original packaging** — model printed on the box
3. **Runtime probe** on the Pi:
   ```bash
   .venv/bin/python -c "from waveshare_epd import epd2in9_V2; epd2in9_V2.EPD().init()"
   ```
   If no error, that's the right driver. Otherwise try `epd2in9_V4`, then `epd2in9b_V4`.

For the 3-color (B) variant, `render.py` will need to be extended to emit a second plane
(red) — the current palette is 1-bit only.

## Layout

```
pi-epaper/
├── dashboard/                     # Python package
│   ├── __init__.py                # Constants (URL, dimensions)
│   ├── __main__.py                # CLI: preview / run
│   ├── client.py                  # HTTP + typed dataclasses
│   ├── render.py                  # 296×128 1-bit PIL renderer
│   ├── weather_icons.py           # Weather glyphs from PIL primitives
│   ├── fonts.py                   # Cross-platform font resolution
│   └── display.py                 # Waveshare wrapper (Pi-only)
├── deploy/
│   ├── install.sh                 # One-shot Pi setup
│   └── ratp-dashboard.service     # systemd unit
└── requirements.txt
```

## Configuration knobs

| Knob                         | Where                                                                 |
|------------------------------|-----------------------------------------------------------------------|
| API URL                      | `DASHBOARD_API_URL` env var (Mac: shell; Pi: `/etc/default/ratp-dashboard`) |
| Panel driver                 | `dashboard/display.py` (`_MODEL`)                                     |
| Refresh interval             | `--interval 60` flag on `run` (systemd unit)                          |
| PNG output                   | `--output preview.png` flag on `preview`                              |
| Stale-data threshold         | `_STALE_AFTER_SECONDS` in `dashboard/__main__.py`                     |

## Troubleshooting

**`ModuleNotFoundError: No module named 'PIL'`** — venv not activated or deps missing.
`source .venv/bin/activate && pip install -r requirements.txt`.

**`ModuleNotFoundError: No module named 'waveshare_epd'`** — Pi-only: the driver isn't
in `requirements.txt`, it's installed by `deploy/install.sh` from the official Waveshare repo.

**`ModuleNotFoundError: No module named 'spidev' / 'gpiozero'`** — the Waveshare lib needs
these at startup but doesn't declare them. `install.sh` installs them as part of the deploy.
If you ran the script before the fix landed:
`.venv/bin/pip install spidev gpiozero rpi-lgpio && sudo systemctl restart ratp-dashboard`.

**`RuntimeError: Failed to add edge detection`** — recent Pi OS (Trixie / late Bookworm)
moves GPIO from sysfs to gpiochip; the legacy `RPi.GPIO` can't follow. Affects every Pi
model, not just Pi 5. Swap for the drop-in: `pip uninstall RPi.GPIO; pip install rpi-lgpio`
(fresh installs get this via `install.sh`).

**`OSError: [Errno 22] Invalid argument` from `gpiozero/pins/native.py`** — gpiozero's
auto-detect picked the legacy sysfs factory. Pin it explicitly by adding
`GPIOZERO_PIN_FACTORY=lgpio` to `/etc/default/ratp-dashboard` (fresh installs get this).

**`lgpio.error: 'GPIO busy'`** — another process holds the pin, almost always the systemd
service in its retry loop. `sudo systemctl stop ratp-dashboard` before running a one-shot test.

**Panel stays blank / no refresh** — check that SPI is enabled (`lsmod | grep spi_bcm2835`),
that no other process is holding the SPI bus, and look at the systemd logs.

**`Invalid isoformat string` on `generatedAt`** — Python <3.11 doesn't parse ISO nanoseconds.
The client already truncates — make sure you're up to date (`git pull`).

**Clock is off** — that's the Pi's local time. See [Timezone](#timezone) above.

## Roadmap

- [ ] Test on the real panel and tune the layout
- [ ] Partial refresh on V4 to update only the minute fields (no full-screen flash)
- [ ] 3-color (B) support — highlight imminent departures (<2 min) or disruptions in red
- [ ] Night mode (invert polarity or blank the display)
- [ ] Show disruptions when the backend returns any
- [ ] Optional sort by closest departure
