from __future__ import annotations

import argparse
import select
import sys
import termios
import time
import tty
from typing import List, Optional

from q8gait.config_rx24f import default_config
from q8gait.robot import Robot

NEUTRAL_DEG = 150.0
FRONT_LEFT_Q1_INDEX = 0
LEG_TEST_DELTA_DEG = 15.0
LEG_TEST_HOLD_SEC = 0.35


def main() -> None:
    args = parse_args()
    cfg = default_config(port=args.port, baudrate=args.baudrate)
    robot = Robot(cfg)
    keyboard = SingleKeyReader()

    print(
        "\nG-key leg test\n"
        "  g = move front-left leg a little, then return to neutral\n"
        "  q = quit safely\n"
        "\nPut the robot on a stand before running this test.\n"
    )

    torque_enabled = False
    try:
        robot.open()
        robot.torque(True)
        torque_enabled = True
        robot.write_positions_deg(_neutral_pose())

        while True:
            key = keyboard.read_key()
            if key == "q":
                raise KeyboardInterrupt
            if key == "g":
                print("[g-test] moving front-left leg")
                _move_front_left_leg_once(robot)
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("\n[g-test] stopping")
    finally:
        keyboard.close()
        try:
            robot.write_positions_deg(_neutral_pose())
            if torque_enabled:
                robot.torque(False)
        finally:
            robot.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Press G to move one quadruped leg a little.")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Dynamixel USB adapter, e.g. /dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=1000000, help="Dynamixel bus baudrate")
    return parser.parse_args()


def _move_front_left_leg_once(robot: Robot) -> None:
    pose = _neutral_pose()
    pose[FRONT_LEFT_Q1_INDEX] = NEUTRAL_DEG + LEG_TEST_DELTA_DEG
    robot.write_positions_deg(pose)
    time.sleep(LEG_TEST_HOLD_SEC)
    robot.write_positions_deg(_neutral_pose())


def _neutral_pose() -> List[float]:
    return [NEUTRAL_DEG] * 8


class SingleKeyReader:
    def __init__(self) -> None:
        self._fd = sys.stdin.fileno()
        self._old_settings = None
        try:
            self._old_settings = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        except termios.error:
            print("[g-test] stdin is not a TTY; keyboard input is disabled.")

    def read_key(self) -> Optional[str]:
        if self._old_settings is None:
            return None
        readable, _, _ = select.select([sys.stdin], [], [], 0.0)
        if not readable:
            return None
        return sys.stdin.read(1).lower()

    def close(self) -> None:
        if self._old_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
            self._old_settings = None


if __name__ == "__main__":
    main()
