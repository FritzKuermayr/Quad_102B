#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "=== Installing Raspberry Pi system packages ==="
sudo apt update
sudo apt install -y git build-essential python3-venv python3-pip i2c-tools

echo "=== Enabling Raspberry Pi I2C bus for SHT40 ==="
if command -v raspi-config >/dev/null 2>&1; then
  sudo raspi-config nonint do_i2c 0
fi

echo "=== Installing DynamixelSDK for Python ==="
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/software/requirements.txt"

echo "=== Optional: building Dynamixel C tools ==="
if [ -d "$PROJECT_DIR/software/dynamixel_tools" ]; then
  make -C "$PROJECT_DIR/software/dynamixel_tools"
fi

echo
echo "Setup complete."
echo "Before running the robot, plug in the Dynamixel USB adapter and allow access:"
echo "  sudo chmod a+rw /dev/ttyUSB0"
echo "You can check the SHT40 I2C connection with:"
echo "  i2cdetect -y 1"
