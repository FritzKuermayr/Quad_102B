from __future__ import annotations

from .gait_generator import generate_trot_trajectories, generate_walk_trajectories

# Format: [type, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks]
GAITS = {
    "TROT_LOW": ["trot", 15.0, 25.0, 20.0, 10.0, 0.0, 15, 30],
    "TROT": ["trot", 15.0, 43.36, 40.0, 20.0, 0.0, 15, 30],
    "WALK": ["walk", 15.0, 43.36, 30.0, 20.0, 0.0, 20, 140],
}


class GaitManager:
    def __init__(self, leg, available_gaits=None) -> None:
        self.leg = leg
        self.available_gaits = available_gaits if available_gaits is not None else GAITS
        self.current_gait = None
        self.current_trajectories = {}
        self.current_trajectory = None
        self.current_direction = None
        self.phase_index = 0

    def load_gait(self, gait_name: str) -> bool:
        if gait_name not in self.available_gaits:
            return False

        gait_params = self.available_gaits[gait_name]
        gait_type = gait_params[0]

        if gait_type == "trot":
            trajectories = generate_trot_trajectories(self.leg, gait_params)
        elif gait_type == "walk":
            trajectories = generate_walk_trajectories(self.leg, gait_params)
        else:
            return False

        if trajectories is None:
            return False

        self.current_gait = gait_name
        self.current_trajectories = trajectories
        self.stop()
        print(f"[gait] loaded {gait_name}")
        return True

    def start_movement(self, direction: str) -> bool:
        if direction not in self.current_trajectories:
            return False

        if direction != self.current_direction:
            self.phase_index = 0

        self.current_direction = direction
        self.current_trajectory = self.current_trajectories[direction]
        return True

    def tick(self):
        if self.current_trajectory is None:
            return None

        pos = self.current_trajectory[self.phase_index % len(self.current_trajectory)]
        self.phase_index = (self.phase_index + 1) % len(self.current_trajectory)
        return pos

    def stop(self) -> None:
        self.current_trajectory = None
        self.current_direction = None
        self.phase_index = 0
