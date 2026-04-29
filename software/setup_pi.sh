#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"

echo "=== Installing Raspberry Pi system packages ==="
sudo apt update
sudo apt install -y git build-essential python3-venv python3-pip

echo "=== Installing DynamixelSDK for Python ==="
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/software/requirements.txt"

echo "=== Optional: building Dynamixel C tools ==="
if [ -d "$PROJECT_DIR/software/dynamixel_tools" ]; then
  if [ -f "$HOME/DynamixelSDK/c/include/dynamixel_sdk.h" ]; then
    make -C "$PROJECT_DIR/software/dynamixel_tools"
  else
    echo "Skipping optional Dynamixel C tools build:"
    echo "  $HOME/DynamixelSDK/c/include/dynamixel_sdk.h not found"
    echo "  Python quadruped control is still ready to use."
  fi
fi

echo
echo "Setup complete."
echo "Before running the robot, plug in the Dynamixel USB adapter and allow access:"
echo "  sudo chmod a+rw /dev/ttyUSB0"
