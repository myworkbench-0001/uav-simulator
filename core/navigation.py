"""
Waypoint navigation in XY plane + altitude.
"""
import math


class Waypoint:
    __slots__ = ("x", "y", "alt")
    def __init__(self, x, y, alt):
        self.x = x
        self.y = y
        self.alt = alt


class Navigator:
    """Sequential waypoint tracker with acceptance radius."""

    def __init__(self, waypoints, acceptance_radius):
        # waypoints can be (x, alt) or (x, y, alt)
        self.waypoints = []
        for wp in waypoints:
            if len(wp) == 2:
                self.waypoints.append(Waypoint(wp[0], 0.0, wp[1]))
            else:
                self.waypoints.append(Waypoint(wp[0], wp[1], wp[2]))
        self.radius = acceptance_radius
        self.index = 0
        self.done = len(self.waypoints) == 0

    @property
    def current(self):
        if self.done or self.index >= len(self.waypoints):
            return None
        return self.waypoints[self.index]

    @property
    def previous(self):
        if self.index == 0:
            return None
        return self.waypoints[self.index - 1]

    def reset(self):
        self.index = 0
        self.done = len(self.waypoints) == 0

    def distance_to_current(self, x, y):
        wp = self.current
        if wp is None:
            return float("inf")
        return math.hypot(wp.x - x, wp.y - y)

    def bearing_to_current(self, x, y):
        wp = self.current
        if wp is None:
            return 0.0
        return math.atan2(wp.y - y, wp.x - x)

    def target_altitude(self):
        wp = self.current
        return wp.alt if wp is not None else 0.0

    def update(self, x, y):
        wp = self.current
        if wp is None:
            return False
        if self.distance_to_current(x, y) <= self.radius:
            self.index += 1
            if self.index >= len(self.waypoints):
                self.done = True
            return True
        return False