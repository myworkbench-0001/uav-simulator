"""
Aircraft parameters and mission configuration.
All units in SI (meters, seconds, kg, radians internally).
"""

# ─────────────────────────────────────────────
# AIRCRAFT PARAMETERS
# ─────────────────────────────────────────────
AIRCRAFT = {
    "mass": 2.5,
    "wing_area": 0.35,
    "CL0": 0.3,
    "CL_alpha": 5.0,
    "CD0": 0.03,
    "CD_k": 0.05,
    "T_max": 25.0,
    "V_rotate": 14.0,
    "V_stall": 11.0,
    "max_pitch": 0.35,
    "max_bank": 0.6,
}

# ─────────────────────────────────────────────
# ENVIRONMENT
# ─────────────────────────────────────────────
ENV = {
    "g": 9.81,
    "rho": 1.225,
    "dt": 0.02,
}

# ─────────────────────────────────────────────
# AUTOPILOT PID GAINS
# ─────────────────────────────────────────────
PID = {
    "altitude": {"kp": 0.08, "ki": 0.001, "kd": 0.15},
    "pitch":    {"kp": 2.5,  "ki": 0.1,   "kd": 0.5},
    "heading":  {"kp": 1.8,  "ki": 0.0,   "kd": 0.4},
    "bank":     {"kp": 3.0,  "ki": 0.0,   "kd": 0.8},
    "speed":    {"kp": 0.15, "ki": 0.01,  "kd": 0.02},
}

# ─────────────────────────────────────────────
# MISSION
# ─────────────────────────────────────────────
MISSION = {
    "start_pos":       (0.0, 0.0),
    "start_heading":   0.0,
    "cruise_altitude": 60.0,
    "cruise_speed":    18.0,
    "takeoff_alt":     30.0,
    "landing_alt":     2.0,
    "waypoint_radius": 40.0,
    "waypoints": [
        (300.0, 60.0),
        (600.0, 60.0),
        (900.0, 60.0),
        (900.0, 40.0),
        (600.0, 40.0),
        (300.0, 40.0),
    ],
    "landing_pos": (100.0, 0.0),
}

# ─────────────────────────────────────────────
# VISUALIZATION (2D legacy — kept for compatibility)
# ─────────────────────────────────────────────
VIZ = {
    "window_w": 1000,
    "window_h": 600,
    "meters_per_pixel": 2.5,
    "px_per_second": 50.0,
    "follow_camera": True,
    "ground_color": (60, 90, 60),
    "sky_color":    (135, 206, 235),
    "plane_color":  (255, 255, 255),
    "wp_color":     (255, 200, 0),
    "trail_color":  (255, 255, 255),
    "trail_max":    400,
}

# ─────────────────────────────────────────────
# MANUAL CONTROL PARAMETERS
# ─────────────────────────────────────────────
MANUAL = {
    "pitch_rate":    0.8,
    "bank_rate":     1.2,
    "throttle_rate": 0.7,
    "trim_speed":    1.0,
    "max_pitch":     0.6,
    "max_bank":      0.9,
}

# ─────────────────────────────────────────────
# 3D VIEW
# ─────────────────────────────────────────────
VIEW3D = {
    "fov":           60.0,
    "near":          1.0,
    "far":           2000.0,
    "camera_dist":   120.0,
    "camera_height": 30.0,
    "show_axes":     True,
    "axis_length":   25.0,
    "grid_size":     500.0,
    "grid_step":     50.0,
}

# ─────────────────────────────────────────────
# CAMERA MODES (NEW)
# ─────────────────────────────────────────────
CAMERA = {
    "mode": "CHASE",        # CHASE | TOPDOWN | COCKPIT
    "chase_dist":   120.0,
    "chase_height": 30.0,
    "cockpit_fov":  75.0,
    "topdown_height": 400.0,
}

# ─────────────────────────────────────────────
# SIMULATION SPEED (NEW)
# ─────────────────────────────────────────────
SPEED = {
    "levels": [1, 2, 5, 10, 20, 50],   # available speed multipliers
    "default_index": 2,                 # starts at 5x
}

# ─────────────────────────────────────────────
# WAYPOINT EDITING (NEW)
# ─────────────────────────────────────────────
WP_EDIT = {
    "default_alt": 60.0,      # altitude when user clicks to add waypoint
    "default_y":   0.0,       # default Y coordinate
    "max_count":   30,
}