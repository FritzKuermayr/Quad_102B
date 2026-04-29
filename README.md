# Quadruped Keyboard Control

This repository contains the current Raspberry Pi control software for the quadruped.
The robot is controlled directly on the Raspberry Pi through an SSH terminal.
No hotspot-based setup is used.

## Current Setup

- The Raspberry Pi and laptop are on the same regular Wi-Fi network.
- The code lives on the Pi in `~/Quad_102B`.
- Updates are pulled from GitHub:
  `https://github.com/FritzKuermayr/Quad_102B.git`
- Movement is controlled with `h/j/k/l`. Arrow keys remain available as a fallback,
  but they can be less reliable depending on the terminal or SSH client.
- The default Dynamixel port is `/dev/ttyUSB0`.
- The default baudrate is `1000000`.
- Motors: Dynamixel RX-24F, protocol `1.0`.

## Project Structure

```text
software/
├── raspi_controller/
│   ├── main.py
│   ├── g_key_leg_test.py
│   ├── keyboard_interface.py
│   └── q8gait/
│       ├── config_rx24f.py
│       ├── gait_generator.py
│       ├── gait_manager.py
│       ├── kinematics_solver.py
│       ├── motion_runner.py
│       └── robot.py
├── dynamixel_tools/
├── requirements.txt
└── setup_pi.sh
```

## Prepare the Raspberry Pi

1. Flash Raspberry Pi OS to the microSD card.
2. Enable SSH during flashing or afterwards.
3. Connect the Pi to the regular Wi-Fi network. No hotspot is required.
4. Find the Pi's IP address:

```bash
hostname -I
```

Or try the hostname from the laptop:

```bash
ssh pi@raspberrypi.local
```

If the hostname does not work:

```bash
ssh pi@<PI_IP_ADRESSE>
```

## Install the Code on the Pi

On the Pi:

```bash
cd ~
git clone https://github.com/FritzKuermayr/Quad_102B.git
cd ~/Quad_102B
chmod +x software/setup_pi.sh
./software/setup_pi.sh
```

If the repository already exists on the Pi, update it:

```bash
cd ~/Quad_102B
git pull origin main
```

Then plug in the Dynamixel USB adapter and check it:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

The adapter is usually `/dev/ttyUSB0`. If needed, set the port permissions:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

## Python Dependencies

Normally `software/setup_pi.sh` handles everything. If a Python module is
missing, reinstall dependencies from inside the active project directory:

```bash
cd ~/Quad_102B
source .venv/bin/activate
python -m pip install -r software/requirements.txt
```

## Start Keyboard Control

Place the robot on a stand for the first test so the legs can move freely.

```bash
cd ~/Quad_102B
source .venv/bin/activate
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait TROT_LOW --torque-limit 400
```

Keys:

```text
k      walk forward
j      walk backward
h      turn left
l      turn right
Space  stop and hold neutral stance
s      stop and hold neutral stance
q      quit safely and disable torque
```

Arrow keys also work if the terminal passes them through correctly:

```text
↑  walk forward
↓  walk backward
←  turn left
→  turn right
```

When input is detected, the terminal prints messages such as:

```text
[keyboard] k -> forward
```

If the motors react too weakly while the robot is on the stand, increase the torque limit:

```bash
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait TROT_LOW --torque-limit 500
```

Alternative gaits:

```bash
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait WALK --torque-limit 500
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait TROT --torque-limit 500
```

## Single-Leg Test

This separate script moves only the front-left leg slightly away from neutral
and then returns it. It is intended only for motor and mapping checks.

```bash
cd ~/Quad_102B
source .venv/bin/activate
python software/raspi_controller/g_key_leg_test.py --port /dev/ttyUSB0
```

Keys:

```text
g  move the front-left leg briefly
q  quit and disable torque
```

Mapping for this test:

```text
FL_q1 = Motor ID 1
Neutral = 150 deg
Test movement = 165 deg for 0.35 s, then back to 150 deg
```

## Important Checks

- Motor IDs and ordering are defined in `software/raspi_controller/q8gait/config_rx24f.py`.
- On startup, `main.py` moves all motors to the neutral pose.
- On exit with `q` or `Ctrl+C`, torque is disabled.
- Put the robot on a stand before the first motion test.
- If `dynamixel_sdk` is missing: `python -m pip install -r software/requirements.txt`.
- If `/dev/ttyUSB0` is not accessible, check the USB adapter and, if needed, run
  `sudo chmod a+rw /dev/ttyUSB0`.
