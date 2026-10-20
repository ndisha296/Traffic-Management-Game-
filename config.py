"""
Configuration module for GridLock AI
Contains color palette, window dimensions, game rules, and simulation tuning constants.
"""

# Window & Layout Settings
WINDOW_WIDTH = 1260
WINDOW_HEIGHT = 860
GRID_AREA_WIDTH = 880
GRID_AREA_HEIGHT = 860
FPS = 60

# Vehicle Masters Stylized City Aesthetics
BG_COLOR = (84, 165, 54)          # Lush stylized grass backdrop #54A536
GRASS_BASE = (92, 178, 60)        # #5CB23C Bright manicured lawn
GRASS_STRIPE = (82, 164, 52)      # Alternating lawn striping
SIDEWALK_COLOR = (232, 238, 245)  # Clean light concrete pavers
SIDEWALK_CURB = (176, 190, 205)   # Clean curb edging
SIDEWALK_WIDTH = 12

# Command Center & Mobile Glassmorphism HUD Palette
PANEL_BG = (15, 23, 42, 240)      # #0F172A Deep slate with glass alpha
CARD_BG = (30, 41, 59, 230)       # Glass card background
CARD_BORDER = (71, 85, 105)       # Card border
TEXT_PRIMARY = (255, 255, 255)    # Crisp white
TEXT_SECONDARY = (203, 213, 225) # Slate 300
TEXT_MUTED = (148, 163, 184)     # Slate 400

# Vehicle Masters Modern Road Network
ROAD_COLOR = (51, 65, 85)        # #334155 Modern smooth dark slate asphalt
ROAD_BORDER = (241, 245, 249)    # Crisp white road boundary line
LANE_MARKING = (255, 255, 255)   # Bright white dashed lane lines
INTERSECTION_BOX = (44, 56, 74)  # Clean intersection tarmac
ZEBRA_CROSSING = (255, 255, 255) # Pedestrian crosswalk stripes
STOP_LINE = (255, 255, 255)      # Stop line at signals

# Signal Colors
RED_LIGHT = (239, 68, 68)        # #EF4444 Crimson Alert
RED_LIGHT_GLOW = (239, 68, 68, 90)
YELLOW_LIGHT = (245, 158, 11)    # #F59E0B Amber Warning
YELLOW_LIGHT_GLOW = (245, 158, 11, 90)
GREEN_LIGHT = (16, 185, 129)     # #10B981 Emerald Flow
GREEN_LIGHT_GLOW = (16, 185, 129, 90)

# Vehicle Colors (Vibrant Stylized Vehicle Masters look)
CAR_COLOR = (59, 130, 246)       # #3B82F6 Electric Blue
CAR_ACCENT = (147, 197, 253)
EMERGENCY_COLOR = (236, 72, 153) # #EC4899 Neon Magenta
EMERGENCY_ACCENT = (244, 114, 182)

# Vehicle Masters Iconic Green Target Parking Bay
PARKING_BAY_GREEN = (34, 197, 94)    # #22C55E Glowing green target
PARKING_BAY_BG = (34, 197, 94, 65)
PARKING_BAY_BORDER = (74, 222, 128)  # #4ADE80
PARKING_CHEVRON = (250, 204, 21)     # Yellow guidance chevron

# Overlays & Indicators
PATH_OVERLAY = (6, 182, 212)     # #06B6D4 Cyan Glow
PATH_OVERLAY_ALPHA = 120
HEATMAP_LOW = (16, 185, 129, 85)
HEATMAP_MED = (245, 158, 11, 110)
HEATMAP_HIGH = (239, 68, 68, 140)

ACCENT_PURPLE = (168, 85, 247)
ACCENT_CYAN = (6, 182, 212)
SUCCESS_GREEN = (34, 197, 94)
DANGER_RED = (239, 68, 68)

# Stylized Buildings & 3D Architectural Facades
BUILDING_SHADOW = (20, 35, 15, 95)   # Soft ambient drop shadow on grass
BUILDING_PALETTES = [
    {"base": (248, 113, 113), "roof": (239, 68, 68), "edge": (220, 38, 38)},   # Warm Coral/Salmon
    {"base": (96, 165, 250), "roof": (59, 130, 246), "edge": (37, 99, 235)},   # Sky Blue
    {"base": (251, 191, 36), "roof": (245, 158, 11), "edge": (217, 119, 6)},   # Amber Cream
    {"base": (52, 211, 153), "roof": (16, 185, 129), "edge": (5, 150, 105)},   # Mint Green
    {"base": (192, 132, 252), "roof": (168, 85, 247), "edge": (147, 51, 234)}, # Modern Violet
    {"base": (226, 232, 240), "roof": (203, 213, 225), "edge": (148, 163, 184)} # Modern White/Slate
]
BUILDING_BASE = (226, 232, 240)
BUILDING_ROOF = (203, 213, 225)
BUILDING_EDGE = (148, 163, 184)
WINDOW_LIT_AMBER = (254, 240, 138)
WINDOW_LIT_CYAN = (186, 230, 253)
WINDOW_UNLIT = (71, 85, 105)

# Foliage & Street Trees
TREE_SHADOW = (20, 35, 15, 80)
TREE_CANOPY_DARK = (47, 133, 90)
TREE_CANOPY_LIGHT = (72, 187, 120)
TREE_TRUNK = (138, 90, 48)

# Streetlight Ambience
STREETLIGHT_POLE = (100, 116, 139)
STREETLIGHT_GLOW = (254, 240, 138, 45)
STREETLIGHT_BULB = (254, 240, 138)

# Mini-Map GPS HUD (Top-Left Bezel)
MINIMAP_X = 20
MINIMAP_Y = 65
MINIMAP_WIDTH = 195
MINIMAP_HEIGHT = 195

# Vehicle Masters Mobile Cockpit Layout
STEERING_X = 135
STEERING_Y = 730
STEERING_RADIUS = 70
STEERING_MAX_ANGLE = 55.0  # Max front wheel steering degrees

# PRND Shifter
SHIFTER_X = 1005
SHIFTER_Y = 665
SHIFTER_WIDTH = 46
SHIFTER_HEIGHT = 165

# Pedals
BRAKE_PEDAL_RECT = (1065, 715, 74, 90)
GAS_PEDAL_RECT = (1155, 680, 56, 125)

# Turn Signal Buttons
BLINKER_LEFT_RECT = (100, 625, 34, 30)
HAZARD_RECT = (142, 625, 34, 30)
BLINKER_RIGHT_RECT = (184, 625, 34, 30)

# Grid Layout
GRID_COLS = 4
GRID_ROWS = 4
CELL_WIDTH = 190
CELL_HEIGHT = 190
GRID_OFFSET_X = 155
GRID_OFFSET_Y = 145
ROAD_WIDTH = 38                  # Width of road (accommodates 2 lanes)
LANE_OFFSET = 9                  # Offset from center for right-hand traffic

# Traffic Signal Settings
BASE_GREEN_TIME = 6.0            # Seconds
MIN_GREEN_TIME = 3.0             # Seconds
MAX_GREEN_TIME = 15.0            # Seconds
YELLOW_TIME = 2.0                # Seconds
ALL_RED_TIME = 0.5               # Clearance interval
QUEUE_WEIGHT_FACTOR = 1.2        # Extra green seconds per waiting car
EMERGENCY_PREEMPTION_RADIUS = 220 # Pixels approach distance to trigger signal priority

# A* Dynamic Cost Factors
DEFAULT_K_PENALTY = 6.0          # k * queue_density in dynamic A*
BASE_SPEED_LIMIT = 70.0          # Pixels per second for standard cars
EMERGENCY_SPEED_LIMIT = 110.0    # Pixels per second for emergency cars
VEHICLE_LENGTH = 20              # Pixels
VEHICLE_WIDTH = 11               # Pixels
SAFE_DISTANCE = 14               # Pixels between vehicles in queue

# Player Car Settings (Vehicle Masters Sport Coupe)
PLAYER_COLOR = (250, 204, 21)        # #FACC15 Cyber Racing Yellow
PLAYER_ACCENT = (254, 240, 138)
PLAYER_MAX_SPEED = 145.0             # Pixels/sec
PLAYER_ACCELERATION = 260.0          # Snappy, responsive acceleration
PLAYER_BRAKE = 440.0                 # Firm, decisive braking
PLAYER_REVERSE_SPEED = 75.0          # Clean reverse speed
PLAYER_TURN_SPEED = 220.0            # Agile, precise cornering
PLAYER_COLLISION_COOLDOWN = 1.0      # Seconds between collision penalties

# Game Rules & Thresholds
CRITICAL_WAIT_LIMIT = 25.0       # Max average wait time (seconds) before crisis
GRIDLOCK_THRESHOLD = 0.75        # 75% roads congested triggers warning
AMBULANCE_TIME_LIMIT = 45.0      # Seconds to guide emergency vehicle across city
DEFAULT_SPAWN_INTERVAL = 2.0     # Seconds between car spawns
MISSION_TIME_LIMIT = 50.0        # Seconds per player delivery mission
MAX_COLLISION_PENALTY = 50       # Points deducted per crash
RED_LIGHT_PENALTY = 100          # Points deducted for running red light

