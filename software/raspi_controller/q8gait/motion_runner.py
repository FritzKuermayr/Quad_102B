from __future__ import annotations

import time
from typing import Optional

from .gait_manager import GAITS, GaitManager
from .kinematics_solver import k_solver
from .robot import Robot

COMMAND_TO_DIRECTION = {
    # MOVEMENT STATE MACHINE STATES:
    # "stop" is the IDLE state. The other commands are active movement states.
    "forward": "f",
    "backward": "b",
    "turn_left": "l",
    "turn_right": "r",
    "stop": None,
}


class MotionRunner:
    def __init__(
        self,
        robot: Robot,
        leg_solver: k_solver,
        gait_name: str = "TROT_LOW",
        hz: int = 50,
        neutral_center_deg: float = 150.0,
        torque_limit: int = 600,
        moving_speed: int = 0,
    ) -> None:
        self.robot = robot
        self.leg = leg_solver
        self.hz = hz
        self.dt = 1.0 / hz
        self.neutral_center_deg = neutral_center_deg
        self.torque_limit = torque_limit
        self.moving_speed = moving_speed
        self.gait_manager = GaitManager(self.leg, GAITS)
        self.current_command = "stop"

        if not self.gait_manager.load_gait(gait_name):
            raise RuntimeError(f"Failed to load gait {gait_name}")

        _, x0, y0, *_ = GAITS[gait_name]
        q1n, q2n, ok = self.leg.ik_solve(x0, y0, True, 3)
        if not ok:
            raise RuntimeError("IK failed for neutral pose.")
        self.q_neutral = [q1n, q2n, q1n, q2n, q1n, q2n, q1n, q2n]

    # SERVICE FUNCTION:
    # Moves all legs to the neutral standing pose. This is used for startup and
    # for the IDLE/"stop" movement state.
    def move_to_neutral(self, seconds: float = 1.0) -> None:
        command = [self.neutral_center_deg] * 8
        for _ in range(max(1, int(seconds * self.hz))):
            self.robot.write_positions_deg(command)
            time.sleep(self.dt)

    # STATE MACHINE TRANSITION LOGIC:
    # Converts keyboard commands into movement states:
    # - "stop"      -> IDLE state, stop gait and hold neutral pose
    # - "forward"   -> forward walking state
    # - "backward"  -> backward walking state
    # - "turn_left" -> left-turn state
    # - "turn_right"-> right-turn state
    # - "quit"      -> shutdown event
    def set_command(self, command: Optional[str]) -> None:
        if command is None or command == self.current_command:
            return

        if command == "quit":
            raise KeyboardInterrupt

        direction = COMMAND_TO_DIRECTION.get(command)
        if direction is None:
            self.gait_manager.stop()
            self.current_command = "stop"
            return

        self.robot.set_torque_limit_all(self.torque_limit)
        self.robot.set_moving_speed_all(self.moving_speed)

        if not self.gait_manager.start_movement(direction):
            self.gait_manager.stop()
            self.current_command = "stop"
            return

        self.current_command = command

    # SERVICE FUNCTION:
    # Sends the next motor command for the current movement state. If the state
    # is IDLE/"stop", it writes the neutral standing pose.
    def tick(self) -> None:
        q_abs = self.gait_manager.tick()
        if q_abs is None:
            self.robot.write_positions_deg([self.neutral_center_deg] * 8)
            return

        self.robot.write_positions_deg(self._recenter_to_neutral(q_abs))

    # STATE MACHINE DRIVER:
    # Runs the movement state machine continuously. The event checker is
    # keyboard_interface.poll(), and the service function is tick().
    def loop_forever(self, keyboard_interface) -> None:
        next_tick = time.perf_counter()
        while True:
            self.set_command(keyboard_interface.poll())

            now = time.perf_counter()
            if now >= next_tick:
                self.tick()
                next_tick += self.dt
            else:
                time.sleep(max(0.0, next_tick - now))

    # SERVICE FUNCTION:
    # Converts gait-generated absolute joint angles into robot-centered commands.
    def _recenter_to_neutral(self, q_abs_8: list[float]) -> list[float]:
        return [
            self.neutral_center_deg + (q_abs_8[i] - self.q_neutral[i])
            for i in range(8)
        ]
