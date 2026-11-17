"""
Post-flight telemetry plots using matplotlib.
"""
import matplotlib
matplotlib.use("Agg")  # headless save
import matplotlib.pyplot as plt


class TelemetryLogger:
    def __init__(self):
        self.time = []
        self.alt = []
        self.speed = []
        self.pitch = []
        self.bank = []
        self.throttle = []
        self.phase = []

    def log(self, state, phase_name):
        self.time.append(state.time)
        self.alt.append(state.alt)
        self.speed.append(state.airspeed)
        self.pitch.append(state.pitch * 180 / 3.14159)
        self.bank.append(state.bank * 180 / 3.14159)
        self.throttle.append(state.throttle * 100)
        self.phase.append(phase_name)

    def save(self, path="flight_telemetry.png"):
        if not self.time:
            print("[telemetry] no data to plot")
            return
        fig, axes = plt.subplots(4, 1, figsize=(10, 10), sharex=True)

        axes[0].plot(self.time, self.alt, "b-", label="Altitude (m)")
        axes[0].set_ylabel("Altitude (m)")
        axes[0].grid(True)
        axes[0].legend()

        axes[1].plot(self.time, self.speed, "g-", label="Airspeed (m/s)")
        axes[1].set_ylabel("Speed (m/s)")
        axes[1].grid(True)
        axes[1].legend()

        axes[2].plot(self.time, self.pitch, "r-", label="Pitch (deg)")
        axes[2].plot(self.time, self.bank, "m-", label="Bank (deg)")
        axes[2].set_ylabel("Angle (deg)")
        axes[2].grid(True)
        axes[2].legend()

        axes[3].plot(self.time, self.throttle, "k-", label="Throttle (%)")
        axes[3].set_ylabel("Throttle (%)")
        axes[3].set_xlabel("Time (s)")
        axes[3].grid(True)
        axes[3].legend()

        fig.suptitle("UAV Flight Telemetry")
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)
        print(f"[telemetry] saved → {path}")