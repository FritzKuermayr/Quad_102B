from __future__ import annotations

import math


class k_solver:
    """Inverse kinematics for one 2-DOF five-bar leg."""

    def __init__(self, d=30, l1=33, l2=44, l1p=33, l2p=44):
        self.d = d
        self.l1 = l1
        self.l2 = l2
        self.l1p = l1p
        self.l2p = l2p

    def ik_solve(self, x, y, deg=True, rounding=3):
        try:
            c1 = math.sqrt((x - self.d) ** 2 + y**2)
            c2 = math.sqrt(x**2 + y**2)
            a1 = math.acos((c1**2 + self.d**2 - c2**2) / (2 * c1 * self.d))
            a2 = math.acos((c2**2 + self.d**2 - c1**2) / (2 * c2 * self.d))
            b1 = math.acos((c1**2 + self.l1**2 - self.l2**2) / (2 * c1 * self.l1))
            b2 = math.acos((c2**2 + self.l1p**2 - self.l2p**2) / (2 * c2 * self.l1p))
            q1 = math.pi - a1 - b1
            q2 = a2 + b2
        except (ValueError, ZeroDivisionError):
            return 0.0, 0.0, False

        if deg:
            q1 = math.degrees(q1)
            q2 = math.degrees(q2)

        return round(q1, rounding), round(q2, rounding), True
