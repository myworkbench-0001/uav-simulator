"""
PID-based autopilot for altitude, heading, and speed control.
Outputs: pitch command, bank command, throttle command.
"""
import math
from config import PID, AIRCRAFT


class PIDController:
    """Standard PID with anti-windup and output clamping."""

    def __init__(self, kp, ki, kd, out_min, out_max):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.integral = 0.0
        self.prev_error = 0.0
        self.first = True

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.first = True

    def update(self, error, dt):
        # integral
        self.integral += error * dt
        # derivative
        if self.first:
            derivative = 0.0
            self.first = False
        else:
            derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        self.prev_error = error

        out = self.kp * error + self.ki * self.integral + self.kd * derivative

        # clamp with anti-windup on integral
        if out > self.out_max:
            out = self.out_max
            self.integral -= error * dt  # undo
        elif out < self.out_min:
            out = self.out_min
            self.integral -= error * dt

        return out


class Autopilot:
    """Cascaded PID autopilot."""

    def __init__(self):
        self.alt_pid = PIDController(
            PID["altitude"]["kp"], PID["altitude"]["ki"], PID["altitude"]["kd"],
            out_min=-AIRCRAFT["max_pitch"], out_max=AIRCRAFT["max_pitch"],
        )
        self.pitch_pid = PIDController(
            PID["pitch"]["kp"], PID["pitch"]["ki"], PID["pitch"]["kd"],
            out_min=-1.0, out_max=1.0,  # normalized elevator
        )
        self.heading_pid = PIDController(
            PID["heading"]["kp"], PID["heading"]["ki"], PID["heading"]["kd"],
            out_min=-AIRCRAFT["max_bank"], out_max=AIRCRAFT["max_bank"],
        )
        self.bank_pid = PIDController(
            PID["bank"]["kp"], PID["bank"]["ki"], PID["bank"]["kd"],
            out_min=-1.0, out_max=1.0,
        )
        self.speed_pid = PIDController(
            PID["speed"]["kp"], PID["speed"]["ki"], PID["speed"]["kd"],
            out_min=0.0, out_max=1.0,
        )

    def reset(self):
        for pid in (self.alt_pid, self.pitch_pid, self.heading_pid,
                    self.bank_pid, self.speed_pid):
            pid.reset()

    # ────────────────────────────────
    # Helpers
    # ────────────────────────────────
    @staticmethod
    def _wrap_pi(a):
        while a > math.pi:
            a -= 2 * math.pi
        while a < -math.pi:
            a += 2 * math.pi
        return a

    # ────────────────────────────────
    # Main update
    # ────────────────────────────────
    def update(self, state, target_alt, target_heading, target_speed, dt):
        """Returns (pitch_cmd, bank_cmd, throttle_cmd)."""
        # ── Altitude → pitch command ──
        alt_err = target_alt - state.alt
        pitch_cmd = self.alt_pid.update(alt_err, dt)

        # ── Pitch tracking (state.pitch follows pitch_cmd) ──
        pitch_err = pitch_cmd - state.pitch
        self.pitch_pid.update(pitch_err, dt)  # elevator not used directly

        # ── Heading → bank command ──
        head_err = self._wrap_pi(target_heading - state.heading)
        bank_cmd = self.heading_pid.update(head_err, dt)

        # ── Bank tracking ──
        bank_err = bank_cmd - state.bank
        self.bank_pid.update(bank_err, dt)

        # ── Speed → throttle ──
        speed_err = target_speed - state.airspeed
        throttle_cmd = self.speed_pid.update(speed_err, dt)

        return pitch_cmd, bank_cmd, throttle_cmd