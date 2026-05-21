#!/usr/bin/env bash
# One-shot Raspberry Pi setup. Run from the pi-epaper directory on the Pi:
#   bash deploy/install.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="ratp-dashboard"

echo "==> System packages"
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip libopenjp2-7 fonts-dejavu-core

echo "==> SPI enabled?"
if ! lsmod | grep -q spi_bcm2835; then
  echo "    SPI module not loaded. Enable with 'sudo raspi-config' → Interface Options → SPI, then reboot."
  exit 1
fi

echo "==> Virtualenv"
python3 -m venv "$PROJECT_DIR/.venv"
"$PROJECT_DIR/.venv/bin/pip" install --upgrade pip
"$PROJECT_DIR/.venv/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

echo "==> Waveshare driver"
# The Waveshare Python driver isn't on PyPI under a maintained name —
# install directly from their official repo, pinned to a known commit.
WAVESHARE_DIR="${WAVESHARE_DIR:-$PROJECT_DIR/.vendor/waveshare-epd}"
WAVESHARE_SHA="86aa9932f471a50157cf02fafadc2c1b4a965449"
if [[ ! -d "$WAVESHARE_DIR" ]]; then
  mkdir -p "$(dirname "$WAVESHARE_DIR")"
  git clone https://github.com/waveshareteam/e-Paper.git "$WAVESHARE_DIR"
fi
git -C "$WAVESHARE_DIR" fetch --quiet origin "$WAVESHARE_SHA"
git -C "$WAVESHARE_DIR" checkout --quiet "$WAVESHARE_SHA"
"$PROJECT_DIR/.venv/bin/pip" install "$WAVESHARE_DIR/RaspberryPi_JetsonNano/python"

echo "==> Endpoint configuration"
ENV_FILE="/etc/default/$SERVICE_NAME"
if sudo test -f "$ENV_FILE"; then
  echo "    $ENV_FILE already exists, leaving alone."
else
  read -r -p "    API URL (DASHBOARD_API_URL): " api_url
  printf 'DASHBOARD_API_URL=%s\n' "$api_url" | sudo tee "$ENV_FILE" > /dev/null
  sudo chmod 644 "$ENV_FILE"
fi

echo "==> systemd unit"
sudo cp "$PROJECT_DIR/deploy/$SERVICE_NAME.service" "/etc/systemd/system/$SERVICE_NAME.service"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME.service"
sudo systemctl restart "$SERVICE_NAME.service"

echo "==> Done. Logs:  journalctl -u $SERVICE_NAME -f"
