"""Shared constants for the pi-epaper target."""

import os

# Endpoint URL — read from the DASHBOARD_API_URL environment variable.
# Empty by default; the daemon refuses to fetch with a clear error rather
# than picking a baked-in URL.
#
# Mac dev: `export DASHBOARD_API_URL=https://your-host/api/spring/transport`
# Pi:      set it in /etc/default/ratp-dashboard (see deploy/install.sh)
API_URL = os.environ.get("DASHBOARD_API_URL", "")

DISPLAY_WIDTH = 296
DISPLAY_HEIGHT = 128
