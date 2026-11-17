"""
Keyboard-driven manual control for the UAV.
Up/Down: pitch  |  Left/Right: bank  |  W/S: throttle
"""
from config import MANUAL


class ManualController:
    """Converts held keys → smooth control rates."""

    def __init__(self):
        self.pitch_cmd = 0.0
        self.bank_cmd = 0.0
        self.throttle_delta = 0.0

    def update(self, keys, dt):
        """keys: pygame key state dict. Returns (pitch, bank, throttle_delta)."""
        cfg = MANUAL

        # ── pitch (Up / Down) ──
        if keys.get("up"):
            self.pitch_cmd += cfg["pitch_rate"] * dt
        elif keys.get("down"):
            self.pitch_cmd -= cfg["pitch_rate"] * dt
        else:
            # decay to zero (stick spring-back)
            self.pitch_cmd *= (1.0 - cfg["trim_speed"] * dt)

        # ── bank (Left / Right) ──
        if keys.get("left"):
            self.bank_cmd -= cfg["bank_rate"] * dt
        elif keys.get("right"):
            self.bank_cmd += cfg["bank_rate"] * dt
        else:
            self.bank_cmd *= (1.0 - cfg["trim_speed"] * dt)

        # ── throttle (W / S) ──
        self.throttle_delta = 0.0
        if keys.get("w"):
            self.throttle_delta = cfg["throttle_rate"]
        elif keys.get("s"):
            self.throttle_delta = -cfg["throttle_rate"]

        # ── clamp ──
        self.pitch_cmd = max(-cfg["max_pitch"], min(cfg["max_pitch"], self.pitch_cmd))
        self.bank_cmd = max(-cfg["max_bank"], min(cfg["max_bank"], self.bank_cmd))

        return self.pitch_cmd, self.bank_cmd, self.throttle_delta

    def reset(self):
        self.pitch_cmd = 0.0
        self.bank_cmd = 0.0
        self.throttle_delta = 0.0