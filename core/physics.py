"""
Point-mass 3-DOF fixed-wing aircraft dynamics + heading (pseudo-3D).
State: x, y, alt, vx, vy, vz, pitch, bank, heading, throttle
"""
import math
from config import AIRCRAFT, ENV


class AircraftState:
    """Mutable state container for the aircraft (3D position)."""

    __slots__ = ("x", "y", "alt", "vx", "vy", "vz",
                 "pitch", "throttle", "heading", "bank",
                 "time", "on_ground")

    def __init__(self, x, y, alt, heading):
        self.x = x
        self.y = y
        self.alt = alt
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.pitch = 0.0
        self.throttle = 0.0
        self.heading = heading
        self.bank = 0.0
        self.time = 0.0
        self.on_ground = True

    @property
    def airspeed(self):
        return math.sqrt(self.vx**2 + self.vy**2 + self.vz**2)

    @property
    def flight_path_angle(self):
        horiz = math.hypot(self.vx, self.vy)
        if horiz < 1e-3:
            return 0.0
        return math.atan2(self.vz, horiz)

    def copy(self):
        s = AircraftState(self.x, self.y, self.alt, self.heading)
        for k in self.__slots__:
            setattr(s, k, getattr(self, k))
        return s


class AircraftPhysics:
    """Point-mass fixed-wing model with aerodynamic forces."""

    def __init__(self):
        self.cfg = AIRCRAFT
        self.env = ENV

    def _lift_coeff(self, alpha):
        cl = self.cfg["CL0"] + self.cfg["CL_alpha"] * alpha
        alpha_stall = 0.28
        if abs(alpha) > alpha_stall:
            excess = abs(alpha) - alpha_stall
            cl *= max(0.4, 1.0 - 1.8 * excess)
        return cl

    def _drag_coeff(self, cl):
        return self.cfg["CD0"] + self.cfg["CD_k"] * cl * cl

    # ────────────────────────────────
    def step(self, state: AircraftState, dt: float):
        cfg, env = self.cfg, self.env
        g, rho = env["g"], env["rho"]
        V = state.airspeed

        # ── on ground ──
        if state.on_ground:
            T = state.throttle * cfg["T_max"]
            D_roll = 0.03 * cfg["mass"] * g
            ax = (T - D_roll) / cfg["mass"]
            state.vx += ax * dt * math.cos(state.heading)
            state.vy += ax * dt * math.sin(state.heading)
            state.vz = 0.0
            state.alt = 0.0
            state.pitch = 0.0
            state.bank = 0.0
            state.x += state.vx * dt
            state.y += state.vy * dt
            state.time += dt
            if V >= cfg["V_rotate"]:
                state.on_ground = False
                state.pitch = 0.10
                state.vz = 1.0
            return

        # ── airborne ──
        alpha = state.pitch - state.flight_path_angle
        cl = self._lift_coeff(alpha)
        cd = self._drag_coeff(cl)
        q = 0.5 * rho * V * V * cfg["wing_area"]
        L = q * cl
        D = q * cd
        T = state.throttle * cfg["T_max"]
        gamma = state.flight_path_angle

        # horizontal acceleration magnitude
        ax_h = (T * math.cos(alpha) - D * math.cos(gamma) - L * math.sin(gamma)) / cfg["mass"]
        az = (T * math.sin(alpha) + L * math.cos(gamma) - D * math.sin(gamma)) / cfg["mass"] - g

        # apply along heading
        state.vx += ax_h * dt * math.cos(state.heading)
        state.vy += ax_h * dt * math.sin(state.heading)
        state.vz += az * dt

        # bank-induced turn
        if V > 1.0:
            turn_rate = (g / V) * math.tan(state.bank)
            state.heading += turn_rate * dt

        state.x += state.vx * dt
        state.y += state.vy * dt
        state.alt += state.vz * dt
        state.time += dt

        if state.alt <= 0.0:
            state.alt = 0.0
            state.vz = 0.0
            if state.pitch < 0.0:
                state.pitch = 0.0
            if V < cfg["V_stall"] * 0.9:
                state.on_ground = True
                state.throttle = 0.0