from __future__ import annotations

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

TITLE = "AR Fruit Ninja"

BACKGROUND_COLOR = (11, 17, 25)
PANEL_COLOR = (18, 25, 35)
TEXT_COLOR = (245, 248, 252)
MUTED_TEXT_COLOR = (162, 174, 190)
ACCENT_COLOR = (54, 210, 255)
FEVER_COLOR = (255, 211, 77)
MISS_COLOR = (255, 95, 95)
GOOD_COLOR = (120, 226, 144)
PERFECT_COLOR = (255, 240, 132)

GRAVITY = 520.0
SPAWN_LEAD_TIME = 1.6
HIT_LINE_Y_RATIO = 2 / 3
DEFAULT_BPM = 112
DEFAULT_DURATION = 90.0
MAX_MISSES = 20
HAND_LOST_PAUSE_SECONDS = 2.0
TRACKING_SAFE_MARGIN_X = 0.09
TRACKING_SAFE_MARGIN_Y = 0.10
CAMERA_GAME_LEFT = 0.08
CAMERA_GAME_TOP = 0.08
CAMERA_GAME_RIGHT = 0.92
CAMERA_GAME_BOTTOM = 0.78

CALIBRATION_MIN_SEEN = 1.0
CALIBRATION_MIN_MOVEMENT = 220.0

LEADERBOARD_PATH = "data/leaderboard.json"

DIFFICULTIES = (
    {"label": "Beginner", "speed": 0.75},
    {"label": "Easy", "speed": 0.9},
    {"label": "Normal", "speed": 1.0},
    {"label": "Hard", "speed": 1.2},
    {"label": "Master", "speed": 1.45},
)
DEFAULT_DIFFICULTY_INDEX = 2

PERFECT_WINDOW = 0.12
GOOD_WINDOW = 0.28

FEVER_DURATION = 6.0
FEVER_COOLDOWN = 8.0
FEVER_MULTIPLIER = 2

FRUIT_TYPES = (
    {
        "name": "Slate Rock",
        "color": (96, 102, 111),
        "accent": (155, 163, 174),
        "radius": 36,
    },
    {
        "name": "Moss Rock",
        "color": (84, 108, 90),
        "accent": (147, 167, 133),
        "radius": 38,
    },
    {
        "name": "Granite",
        "color": (118, 113, 109),
        "accent": (180, 174, 168),
        "radius": 40,
    },
    {
        "name": "Basalt",
        "color": (67, 72, 82),
        "accent": (129, 137, 149),
        "radius": 34,
    },
    {
        "name": "Amber Stone",
        "color": (124, 100, 69),
        "accent": (195, 165, 112),
        "radius": 42,
    },
)

PIKMIN_VARIANTS = (
    {"name": "Red", "color": (240, 74, 66)},
    {"name": "Yellow", "color": (246, 213, 72)},
    {"name": "Blue", "color": (76, 136, 242)},
    {"name": "Purple", "color": (163, 105, 224)},
    {"name": "White", "color": (238, 238, 230)},
    {"name": "Pink", "color": (255, 142, 185)},
)
