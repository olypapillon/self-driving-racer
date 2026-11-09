"""Every tunable number in one place: screen, physics, track features, AI,
colours and layout."""

import math
import sys
from pathlib import Path

from .drivers import ALGORITHMS

IN_BROWSER = sys.platform == "emscripten"
# The repository root: assets/, ghosts/ and leaderboard.json live here.
ROOT = Path(__file__).resolve().parents[2]

SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 900
# The race view sits between two side panels: controls on the left and the
# leaderboard on the right. Everything in the race view is drawn in its own
# coordinates, so SCREEN_WIDTH / SCREEN_HEIGHT stay the size of that view.
SIDE_PANEL_WIDTH = 300
WINDOW_WIDTH = SCREEN_WIDTH + 2 * SIDE_PANEL_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT
FPS = 60
FIXED_STEP = 1 / FPS

ROAD_WIDTH = 2000
SEGMENT_LENGTH = 200
RUMBLE_LENGTH = 3
LANES = 3
DRAW_DISTANCE = 500
FIELD_OF_VIEW = 100
CAMERA_HEIGHT = 1000
CAMERA_DEPTH = 1 / math.tan(math.radians(FIELD_OF_VIEW / 2))
HANDLING_REFERENCE_SPEED = 16 * SEGMENT_LENGTH
MAX_SPEED = 64 * SEGMENT_LENGTH
ACCELERATION = 16 * SEGMENT_LENGTH
BRAKE_DECELERATION = 20 * SEGMENT_LENGTH
COAST_DECELERATION = 6 * SEGMENT_LENGTH
KERB_WIDTH = 1 / 6
# Surface drag acts even while the throttle is held, so it must be stronger
# than ACCELERATION to slow the car at all.
KERB_DECELERATION = 24 * SEGMENT_LENGTH
KERB_MAX_SPEED = 0.7 * MAX_SPEED
OFF_ROAD_DECELERATION = 60 * SEGMENT_LENGTH
OFF_ROAD_MAX_SPEED = MAX_SPEED / 4
PLAYER_LATERAL_SPEED = 0.82
ROAD_CURVE_DRIFT_SPEED = 0.06
STEERING_GRIP_FALLOFF = 0.2
# How quickly sideways motion follows the wheel. The tyres slip more as speed
# rises, so the car is slower to start a slide and slower to stop one.
DRIFT_RESPONSE_SLOW = 3.2
DRIFT_RESPONSE_FAST = 0.9
# A slippery surface: a sideways push that drifts to a new random value about
# every WANDER_INTERVAL seconds, growing with speed.
WANDER_SEED = 11
WANDER_INTERVAL = 1.2
WANDER_RESPONSE = 1.5
WANDER_STRENGTH = 0.35

# Cars, in road half-widths across and world units along the track. The player
# sprite is 420 px wide where the road's half-width is about 1100 px.
CAR_WIDTH = 0.38
# Matched to what is on screen rather than to a real car: a rival this far
# ahead stands at the top edge of the player's sprite, where they look touching.
CAR_LENGTH = 560
# The player is drawn on the road at the bottom of the screen, which sits this
# far ahead of the camera.
PLAYER_Z_OFFSET = CAMERA_HEIGHT * CAMERA_DEPTH
PLAYER_MASS = 1.0
LANES_X = (-2 / 3, 0.0, 2 / 3)

RACE_LAPS = 1
COUNTDOWN_SECONDS = 3.0
GO_DISPLAY_SECONDS = 1.0
# Fast-forward runs more fixed physics steps per drawn frame, so a race at 8x
# is exactly the same race as at 1x, just shown sooner.
SIM_SPEEDS = (1, 2, 4, 8)

# The fastest finished run so far, replayed as a see-through car.
GHOST_PATH = ROOT / "ghosts" / "leader.json"
GHOST_TINT = (150, 200, 255)
GHOST_OPACITY = 110  # out of 255
GHOST_COLOR = (150, 200, 255)
# Each algorithm keeps one colour everywhere: its car, mini map dot and results.
ALGORITHM_COLORS = {
    "Baseline": (230, 230, 230),
    "Pure Pursuit": (70, 140, 255),
    "Stanley": (255, 210, 60),
    "MPC Planner": (70, 220, 120),
    "Imitation NN": (190, 110, 255),
    "Evolved NN": (255, 140, 50),
    "You": (235, 60, 60),
}
# A person at the keyboard is one more entry beside the algorithms. Picking it
# races the player's car by hand; in a battle all six algorithms race you.
HUMAN = "You"
DRIVER_CHOICES = ALGORITHMS + (HUMAN,)
# Your best times: a file on the desktop, the browser's localStorage on the web.
YOUR_BEST_PATH = ROOT / "your_best.json"
YOUR_BEST_KEY = "self-driving-racer/your-best"
RACE_MODES = ("Battle", "Time trial")
# Bump this whenever the track or physics change: ghosts from older rules are
# ignored, since replaying them would no longer be a fair comparison.
RULES_VERSION = 3

# Track features, each one lane wide. Boost pads push you past the normal top
# speed for a moment; mud slows you and takes away grip so the car slides.
BOOST_DURATION = 1.5
BOOST_MAX_SPEED = 1.35 * MAX_SPEED
BOOST_ACCELERATION = 30 * SEGMENT_LENGTH
# How quickly speed above the normal top speed bleeds away after a boost.
BOOST_FADE = 8 * SEGMENT_LENGTH
MUD_MAX_SPEED = 0.6 * MAX_SPEED
MUD_DECELERATION = 40 * SEGMENT_LENGTH
MUD_GRIP = 0.35  # steering strength and slide response are scaled by this
MUD_SLIP = 6.0  # the random sideways push is this many times stronger
FEATURE_HALF_WIDTH = 0.3  # in road half-widths; a lane is 1/3 either side
# (kind, first segment, segment count, lane centre). Lap is 1680 segments:
# per half, straight 0-40, hills 40-280, straight 280-300, bend 300-840.
TRACK_FEATURES = (
    ("boost", 20, 10, 0.0),
    ("boost", 230, 10, 2 / 3),
    ("mud", 330, 22, 0.0),
    ("mud", 560, 22, -2 / 3),
    ("boost", 870, 10, -2 / 3),
    ("boost", 1080, 10, 0.0),
    ("mud", 1190, 22, 2 / 3),
    ("mud", 1450, 26, 0.0),
)
BOOST_COLORS = ((255, 200, 40), (255, 140, 20))
MUD_COLORS = ((110, 72, 40), (92, 58, 32))
# Two cars per grid row, the front row just behind the start line.
GRID_ROW_GAP = 3 * CAR_LENGTH

RACER_SEED = 5
RACER_COUNT = 5
RACER_MIN_MASS = 0.9
RACER_MAX_MASS = 1.25
# A racer drives at this share of the speed it thinks is safe.
RACER_MIN_SKILL = 0.86
RACER_MAX_SKILL = 0.97
RACER_COLORS = (
    ("Blue", (70, 140, 255)),
    ("Yellow", (255, 210, 60)),
    ("Green", (70, 220, 120)),
    ("Purple", (190, 110, 255)),
    ("Orange", (255, 140, 50)),
)

TRAFFIC_SEED = 6
TRAFFIC_COUNT = 3
TRAFFIC_MIN_SPEED = 0.40 * MAX_SPEED
TRAFFIC_MAX_SPEED = 0.55 * MAX_SPEED
TRAFFIC_MIN_MASS = 0.7
TRAFFIC_MAX_MASS = 1.6
TRAFFIC_COLOR = (170, 170, 180)
TRAFFIC_LANE_CHANGE_INTERVAL = 5.0
TRAFFIC_LANE_RESPONSE = 1.2
TRAFFIC_SPEED_RECOVERY = 0.6
TRAFFIC_DRIFT_DAMPING = 2.5
CAR_HEAVY_DARKEN = 0.5
CAR_TINT_LIFT = 90
BUMP_BOUNCE = 0.4
BUMP_SIDE_KICK = 2.0

# The AI driver. It plans corners so that only AI_STEER_BUDGET of full steering
# is needed to hold the line, leaving the rest to fight the slippery surface.
AI_STEER_BUDGET = 0.6
# Plans its braking softer than the brakes can do, as a safety margin.
AI_BRAKING = 0.6 * BRAKE_DECELERATION
AI_BRAKE_SLACK = 0.03 * MAX_SPEED
# PD steering: sideways speed wanted per half-width away from the lane, and
# how strongly the current sideways speed is damped.
AI_STEER_P = 1.5
AI_STEER_D = 1.0
AI_MAX_CORRECTION = 0.6
# Lane choice: how far ahead the AI watches for cars, how much clear space a
# lane needs beside and behind it to move over, and how much better a lane
# must be before it bothers changing.
AI_TRAFFIC_VIEW = 25 * CAR_LENGTH
AI_MERGE_CLEARANCE = 1.5 * CAR_LENGTH
AI_LANE_SWITCH_MARGIN = 3 * CAR_LENGTH
AI_LANE_MARGIN = 0.1
# Stuck behind a car: close in to this gap, slowing in proportion to the rest.
AI_FOLLOW_GAP = 2 * CAR_LENGTH
AI_FOLLOW_GAIN = 2.0

HILL_LOW = 20
# Curves only bend the projected picture, so this scale is what gives them a
# real top-down shape. It is used both to size corners and to draw the mini map.
TURN_DEGREES_PER_CURVE = 0.2

MINIMAP_SIZE = 220
MINIMAP_MARGIN = 20
MINIMAP_PADDING = 16
MINIMAP_BACKGROUND = (18, 22, 40, 255)
MINIMAP_ROAD_COLOR = (235, 235, 235)
MINIMAP_ROAD_WIDTH = 4
MINIMAP_PLAYER_COLOR = (220, 30, 30)
MINIMAP_PLAYER_RADIUS = 6
MINIMAP_RACER_RADIUS = 5
MINIMAP_TRAFFIC_RADIUS = 3
MINIMAP_FLAG_SQUARE = 4
MINIMAP_FLAG_COLUMNS = 4

HUD_FONT_SIZE = 36
HUD_PADDING = 14
HUD_MUTED_COLOR = (170, 180, 200)
HUD_BEST_COLOR = (255, 210, 90)
COUNTDOWN_FONT_SIZE = 160
RESULTS_FONT_SIZE = 40
RESULTS_PADDING = 28

# Side panels (see draw_control_panel and draw_leaderboard_panel).
LEADERBOARD_PATH = ROOT / "leaderboard.json"
PANEL_BACKGROUND = (12, 14, 28)
PANEL_MARGIN = 20
PANEL_TITLE_FONT_SIZE = 34
PANEL_FONT_SIZE = 27
PANEL_SMALL_FONT_SIZE = 21
BUTTON_HEIGHT = 42
BUTTON_GAP = 8
BUTTON_COLOR = (30, 36, 62)
BUTTON_HOVER_COLOR = (46, 54, 92)
BUTTON_SELECTED_COLOR = (62, 72, 118)
BUTTON_DISABLED_TEXT = (90, 96, 120)

# Tree placement is measured in road half-widths: the road edge is 1, so 1.4
# keeps a tree's trunk clear of the rumble strip.
TREE_SEED = 7
TREE_SPACING = 5
TREE_CHANCE = 0.55
TREE_MIN_OFFSET = 1.4
TREE_MAX_OFFSET = 3.6
TREE_MIN_SIZE = 0.8
TREE_MAX_SIZE = 1.3
TREE_WIDTH = 0.4
TREE_IMAGE_SIZE = (160, 256)
TREE_TRUNK_COLOR = (92, 60, 38)
TREE_CROWN_COLORS = ((22, 82, 44), (30, 102, 54), (40, 122, 64))
# Trees shorter than this near the horizon are a speck; skipping them is free.
MIN_TREE_PIXELS = 2

SKY_WIDTH = SCREEN_WIDTH * 2
SKY_HEIGHT = 560
SKY_TOP_COLOR = (30, 48, 120)
SKY_HORIZON_COLOR = (255, 170, 110)
SKY_GRADIENT_BIAS = 1.7
SUN_COLOR = (255, 232, 140)
SUN_RADIUS = 110
SUN_HEIGHT_ABOVE_HORIZON = 40
SUN_GLOW_STEPS = 28
SUN_GLOW_EXTENT = 3.2
SUN_SUPERSAMPLE = 2
SKY_PARALLAX_SPEED = 0.0025

PLAYER_CAR_WIDTH = 420
PLAYER_CAR_HEIGHT = 200
PLAYER_CAR_BOTTOM_MARGIN = -20
CAR_SHADOW_HEIGHT = 48
CAR_SHADOW_VERTICAL_POSITION = 0.84
PLAYER_CAR_SWAY = 32
STEERING_ANIMATION_RESPONSE = 12
STEERING_SPRITE_THRESHOLD = 0.22
