"""
3D perspective renderer with XYZ axis gizmo + follow camera.
"""
import math
import pygame
from config import VIZ, VIEW3D


# ─────────────────────────────────────────────
# Pygame init
# ─────────────────────────────────────────────
pygame.init()
pygame.font.init()
pygame.display.init()


def _get_font(size):
    for name in ("consolas", "couriernew", "dejavusansmono", "arial"):
        try:
            font = pygame.font.SysFont(name, size)
            if font:
                return font
        except Exception:
            continue
    return pygame.font.Font(None, size)


class Renderer:
    def __init__(self):
        # ── display ──
        self.w = VIZ["window_w"]
        self.h = VIZ["window_h"]
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption("UAV Simulator — 3D (C: camera, M: mode)")
        self.clock = pygame.time.Clock()
        self.font = _get_font(16)
        self.small = _get_font(13)

        # ── camera ──
        self.cam_pos = [0.0, 0.0, 30.0]
        self._cam_yaw = 0.0
        self.cam_pitch = math.radians(15)
        self.cam_mode = "CHASE"

        # ── trail ──
        self.trail = []
        self.trail_max = VIZ.get("trail_max", 400)

        # ── rate indicators ──
        self.prev_pitch = 0.0
        self.prev_bank = 0.0
        self.pitch_rate = 0.0
        self.bank_rate = 0.0

        # ── speed (set externally by main) ──
        self._speed_index = 2

    # ────────────────────────────────
    # 3D → 2D projection
    # ────────────────────────────────
    def _project(self, world_pt):
        cx, cy, cz = self.cam_pos
        wx, wy, wz = world_pt

        dx = wx - cx
        dy = wy - cy
        dz = wz - cz

        yaw = self._cam_yaw
        cos_y, sin_y = math.cos(-yaw), math.sin(-yaw)
        rx = dx * cos_y - dy * sin_y
        ry = dx * sin_y + dy * cos_y
        rz = dz

        pitch = self.cam_pitch
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)
        rx, rz = rx * cos_p - rz * sin_p, rx * sin_p + rz * cos_p

        if rx <= VIEW3D["near"]:
            return None

        f = (self.h / 2) / math.tan(math.radians(VIEW3D["fov"]) / 2)
        sx = self.w / 2 + (ry / rx) * f
        sy = self.h / 2 - (rz / rx) * f
        return int(sx), int(sy)

    # ────────────────────────────────
    def _update_camera(self, state):
        from config import CAMERA

        if not VIZ["follow_camera"]:
            self._cam_yaw = 0.0
            return

        mode = self.cam_mode

        if mode == "CHASE":
            dist = CAMERA["chase_dist"]
            height = CAMERA["chase_height"]
            tx = state.x - dist * math.cos(state.heading)
            ty = state.y - dist * math.sin(state.heading)
            tz = state.alt + height
            self.cam_pitch = math.radians(15)

        elif mode == "TOPDOWN":
            tx = state.x
            ty = state.y
            tz = state.alt + CAMERA["topdown_height"]
            self.cam_pitch = math.radians(80)

        elif mode == "COCKPIT":
            offset = 3.0
            tx = state.x + offset * math.cos(state.heading)
            ty = state.y + offset * math.sin(state.heading)
            tz = state.alt + 1.0
            self.cam_pitch = math.radians(-5)

        else:
            tx, ty, tz = state.x, state.y, state.alt

        alpha = 0.35 if mode == "COCKPIT" else 0.15
        self.cam_pos[0] += (tx - self.cam_pos[0]) * alpha
        self.cam_pos[1] += (ty - self.cam_pos[1]) * alpha
        self.cam_pos[2] += (tz - self.cam_pos[2]) * alpha
        self._cam_yaw = state.heading

    # ────────────────────────────────
    # MAIN RENDER
    # ────────────────────────────────
    def render(self, state, navigator, waypoints, phase_name, mode_name):
        self._update_camera(state)

        # sky + ground
        self.screen.fill(VIZ["sky_color"])
        horizon_y = int(self.h * 0.55)
        pygame.draw.rect(self.screen, VIZ["ground_color"],
                         (0, horizon_y, self.w, self.h - horizon_y))

        # ground grid
        self._draw_ground_grid(state)

        # waypoints
        for i, wp in enumerate(waypoints):
            pt = self._project((wp.x, wp.y, wp.alt))
            if pt is None:
                continue
            color = (255, 100, 100) if i == navigator.index else VIZ["wp_color"]
            pygame.draw.circle(self.screen, color, pt, 8)
            pygame.draw.circle(self.screen, color, pt, 8, 1)
            label = self.small.render(str(i), True, (255, 255, 255))
            self.screen.blit(label, (pt[0] + 10, pt[1] - 10))

        # trail (self.trail now exists)
        self.trail.append((state.x, state.y, state.alt))
        if len(self.trail) > self.trail_max:
            self.trail.pop(0)
        if len(self.trail) > 1:
            pts = [self._project(t) for t in self.trail]
            pts = [p for p in pts if p is not None]
            if len(pts) > 1:
                pygame.draw.lines(self.screen, VIZ["trail_color"], False, pts, 1)

        # aircraft + axes
        self._draw_aircraft(state)
        if VIEW3D["show_axes"]:
            self._draw_axes_gizmo(state)

        # HUD
        self._draw_hud(state, phase_name, mode_name)

        pygame.display.flip()

    # ────────────────────────────────
    def _draw_aircraft(self, state):
        pt = self._project((state.x, state.y, state.alt))
        if pt is None:
            return
        size = 12
        pitch_px = -state.pitch
        tip = (pt[0] + size * math.cos(pitch_px),
               pt[1] + size * math.sin(pitch_px))
        left = (pt[0] + 0.7 * size * math.cos(pitch_px + 2.6),
                pt[1] + 0.7 * size * math.sin(pitch_px + 2.6))
        right = (pt[0] + 0.7 * size * math.cos(pitch_px - 2.6),
                 pt[1] + 0.7 * size * math.sin(pitch_px - 2.6))
        pygame.draw.polygon(self.screen, VIZ["plane_color"], [tip, left, right])

    # ────────────────────────────────
    def _draw_axes_gizmo(self, state):
        L = VIEW3D["axis_length"]
        origin = (state.x, state.y, state.alt)
        ch, sh = math.cos(state.heading), math.sin(state.heading)
        axes = [
            ((origin[0] + L * ch, origin[1] + L * sh, origin[2]), (255, 60, 60), "X"),
            ((origin[0] - L * sh, origin[1] + L * ch, origin[2]), (60, 255, 60), "Y"),
            ((origin[0], origin[1], origin[2] + L), (60, 120, 255), "Z"),
        ]
        o_pt = self._project(origin)
        if o_pt is None:
            return
        for end, color, label in axes:
            e_pt = self._project(end)
            if e_pt is None:
                continue
            pygame.draw.line(self.screen, color, o_pt, e_pt, 2)
            txt = self.small.render(label, True, color)
            self.screen.blit(txt, (e_pt[0] + 4, e_pt[1] - 4))

    # ────────────────────────────────
    def _draw_ground_grid(self, state):
        step = VIEW3D["grid_step"]
        color = (40, 70, 40)
        base_x = math.floor(state.x / step) * step
        base_y = math.floor(state.y / step) * step
        for i in range(-4, 5):
            gx = base_x + i * step
            for j in range(-4, 5):
                gy = base_y + j * step
                p1 = self._project((gx, gy, 0))
                p2 = self._project((gx + step, gy, 0))
                p3 = self._project((gx, gy + step, 0))
                if p1 and p2:
                    pygame.draw.line(self.screen, color, p1, p2, 1)
                if p1 and p3:
                    pygame.draw.line(self.screen, color, p1, p3, 1)

    # ────────────────────────────────
    def _draw_hud(self, state, phase_name, mode_name):
        from config import SPEED

        # rates
        dt_hud = 0.05
        self.pitch_rate = (state.pitch - self.prev_pitch) / dt_hud
        self.bank_rate = (state.bank - self.prev_bank) / dt_hud
        self.prev_pitch = state.pitch
        self.prev_bank = state.bank

        try:
            speed_val = SPEED["levels"][self._speed_index]
        except Exception:
            speed_val = 1

        # ── main HUD ──
        lines = [
            f"MODE:    {mode_name}",
            f"PHASE:   {phase_name}",
            f"CAMERA:  {self.cam_mode}",
            f"SPEED×:  {speed_val}x",
            f"POS:     X={state.x:6.1f}  Y={state.y:6.1f}  Z={state.alt:6.1f}",
            f"AIRSPD:  {state.airspeed:6.1f} m/s",
            f"HEADING: {math.degrees(state.heading):7.1f}°",
            f"PITCH:   {math.degrees(state.pitch):7.1f}°  (rate {math.degrees(self.pitch_rate):+6.1f}°/s)",
            f"BANK:    {math.degrees(state.bank):7.1f}°  (rate {math.degrees(self.bank_rate):+6.1f}°/s)",
            f"THR:     {state.throttle*100:5.1f}%",
            f"T:       {state.time:6.1f}s",
        ]
        y = 10
        for line in lines:
            surf = self.font.render(line, True, (0, 0, 0))
            bg = pygame.Surface((surf.get_width() + 8, surf.get_height() + 4),
                                pygame.SRCALPHA)
            bg.fill((255, 255, 255, 200))
            self.screen.blit(bg, (8, y - 2))
            self.screen.blit(surf, (12, y))
            y += 22

        # attitude indicator
        self._draw_attitude_indicator(state)

        # control hints
        hints = [
            "CONTROLS:",
            "M  → AUTOPILOT / MANUAL",
            "C  → Camera (CHASE / TOPDOWN / COCKPIT)",
            "+/- → Speed multiplier",
            "F  → Add waypoint ahead",
            "G  → Remove last waypoint",
            "H  → Clear all waypoints",
            "↑↓ → pitch   ←→ → bank",
            "W/S → throttle",
            "SPACE → start   ESC → quit",
        ]
        y = self.h - len(hints) * 18 - 10
        for line in hints:
            surf = self.small.render(line, True, (255, 255, 255))
            bg = pygame.Surface((surf.get_width() + 8, surf.get_height() + 2),
                                pygame.SRCALPHA)
            bg.fill((0, 0, 0, 140))
            self.screen.blit(bg, (self.w - surf.get_width() - 20, y))
            self.screen.blit(surf, (self.w - surf.get_width() - 16, y + 1))
            y += 18

    # ────────────────────────────────
    def _draw_attitude_indicator(self, state):
        cx = 90
        cy = self.h - 90
        radius = 60

        pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), radius + 4)
        pygame.draw.circle(self.screen, (40, 40, 40), (cx, cy), radius)

        pitch_px = math.degrees(state.pitch) * 2
        bank_px = math.degrees(state.bank)

        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.rect(surf, (70, 130, 200), (0, 0, radius * 2, radius))
        pygame.draw.rect(surf, (140, 90, 40), (0, radius, radius * 2, radius))
        pygame.draw.line(surf, (255, 255, 255),
                         (0, radius), (radius * 2, radius), 2)

        rotated = pygame.transform.rotate(surf, bank_px)
        rect = rotated.get_rect(center=(cx, cy + int(pitch_px)))
        self.screen.blit(rotated, rect)

        pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), radius, 2)
        pygame.draw.line(self.screen, (255, 255, 0), (cx - 20, cy), (cx + 20, cy), 2)
        pygame.draw.line(self.screen, (255, 255, 0), (cx, cy - 8), (cx, cy + 8), 2)

        lbl = self.small.render("ATTITUDE", True, (255, 255, 255))
        self.screen.blit(lbl, (cx - 30, cy + radius + 8))

    # ────────────────────────────────
    def tick(self, fps=60):
        self.clock.tick(fps)

    def close(self):
        pygame.quit()