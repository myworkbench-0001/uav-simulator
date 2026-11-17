"""
Entry point — autonomous + manual modes, 3D view, camera modes,
speed multiplier, waypoint editing.
"""
import sys
import math
import pygame

from config import MISSION, ENV, VIZ, MANUAL, CAMERA, SPEED, WP_EDIT
from core.physics import AircraftState, AircraftPhysics
from core.autopilot import Autopilot
from core.navigation import Navigator
from core.state_machine import StateMachine, Phase
from core.manual_control import ManualController
from core.waypoint_editor import WaypointEditor
from viz.renderer import Renderer
from viz.telemetry import TelemetryLogger

MODE_AUTOPILOT = "AUTOPILOT"
MODE_MANUAL = "MANUAL"


def main():
    # ── create all objects (renderer FIRST so attributes work) ──
    start_x, start_y = MISSION["start_pos"]
    start_alt = 0.0
    state = AircraftState(start_x, start_y, start_alt, MISSION["start_heading"])
    state.on_ground = True

    physics = AircraftPhysics()
    autopilot = Autopilot()
    navigator = Navigator(MISSION["waypoints"], MISSION["waypoint_radius"])
    sm = StateMachine(MISSION)
    manual = ManualController()

    renderer = Renderer()                       # ← FIRST
    telemetry = TelemetryLogger()

    wp_editor = WaypointEditor(navigator)
    speed_index = SPEED["default_index"]
    renderer._speed_index = speed_index         # ← now OK
    renderer.cam_mode = CAMERA["mode"]

    dt = ENV["dt"]
    speedup = VIZ["px_per_second"]
    running = True
    started = False
    mode = MODE_AUTOPILOT

    print("=" * 60)
    print(" Autonomous Fixed-Wing UAV Simulator — 3D")
    print("=" * 60)
    print(" SPACE → start mission")
    print(" M     → toggle AUTOPILOT / MANUAL mode")
    print(" C     → cycle camera: CHASE → TOPDOWN → COCKPIT")
    print(" + / - → speed multiplier up/down")
    print(" F     → add waypoint 300 m ahead")
    print(" G     → remove last waypoint")
    print(" H     → clear all waypoints")
    print(" ↑↓    → pitch (MANUAL mode)")
    print(" ←→    → bank  (MANUAL mode)")
    print(" W/S   → throttle (MANUAL mode)")
    print(" ESC   → quit")
    print("=" * 60)

    while running:
        # ── events ──
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE and not started:
                    started = True
                    state.throttle = 1.0
                    print("[main] mission started")

                elif event.key == pygame.K_m and started:
                    mode = MODE_MANUAL if mode == MODE_AUTOPILOT else MODE_AUTOPILOT
                    if mode == MODE_MANUAL:
                        manual.reset()
                        print("[main] → MANUAL mode")
                    else:
                        autopilot.reset()
                        print("[main] → AUTOPILOT mode")

                elif event.key == pygame.K_c:
                    modes = ["CHASE", "TOPDOWN", "COCKPIT"]
                    cur = renderer.cam_mode
                    nxt = modes[(modes.index(cur) + 1) % len(modes)]
                    renderer.cam_mode = nxt
                    print(f"[main] camera → {nxt}")

                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    speed_index = min(speed_index + 1, len(SPEED["levels"]) - 1)
                    renderer._speed_index = speed_index
                    print(f"[main] speed ×{SPEED['levels'][speed_index]}")

                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    speed_index = max(speed_index - 1, 0)
                    renderer._speed_index = speed_index
                    print(f"[main] speed ×{SPEED['levels'][speed_index]}")

                elif event.key == pygame.K_f:
                    if started:
                        wp_editor.add_relative(state, dx=300.0,
                                               alt=max(40.0, state.alt))
                    else:
                        print("[main] start mission first (SPACE)")

                elif event.key == pygame.K_g:
                    wp_editor.remove_last()

                elif event.key == pygame.K_h:
                    wp_editor.clear_all()

        # ── held keys ──
        keys = pygame.key.get_pressed()
        key_state = {
            "up":    keys[pygame.K_UP],
            "down":  keys[pygame.K_DOWN],
            "left":  keys[pygame.K_LEFT],
            "right": keys[pygame.K_RIGHT],
            "w":     keys[pygame.K_w],
            "s":     keys[pygame.K_s],
        }

        # ── physics loop ──
        if started:
            speed_mult = SPEED["levels"][speed_index]
            n_sub = max(1, int(speed_mult))
            sub_dt = dt

            for _ in range(n_sub):
                if mode == MODE_MANUAL:
                    pitch_cmd, bank_cmd, thr_delta = manual.update(key_state, sub_dt)
                    state.throttle += thr_delta * sub_dt
                    state.throttle = max(0.0, min(1.0, state.throttle))
                    state.pitch += (pitch_cmd - state.pitch) * 0.20
                    state.bank  += (bank_cmd  - state.bank)  * 0.20
                else:
                    target_alt = _target_altitude(sm.phase, state, navigator)
                    target_head = _target_heading(sm.phase, state, navigator)
                    target_speed = _target_speed(sm.phase)
                    pitch_cmd, bank_cmd, throttle_cmd = autopilot.update(
                        state, target_alt, target_head, target_speed, sub_dt
                    )
                    state.pitch += (pitch_cmd - state.pitch) * 0.25
                    state.bank  += (bank_cmd  - state.bank)  * 0.25
                    state.throttle += (throttle_cmd - state.throttle) * 0.10

                state.pitch = _clamp(state.pitch, -0.6, 0.5)
                state.bank  = _clamp(state.bank, -MANUAL["max_bank"], MANUAL["max_bank"])
                state.throttle = _clamp(state.throttle, 0.0, 1.0)

                physics.step(state, sub_dt)

                if mode == MODE_AUTOPILOT:
                    navigator.update(state.x, state.y)
                    sm.update(state, navigator)

                telemetry.log(state, sm.describe())

                if mode == MODE_AUTOPILOT and sm.phase == Phase.DONE:
                    print(f"[main] mission complete at t={state.time:.1f}s")
                    running = False
                    break

        # ── render ──
        try:
            renderer.render(state, navigator, navigator.waypoints,
                            sm.describe(), mode)
        except pygame.error:
            running = False
        renderer.tick(60)

    renderer.close()
    telemetry.save("flight_telemetry.png")
    print("[main] exit")


# ────────────────────────────────
def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _target_altitude(phase, state, navigator):
    if phase == Phase.TAKE_OFF:
        return MISSION["takeoff_alt"] + 5.0
    if phase == Phase.CRUISE:
        wp = navigator.current
        return wp.alt if wp else MISSION["cruise_altitude"]
    if phase == Phase.LANDING:
        land_x = MISSION["landing_pos"][0]
        dx = max(1.0, state.x - land_x)
        return max(0.0, dx * math.tan(math.radians(3.0)))
    if phase == Phase.GROUND:
        return 0.0
    return MISSION["cruise_altitude"]


def _target_heading(phase, state, navigator):
    if phase in (Phase.TAKE_OFF, Phase.LANDING, Phase.GROUND):
        return state.heading
    if phase == Phase.CRUISE:
        return navigator.bearing_to_current(state.x, state.y)
    return state.heading


def _target_speed(phase):
    if phase == Phase.TAKE_OFF:
        return 16.0
    if phase == Phase.CRUISE:
        return MISSION["cruise_speed"]
    if phase == Phase.LANDING:
        return 13.0
    return 0.0


if __name__ == "__main__":
    main()