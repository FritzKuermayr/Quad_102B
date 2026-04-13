from __future__ import annotations

import argparse

from humidity_control import HumidityController
from keyboard_interface import KeyboardInterface
from q8gait.config_rx24f import default_config
from q8gait.kinematics_solver import k_solver
from q8gait.motion_runner import MotionRunner
from q8gait.robot import Robot

CENTER_DIST_MM = 30
UPPER_LINK_MM = 33
LOWER_LINK_MM = 44


def main() -> None:
    args = parse_args()
    cfg = default_config(port=args.port, baudrate=args.baudrate)
    robot = Robot(cfg)
    leg = k_solver(CENTER_DIST_MM, UPPER_LINK_MM, LOWER_LINK_MM, UPPER_LINK_MM, LOWER_LINK_MM)
    keyboard = KeyboardInterface()
    humidity_controller = HumidityController()
    robot_torque_enabled = False

    try:
        try:
            humidity_controller.start()
        except Exception as exc:
            print(f"[main] humidity control unavailable; continuing robot control: {exc}")

        robot.open()
        robot.torque(True)
        robot_torque_enabled = True

        runner = MotionRunner(
            robot,
            leg,
            gait_name=args.gait,
            hz=args.hz,
            torque_limit=args.torque_limit,
            moving_speed=args.moving_speed,
        )
        runner.move_to_neutral(seconds=1.0)
        runner.loop_forever(keyboard)
    except KeyboardInterrupt:
        print("\n[main] stopping")
    finally:
        humidity_controller.stop()
        keyboard.close()
        try:
            if robot_torque_enabled:
                robot.torque(False)
        finally:
            robot.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Keyboard controller for the quadruped.")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Dynamixel USB adapter, e.g. /dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=1000000, help="Dynamixel bus baudrate")
    parser.add_argument("--gait", choices=("TROT_LOW", "TROT", "WALK"), default="TROT_LOW")
    parser.add_argument("--hz", type=int, default=50, help="control loop rate")
    parser.add_argument("--torque-limit", type=int, default=600, help="0..1023")
    parser.add_argument("--moving-speed", type=int, default=0, help="0 means maximum motor speed on RX/AX series")
    return parser.parse_args()


if __name__ == "__main__":
    main()
