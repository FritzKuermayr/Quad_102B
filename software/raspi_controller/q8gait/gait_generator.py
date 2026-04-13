from __future__ import annotations

import math


def generate_trot_trajectories(leg, gait_params):
    _, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks = gait_params

    forward = _single_leg_trajectory(
        leg, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks, 1.0
    )
    backward = _single_leg_trajectory(
        leg, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks, -1.0
    )
    if forward is None or backward is None:
        return None

    phase_shift = len(forward) // 2
    forward_shifted = _shift(forward, phase_shift)
    backward_shifted = _shift(backward, phase_shift)

    return {
        "f": _combine(forward, forward_shifted, forward_shifted, forward),
        "b": _combine(backward, backward_shifted, backward_shifted, backward),
        "l": _combine(backward, forward_shifted, backward_shifted, forward),
        "r": _combine(forward, backward_shifted, forward_shifted, backward),
    }


def generate_walk_trajectories(leg, gait_params):
    _, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks = gait_params

    forward = _single_leg_trajectory(
        leg, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks, 1.0
    )
    backward = _single_leg_trajectory(
        leg, x0, y0, x_range, y_lift, y_push, lift_ticks, ground_ticks, -1.0
    )
    if forward is None or backward is None:
        return None

    quarter = len(forward) // 4
    f1, f2, f3, f4 = forward, _shift(forward, quarter), _shift(forward, 2 * quarter), _shift(forward, 3 * quarter)
    b1, b2, b3, b4 = backward, _shift(backward, quarter), _shift(backward, 2 * quarter), _shift(backward, 3 * quarter)

    return {
        "f": _combine(f1, f2, f3, f4),
        "b": _combine(b1, b2, b3, b4),
        "l": _combine(b1, f2, b3, f4),
        "r": _combine(f1, b2, f3, b4),
    }


def _single_leg_trajectory(
    leg,
    x0: float,
    y0: float,
    x_range: float,
    y_lift: float,
    y_push: float,
    lift_ticks: int,
    ground_ticks: int,
    direction: float,
):
    if y0 - y_lift < 5:
        return None

    trajectory = []
    stride = x_range * direction
    x = x0 - stride / 2
    lift_step = stride / lift_ticks
    ground_step = stride / ground_ticks

    for index in range(lift_ticks + ground_ticks):
        if index < lift_ticks:
            x += lift_step
            y = y0 - math.sin((index + 1) * math.pi / lift_ticks) * y_lift
        else:
            x -= ground_step
            y = y0 + math.sin((index - lift_ticks + 1) * math.pi / ground_ticks) * y_push

        q1, q2, ok = leg.ik_solve(x, y, True, 3)
        if not ok:
            return None
        trajectory.append([q1, q2])

    return trajectory


def _shift(trajectory, offset: int):
    offset %= len(trajectory)
    return trajectory[offset:] + trajectory[:offset]


def _combine(front_left, front_right, back_left, back_right):
    combined = []
    for i in range(len(front_left)):
        combined.append(
            [
                front_left[i][0],
                front_left[i][1],
                front_right[i][0],
                front_right[i][1],
                back_left[i][0],
                back_left[i][1],
                back_right[i][0],
                back_right[i][1],
            ]
        )
    return combined
