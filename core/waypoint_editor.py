"""
Runtime waypoint editor — add/remove waypoints during simulation.
"""
from core.navigation import Waypoint
from config import WP_EDIT


class WaypointEditor:
    """Manage runtime waypoint list (add, remove, clear)."""

    def __init__(self, navigator):
        self.navigator = navigator

    # ────────────────────────────────
    def add(self, x, y=None, alt=None):
        """Add a new waypoint. Returns True on success."""
        if len(self.navigator.waypoints) >= WP_EDIT["max_count"]:
            print("[wp_editor] max waypoints reached")
            return False
        if y is None:
            y = WP_EDIT["default_y"]
        if alt is None:
            alt = WP_EDIT["default_alt"]
        self.navigator.waypoints.append(Waypoint(x, y, alt))
        self.navigator.done = False
        print(f"[wp_editor] added WP #{len(self.navigator.waypoints)-1} "
              f"at ({x:.1f}, {y:.1f}, {alt:.1f})")
        return True

    # ────────────────────────────────
    def remove_last(self):
        """Remove most recent waypoint."""
        if not self.navigator.waypoints:
            print("[wp_editor] no waypoints to remove")
            return False
        wp = self.navigator.waypoints.pop()
        print(f"[wp_editor] removed WP at ({wp.x:.1f}, {wp.y:.1f}, {wp.alt:.1f})")
        if self.navigator.index >= len(self.navigator.waypoints):
            self.navigator.index = max(0, len(self.navigator.waypoints) - 1)
            self.navigator.done = len(self.navigator.waypoints) == 0
        return True

    # ────────────────────────────────
    def clear_all(self):
        self.navigator.waypoints.clear()
        self.navigator.index = 0
        self.navigator.done = True
        print("[wp_editor] cleared all waypoints")

    # ────────────────────────────────
    def add_relative(self, state, dx, dy=0.0, alt=None):
        """Add waypoint relative to aircraft current position."""
        if alt is None:
            alt = state.alt
        return self.add(state.x + dx, state.y + dy, alt)