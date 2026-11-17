"""
Flight phase state machine:
STANDBY → TAKE_OFF → CRUISE → LANDING → GROUND
"""
from enum import Enum, auto


class Phase(Enum):
    STANDBY = auto()
    TAKE_OFF = auto()
    CRUISE = auto()
    LANDING = auto()
    GROUND = auto()
    DONE = auto()


class StateMachine:
    def __init__(self, mission_cfg):
        self.cfg = mission_cfg
        self.phase = Phase.STANDBY
        self.takeoff_alt = mission_cfg["takeoff_alt"]
        self.landing_alt = mission_cfg["landing_alt"]
        self.cruise_alt = mission_cfg["cruise_altitude"]
        self.landing_x = mission_cfg["landing_pos"][0]

    def reset(self):
        self.phase = Phase.STANDBY

    # ────────────────────────────────
    def update(self, state, navigator):
        """Transitions based on state + navigator status."""
        p = self.phase

        if p == Phase.STANDBY:
            if state.throttle > 0.05:
                self.phase = Phase.TAKE_OFF

        elif p == Phase.TAKE_OFF:
            if not state.on_ground and state.alt >= self.takeoff_alt:
                self.phase = Phase.CRUISE

        elif p == Phase.CRUISE:
            if navigator.done:
                self.phase = Phase.LANDING
                navigator.reset_descent = True  # marker

        elif p == Phase.LANDING:
            if state.alt <= self.landing_alt and abs(state.x - self.landing_x) < 60.0:
                self.phase = Phase.GROUND

        elif p == Phase.GROUND:
            if state.airspeed < 0.5:
                self.phase = Phase.DONE

        return self.phase

    # ────────────────────────────────
    def describe(self):
        return self.phase.name