import math
import random
from dataclasses import dataclass
from pathlib import Path

import pygame


SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 900
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

RACE_LAPS = 3
COUNTDOWN_SECONDS = 3.0
GO_DISPLAY_SECONDS = 1.0
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


def ease_in(start, end, percent):
    return start + (end - start) * percent**2


def ease_in_out(start, end, percent):
    return start + (end - start) * (-math.cos(percent * math.pi) / 2 + 0.5)


def last_elevation(track):
    """The world height the track has reached so far."""
    return track[-1][1] if track else 0.0


def add_road(track, enter, hold, leave, curve, hill):
    """Ease a curve in and out while easing the road up or down to a new height.

    Each appended segment is ``(curve, elevation)``, where ``elevation`` is the
    world height of the segment's far end -- hence the ``index + 1`` in the
    height easing, which also lands the last segment exactly on ``end_y``.
    Curves ease over their own enter and leave phases; the height eases across
    the whole stretch instead, so a bend and a climb can overlap without either
    one stepping.
    """
    start_y = last_elevation(track)
    end_y = start_y + hill * SEGMENT_LENGTH
    total = enter + hold + leave

    for index in range(enter):
        track.append(
            (
                ease_in(0.0, curve, index / enter),
                ease_in_out(start_y, end_y, (index + 1) / total),
            )
        )
    for index in range(hold):
        track.append((curve, ease_in_out(start_y, end_y, (enter + index + 1) / total)))
    for index in range(leave):
        track.append(
            (
                ease_in_out(curve, 0.0, index / leave),
                ease_in_out(start_y, end_y, (enter + hold + index + 1) / total),
            )
        )


def add_straight(track, length):
    add_road(track, 0, length, 0, 0.0, 0.0)


def add_hill(track, length, hill):
    """A straight stretch that climbs (or drops) to a new height and holds it."""
    add_road(track, length, length, length, 0.0, hill)


def add_corner(track, enter, hold, leave, angle):
    """A flat bend that turns exactly ``angle`` degrees (positive is right).

    ``add_road`` eases the curve in and out, so each phase contributes a
    different share of the turn. Summing those shares with the same easing
    functions gives the curve value that makes the whole bend hit the angle.
    """
    enter_share = sum(ease_in(0.0, 1.0, index / enter) for index in range(enter))
    leave_share = sum(ease_in_out(1.0, 0.0, index / leave) for index in range(leave))
    curve = angle / TURN_DEGREES_PER_CURVE / (enter_share + hold + leave_share)
    add_road(track, enter, hold, leave, curve, 0.0)


def add_half_lap(track):
    """A hilly straight and a 180-degree bend that ends back at height zero."""
    add_straight(track, 60)
    add_hill(track, 40, HILL_LOW)
    add_hill(track, 40, -HILL_LOW)
    add_straight(track, 30)
    add_hill(track, 45, HILL_LOW)
    add_hill(track, 45, -HILL_LOW)
    add_corner(track, 60, 420, 60, 180)


def build_track():
    """An oval made of two identical halves.

    Each half turns 180 degrees, so the second half retraces the first one
    rotated half a turn and the lap always ends exactly where it started.
    """
    track = []
    add_half_lap(track)
    add_half_lap(track)
    return track


def build_trees(track):
    """Scatter trees along both roadsides, the same way every run.

    Returns one list per segment, each holding ``(offset, size)`` pairs, so the
    renderer can look up a segment's trees directly by its index.
    """
    rng = random.Random(TREE_SEED)
    trees = [[] for _ in track]
    for segment_index in range(0, len(track), TREE_SPACING):
        for side in (-1, 1):
            if rng.random() < TREE_CHANCE:
                offset = side * rng.uniform(TREE_MIN_OFFSET, TREE_MAX_OFFSET)
                size = rng.uniform(TREE_MIN_SIZE, TREE_MAX_SIZE)
                trees[segment_index].append((offset, size))
    return trees


def build_tree_image():
    """Draw one pine tree at startup; every tree on the road is a scaled copy."""
    width, height = TREE_IMAGE_SIZE
    tree = pygame.Surface(TREE_IMAGE_SIZE, pygame.SRCALPHA)
    trunk_width = width // 7
    trunk_height = height // 5
    pygame.draw.rect(
        tree,
        TREE_TRUNK_COLOR,
        (width / 2 - trunk_width / 2, height - trunk_height, trunk_width, trunk_height),
    )

    # Three stacked triangles, each narrower and lighter than the one below.
    crown_bottom = height - trunk_height * 0.6
    layer_height = crown_bottom / 2.2
    for layer, color in enumerate(TREE_CROWN_COLORS):
        base_y = crown_bottom - layer * layer_height * 0.6
        half = width / 2 * (1 - layer * 0.22)
        pygame.draw.polygon(
            tree,
            color,
            [
                (width / 2 - half, base_y),
                (width / 2 + half, base_y),
                (width / 2, base_y - layer_height),
            ],
        )
    return tree.convert_alpha()


def track_path(track):
    """Walk the track from above: the 2D point at the start of every segment.

    The list has one extra point, the end of the lap, so segment ``i`` runs
    from ``points[i]`` to ``points[i + 1]``.
    """
    heading = math.pi / 2
    x = y = 0.0
    points = [(x, y)]
    for curve, _ in track:
        heading += math.radians(curve * TURN_DEGREES_PER_CURVE)
        x += math.sin(heading)
        y -= math.cos(heading)
        points.append((x, y))
    return points


def build_minimap(track):
    """Pre-render the track outline once and return it with its scaled path."""
    points = track_path(track)
    min_x = min(x for x, _ in points)
    min_y = min(y for _, y in points)
    span = max(
        max(x for x, _ in points) - min_x,
        max(y for _, y in points) - min_y,
    )
    scale = (MINIMAP_SIZE - 2 * MINIMAP_PADDING) / span
    # Center the shorter axis inside the square box.
    offset_x = (MINIMAP_SIZE - (max(x for x, _ in points) - min_x) * scale) / 2
    offset_y = (MINIMAP_SIZE - (max(y for _, y in points) - min_y) * scale) / 2
    path = [
        (offset_x + (x - min_x) * scale, offset_y + (y - min_y) * scale)
        for x, y in points
    ]

    minimap = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(
        minimap,
        MINIMAP_BACKGROUND,
        minimap.get_rect(),
        border_radius=MINIMAP_PADDING,
    )
    pygame.draw.lines(minimap, MINIMAP_ROAD_COLOR, True, path, MINIMAP_ROAD_WIDTH)
    draw_start_finish(minimap, path)
    return minimap, path


def draw_start_finish(minimap, path):
    """A checkered strip across the road where the lap starts and ends."""
    start_x, start_y = path[0]
    next_x, next_y = path[1]
    length = math.hypot(next_x - start_x, next_y - start_y)
    along = ((next_x - start_x) / length, (next_y - start_y) / length)
    across = (-along[1], along[0])
    size = MINIMAP_FLAG_SQUARE

    for row in range(2):
        for column in range(MINIMAP_FLAG_COLUMNS):
            # Offsets in squares from the start point: centered across the road.
            a = row - 1
            b = column - MINIMAP_FLAG_COLUMNS / 2
            corners = [
                (
                    start_x + (along[0] * (a + da) + across[0] * (b + db)) * size,
                    start_y + (along[1] * (a + da) + across[1] * (b + db)) * size,
                )
                for da, db in ((0, 0), (1, 0), (1, 1), (0, 1))
            ]
            color = "white" if (row + column) % 2 else "black"
            pygame.draw.polygon(minimap, color, corners)


def format_lap_time(seconds):
    if seconds is None:
        return "--:--.--"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}:{seconds:05.2f}"


def draw_hud(screen, font, race):
    """Race position, lap count and times in a panel opposite the mini map."""
    player = race.player
    order = standings(race)
    lap_number = max(1, min(player.laps + 1, RACE_LAPS))
    if player.lap_start is None or player.finish_time is not None:
        lap_time = 0.0
    else:
        lap_time = race.clock - player.lap_start
    lines = [
        (f"Pos  {order.index(player) + 1}/{len(order)}", "white"),
        (f"Lap  {lap_number}/{RACE_LAPS}", "white"),
        (f"Time {format_lap_time(lap_time)}", "white"),
        (f"Last {format_lap_time(player.last_lap)}", HUD_MUTED_COLOR),
        (f"Best {format_lap_time(player.best_lap)}", HUD_BEST_COLOR),
    ]
    rendered = [font.render(text, True, color) for text, color in lines]
    line_height = font.get_linesize()
    width = max(text.get_width() for text in rendered) + 2 * HUD_PADDING
    height = line_height * len(rendered) + 2 * HUD_PADDING

    panel = pygame.Rect(MINIMAP_MARGIN, MINIMAP_MARGIN, width, height)
    pygame.draw.rect(screen, MINIMAP_BACKGROUND, panel, border_radius=HUD_PADDING)
    for index, text in enumerate(rendered):
        screen.blit(
            text,
            (panel.left + HUD_PADDING, panel.top + HUD_PADDING + index * line_height),
        )


def minimap_point(path, left, top, z):
    """Where track distance ``z`` falls on the mini map, between stored points."""
    segment_position = z / SEGMENT_LENGTH
    index = int(segment_position) % (len(path) - 1)
    percent = segment_position % 1
    (near_x, near_y), (far_x, far_y) = path[index], path[index + 1]
    return (
        left + near_x + (far_x - near_x) * percent,
        top + near_y + (far_y - near_y) * percent,
    )


def draw_minimap(screen, minimap, path, race, track_length):
    left = SCREEN_WIDTH - MINIMAP_SIZE - MINIMAP_MARGIN
    top = MINIMAP_MARGIN
    screen.blit(minimap, (left, top))

    # Traffic first, so racer dots sit on top of it.
    for car in sorted(race.cars, key=lambda car: car.driver != "traffic"):
        if car is race.player:
            continue
        radius = (
            MINIMAP_TRAFFIC_RADIUS if car.driver == "traffic" else MINIMAP_RACER_RADIUS
        )
        pygame.draw.circle(
            screen,
            car.color,
            minimap_point(path, left, top, car.distance % track_length),
            radius,
        )
    player = minimap_point(path, left, top, race.player.distance % track_length)
    pygame.draw.circle(screen, "white", player, MINIMAP_PLAYER_RADIUS + 2)
    pygame.draw.circle(screen, MINIMAP_PLAYER_COLOR, player, MINIMAP_PLAYER_RADIUS)


def road_curve_at(track, position):
    """Return a smoothly interpolated curve value at the camera position."""
    segment_position = position / SEGMENT_LENGTH
    segment_index = int(segment_position) % len(track)
    next_index = (segment_index + 1) % len(track)
    segment_percent = segment_position % 1
    near_curve = track[segment_index][0]
    far_curve = track[next_index][0]
    return near_curve + (far_curve - near_curve) * segment_percent


def road_elevation_at(track, position):
    """Interpolate the road's world height under the camera.

    A segment stores the height of its far end, so the near end is the previous
    segment's stored height.
    """
    segment_position = position / SEGMENT_LENGTH
    segment_index = int(segment_position) % len(track)
    segment_percent = segment_position % 1
    near_y = track[(segment_index - 1) % len(track)][1]
    far_y = track[segment_index][1]
    return near_y + (far_y - near_y) * segment_percent


def surface_drag(player_x):
    """Extra deceleration and the speed it pulls down to, by road zone.

    ``player_x`` is in road half-widths: the asphalt ends at 1 and the kerb
    runs to ``1 + KERB_WIDTH``. Beyond that is grass.
    """
    distance = abs(player_x)
    if distance <= 1:
        return 0.0, MAX_SPEED
    if distance <= 1 + KERB_WIDTH:
        return KERB_DECELERATION, KERB_MAX_SPEED
    return OFF_ROAD_DECELERATION, OFF_ROAD_MAX_SPEED


def move_speed(speed, throttle, brake, player_x, dt):
    """Accelerate or brake while keeping forward speed within its limits.

    Kerb and grass drag only pull speed down to their limit, so the throttle
    can still crawl the car back onto the road.
    """
    if throttle:
        speed += ACCELERATION * dt
    else:
        speed -= COAST_DECELERATION * dt
    speed -= brake * BRAKE_DECELERATION * dt

    drag, limit = surface_drag(player_x)
    if speed > limit:
        speed = max(limit, speed - drag * dt)
    return max(0.0, min(speed, MAX_SPEED))


def update_wander(wander, wander_target, rng, dt):
    """Ease the slippery push toward a target that changes now and then.

    Easing, rather than jumping, keeps the car drifting in smooth arcs.
    """
    if rng.random() < dt / WANDER_INTERVAL:
        wander_target = rng.uniform(-1.0, 1.0)
    wander += (wander_target - wander) * min(1.0, WANDER_RESPONSE * dt)
    return wander, wander_target


def move_sideways(player_x, drift_speed, steering, road_curve, speed, wander, dt):
    """Move a car relative to the road while preserving a straight world heading.

    The player and the AI racers both drive through this, so they face exactly
    the same handling.

    Three effects fight the driver. Steering grows sharper with speed, so a
    tap at the top end moves the car a long way. Cornering load grows with the
    square of speed, the way real centrifugal force does. And the car carries
    sideways momentum: ``drift_speed`` chases the wheel instead of matching it,
    and chases it more lazily as speed rises, so a fast car is late into a
    slide and keeps sliding after the key is released.
    """
    speed_ratio = speed / HANDLING_REFERENCE_SPEED
    speed_fraction = speed / MAX_SPEED
    grip = 1.0 - STEERING_GRIP_FALLOFF * speed_fraction
    target_speed = steering * PLAYER_LATERAL_SPEED * speed_ratio * grip
    response = DRIFT_RESPONSE_SLOW + (
        DRIFT_RESPONSE_FAST - DRIFT_RESPONSE_SLOW
    ) * speed_fraction
    drift_speed += (target_speed - drift_speed) * min(1.0, response * dt)
    # The surface pushes the slide too, so the car wanders even on a straight.
    drift_speed += wander * WANDER_STRENGTH * speed_fraction * dt
    road_turn_speed = road_curve * ROAD_CURVE_DRIFT_SPEED * speed_ratio**2
    return player_x + (drift_speed - road_turn_speed) * dt, drift_speed


@dataclass
class Car:
    """Anything driving on the track: the player, an AI racer, or slow traffic.

    ``distance`` is how far the car has driven from the start line and is never
    wrapped, so ``distance // track_length`` counts its finished laps and the
    grid can start at a negative distance, just behind the line.
    """

    name: str
    driver: str  # "player", "racer" or "traffic"
    distance: float
    x: float
    mass: float
    size: float
    color: tuple
    image: pygame.Surface
    rng: random.Random
    speed: float = 0.0
    drift_speed: float = 0.0
    target_x: float = 0.0
    steering: float = 0.0
    skill: float = 1.0
    cruise_speed: float = 0.0
    wander: float = 0.0
    wander_target: float = 0.0
    # Lap bookkeeping, timed on the race clock. ``laps`` is -1 on the grid.
    laps: int = -1
    lap_start: float | None = None
    last_lap: float | None = None
    best_lap: float | None = None
    finish_time: float | None = None


@dataclass
class Race:
    cars: list
    player: Car
    speed_plan: tuple
    countdown: float = COUNTDOWN_SECONDS
    clock: float = 0.0


def build_car_image(car_image, color, mass):
    """Repaint the player's car: heavier cars come out darker."""
    heaviness = (mass - TRAFFIC_MIN_MASS) / (TRAFFIC_MAX_MASS - TRAFFIC_MIN_MASS)
    shade = 1.0 - CAR_HEAVY_DARKEN * heaviness
    image = pygame.transform.grayscale(car_image)
    # Lift the greys before tinting, or the red body turns out nearly black.
    image.fill((CAR_TINT_LIFT,) * 3, special_flags=pygame.BLEND_RGB_ADD)
    image.fill(
        [round(channel * shade) for channel in color],
        special_flags=pygame.BLEND_RGB_MULT,
    )
    return image


def build_race(car_image, track):
    """A fresh race: the player and the racers on the grid, traffic spread out.

    The player is first in ``cars``. Bumps only ever move the second car of a
    pair, so the camera car is never teleported.
    """
    track_length = len(track) * SEGMENT_LENGTH
    rng = random.Random(RACER_SEED)
    player = Car(
        name="You",
        driver="player",
        distance=0.0,
        x=0.0,
        mass=PLAYER_MASS,
        size=1.0,
        color=MINIMAP_PLAYER_COLOR,
        image=car_image,
        rng=random.Random(WANDER_SEED),
    )
    racers = []
    for index, (name, color) in enumerate(RACER_COLORS[:RACER_COUNT]):
        mass = rng.uniform(RACER_MIN_MASS, RACER_MAX_MASS)
        racers.append(
            Car(
                name=name,
                driver="racer",
                distance=0.0,
                x=0.0,
                mass=mass,
                size=mass ** (1 / 3),
                color=color,
                image=build_car_image(car_image, color, mass),
                rng=random.Random(WANDER_SEED + 1 + index),
                skill=rng.uniform(RACER_MIN_SKILL, RACER_MAX_SKILL),
            )
        )

    # Fill the grid two by two from the front; the player starts last.
    grid = racers + [player]
    for slot, car in enumerate(grid):
        car.distance = -CAR_LENGTH - (slot // 2) * GRID_ROW_GAP
        car.x = car.target_x = LANES_X[0] if slot % 2 else LANES_X[2]

    rng = random.Random(TRAFFIC_SEED)
    traffic = []
    for index in range(TRAFFIC_COUNT):
        mass = rng.uniform(TRAFFIC_MIN_MASS, TRAFFIC_MAX_MASS)
        speed = rng.uniform(TRAFFIC_MIN_SPEED, TRAFFIC_MAX_SPEED)
        lane = rng.choice(LANES_X)
        traffic.append(
            Car(
                name="Traffic",
                driver="traffic",
                distance=track_length * (index + 1) / (TRAFFIC_COUNT + 1),
                x=lane,
                target_x=lane,
                mass=mass,
                # Bigger with mass, but gently: a cube root keeps 1.6x mass
                # about 1.2x wider rather than 1.6x.
                size=mass ** (1 / 3),
                color=TRAFFIC_COLOR,
                image=build_car_image(car_image, TRAFFIC_COLOR, mass),
                rng=rng,
                speed=speed,
                cruise_speed=speed,
            )
        )
    return Race(
        cars=[player] + racers + traffic,
        player=player,
        speed_plan=build_speed_plan(track),
    )


def track_gap(from_distance, to_distance, track_length):
    """Shortest signed distance around the loop, positive when ``to`` is ahead."""
    gap = to_distance - from_distance
    return (gap + track_length / 2) % track_length - track_length / 2


def corner_speed(curve):
    """The fastest speed at which AI_STEER_BUDGET of the wheel holds a bend.

    The corner push grows with speed squared, but steering only grows with
    speed (and loses grip), so above some speed the push always wins:

        curve * ROAD_CURVE_DRIFT_SPEED * r**2
            = AI_STEER_BUDGET * PLAYER_LATERAL_SPEED * r * grip(r)

    where ``r`` is speed / HANDLING_REFERENCE_SPEED. Solving for ``r`` gives
    the line below.
    """
    k = AI_STEER_BUDGET * PLAYER_LATERAL_SPEED / (curve * ROAD_CURVE_DRIFT_SPEED)
    ratio = k / (1 + k * STEERING_GRIP_FALLOFF * HANDLING_REFERENCE_SPEED / MAX_SPEED)
    return ratio * HANDLING_REFERENCE_SPEED


def build_speed_plan(track):
    """The fastest speed entering each segment that still makes every bend after it.

    A bend's safe speed ``v`` allows ``sqrt(v**2 + 2 * a * distance)`` any
    distance before it, from the braking equation. Walking the lap backwards
    applies that to every bend at once, so the AI only has to look up the
    segment it is on. Going round twice lets the bend at the end of the lap
    reach back over the start line.
    """
    limits = [
        min(MAX_SPEED, corner_speed(abs(curve))) if curve else MAX_SPEED
        for curve, _ in track
    ]
    plan = limits[:]
    for step in reversed(range(2 * len(track))):
        index = step % len(track)
        brake_for_next = math.sqrt(
            plan[(index + 1) % len(track)] ** 2 + 2 * AI_BRAKING * SEGMENT_LENGTH
        )
        plan[index] = min(limits[index], brake_for_next)
    return limits, plan


def planned_speed(speed_plan, z):
    """The planned speed at ``z``, part-way through a segment."""
    limits, plan = speed_plan
    segment = int(z // SEGMENT_LENGTH)
    to_next = (segment + 1) * SEGMENT_LENGTH - z
    next_speed = plan[(segment + 1) % len(plan)]
    braking = math.sqrt(next_speed**2 + 2 * AI_BRAKING * to_next)
    return min(limits[segment % len(limits)], braking)


def free_road(car, cars, lane_x, clearance, track_length):
    """How clear ``lane_x`` is ahead of ``car``, and the car in the way.

    ``clearance`` also counts cars this far behind as in the way: moving into
    another lane needs space beside us as well as in front.
    """
    nearest, blocker = AI_TRAFFIC_VIEW, None
    for other in cars:
        if other is car:
            continue
        gap = track_gap(car.distance, other.distance, track_length)
        reach = CAR_WIDTH * (car.size + other.size) / 2 + AI_LANE_MARGIN
        if -clearance < gap < nearest and abs(other.x - lane_x) < reach:
            nearest, blocker = max(0.0, gap), other
    return nearest, blocker


def ai_driver(car, race, track, track_length):
    """Decide steering, throttle and brake, the same three values a player gives.

    Pick the clearest lane, aim for the fastest speed that still makes the bends
    ahead, and steer with a PD controller toward the lane.
    """
    # Lane: stay put unless a car blocks the way and another lane is clearly
    # better. Ignoring small gains stops the car weaving between lanes.
    cars = race.cars
    free, blocker = free_road(car, cars, car.target_x, 0.0, track_length)
    if blocker is not None:
        for lane_x in LANES_X:
            if lane_x == car.target_x:
                continue
            lane_free, _ = free_road(
                car, cars, lane_x, AI_MERGE_CLEARANCE, track_length
            )
            if lane_free > free + AI_LANE_SWITCH_MARGIN:
                free, car.target_x = lane_free, lane_x
        free, blocker = free_road(car, cars, car.target_x, 0.0, track_length)

    # Speed.
    z = car.distance % track_length
    target_speed = car.skill * planned_speed(race.speed_plan, z)
    if blocker is not None:
        follow_speed = blocker.speed + AI_FOLLOW_GAIN * (free - AI_FOLLOW_GAP)
        target_speed = min(target_speed, max(0.0, follow_speed))
    throttle = brake = 0
    if car.speed < target_speed:
        throttle = 1
    elif car.speed > target_speed + AI_BRAKE_SLACK:
        brake = min(1.0, (car.speed - target_speed) / AI_BRAKE_SLACK - 1)

    # Steering. These mirror the terms in move_sideways.
    speed_ratio = car.speed / HANDLING_REFERENCE_SPEED
    grip = 1.0 - STEERING_GRIP_FALLOFF * car.speed / MAX_SPEED
    wheel_strength = PLAYER_LATERAL_SPEED * speed_ratio * grip
    if wheel_strength <= 0:
        return 0.0, throttle, brake
    push = ROAD_CURVE_DRIFT_SPEED * speed_ratio**2
    road_turn = road_curve_at(track, z) * push
    sideways_speed = car.drift_speed - road_turn
    # P: head toward the lane. D: oppose the sideways speed already there.
    correction = AI_STEER_P * (car.target_x - car.x) - AI_STEER_D * sideways_speed
    correction = max(-AI_MAX_CORRECTION, min(AI_MAX_CORRECTION, correction))
    # The slide takes about 1 / response seconds to follow the wheel, so lean
    # against the push the bend will have by then, not the push it has now.
    response = DRIFT_RESPONSE_SLOW + (
        DRIFT_RESPONSE_FAST - DRIFT_RESPONSE_SLOW
    ) * car.speed / MAX_SPEED
    lead_z = (z + car.speed / response) % track_length
    steering = (road_curve_at(track, lead_z) * push + correction) / wheel_strength
    return max(-1.0, min(1.0, steering)), throttle, brake


def drive(car, track, track_length, steering, throttle, brake, dt):
    """Move a player or racer with the shared vehicle physics."""
    car.steering = steering
    car.speed = move_speed(car.speed, throttle, brake, car.x, dt)
    car.distance += car.speed * dt
    car.wander, car.wander_target = update_wander(
        car.wander, car.wander_target, car.rng, dt
    )
    car.x, car.drift_speed = move_sideways(
        car.x,
        car.drift_speed,
        steering,
        road_curve_at(track, car.distance % track_length),
        car.speed,
        car.wander,
        dt,
    )


def drive_traffic(car, dt):
    """Cruise forward, glide toward the chosen lane, and settle after bumps."""
    car.speed += (car.cruise_speed - car.speed) * min(
        1.0, TRAFFIC_SPEED_RECOVERY * dt
    )
    car.distance += car.speed * dt
    if car.rng.random() < dt / TRAFFIC_LANE_CHANGE_INTERVAL:
        car.target_x = car.rng.choice(LANES_X)
    car.drift_speed -= car.drift_speed * min(1.0, TRAFFIC_DRIFT_DAMPING * dt)
    car.x += (car.target_x - car.x) * min(
        1.0, TRAFFIC_LANE_RESPONSE * dt
    ) + car.drift_speed * dt


def count_laps(race, car, track_length):
    """Time a lap each time the car first reaches a new lap.

    Taking the furthest lap reached means a bump that knocks a car back over
    the line cannot count the same lap twice.
    """
    laps = int(car.distance // track_length)
    if laps <= car.laps:
        return
    car.laps = laps
    if car.lap_start is not None:
        lap = race.clock - car.lap_start
        car.last_lap = lap
        car.best_lap = lap if car.best_lap is None else min(car.best_lap, lap)
    car.lap_start = race.clock
    if laps >= RACE_LAPS and car.finish_time is None:
        car.finish_time = race.clock


def standings(race):
    """Player and racers in race order: finishers by time, then by distance."""
    return sorted(
        (car for car in race.cars if car.driver != "traffic"),
        key=lambda car: (
            car.finish_time is None,
            car.finish_time or 0.0,
            -car.distance,
        ),
    )


def collide(speed_a, speed_b, mass_a, mass_b):
    """New speeds after two bodies meet in a line.

    Each body's change is set by the *other* body's share of the total mass, so
    the heavier one is pushed less. BUMP_BOUNCE runs from 0 (they stick) to 1
    (a perfect rebound).
    """
    closing = speed_a - speed_b
    total = mass_a + mass_b
    return (
        speed_a - (1 + BUMP_BOUNCE) * mass_b / total * closing,
        speed_b + (1 + BUMP_BOUNCE) * mass_a / total * closing,
    )


def bump(a, b, track_length):
    """Resolve contact between two cars; only ``b`` is moved apart."""
    gap_z = track_gap(a.distance, b.distance, track_length)
    gap_x = b.x - a.x
    reach_x = CAR_WIDTH * (a.size + b.size) / 2
    if abs(gap_z) >= CAR_LENGTH or abs(gap_x) >= reach_x:
        return

    # Along the track: only resolve if the cars are closing on each other.
    ahead = 1 if gap_z >= 0 else -1
    if (a.speed - b.speed) * ahead > 0:
        closing = abs(a.speed - b.speed)
        a.speed, b.speed = collide(a.speed, b.speed, a.mass, b.mass)
        a.speed, b.speed = max(0.0, a.speed), max(0.0, b.speed)
        # An off-centre hit also shoves both cars sideways.
        side = 1 if gap_x >= 0 else -1
        kick = BUMP_SIDE_KICK * closing / MAX_SPEED
        total = a.mass + b.mass
        a.drift_speed -= side * kick * b.mass / total
        b.drift_speed += side * kick * a.mass / total
        # Move b just out of contact so one hit is not counted twice.
        b.distance += ahead * CAR_LENGTH - gap_z
    elif (CAR_LENGTH - abs(gap_z)) / CAR_LENGTH < (reach_x - abs(gap_x)) / reach_x:
        # Already pulling apart along the track and barely overlapping that
        # way: just finish separating them.
        b.distance += ahead * CAR_LENGTH - gap_z
    else:
        # Side by side: resolve the sideways speeds the same way.
        side = 1 if gap_x >= 0 else -1
        if (a.drift_speed - b.drift_speed) * side > 0:
            a.drift_speed, b.drift_speed = collide(
                a.drift_speed, b.drift_speed, a.mass, b.mass
            )
        b.x = a.x + side * reach_x


def bump_cars(cars, track_length):
    for index, a in enumerate(cars):
        for b in cars[index + 1 :]:
            bump(a, b, track_length)


def update_race(race, track, track_length, controls, dt):
    """One fixed physics step. ``controls`` is the keyboard's (steer, throttle, brake).

    Once the player finishes, the AI takes over their car for the lap of honour.
    """
    if race.countdown > 0:
        race.countdown -= dt
        return
    race.clock += dt
    for car in race.cars:
        if car.driver == "traffic":
            drive_traffic(car, dt)
            continue
        if car is race.player and car.finish_time is None:
            steering, throttle, brake = controls
        else:
            steering, throttle, brake = ai_driver(car, race, track, track_length)
        drive(car, track, track_length, steering, throttle, brake, dt)
        count_laps(race, car, track_length)
    bump_cars(race.cars, track_length)


def project_point(camera_x, camera_y, camera_z):
    """Project a point already expressed in camera space onto the screen."""
    if camera_z <= CAMERA_DEPTH:
        return None

    scale = CAMERA_DEPTH / camera_z
    screen_x = SCREEN_WIDTH / 2 - scale * camera_x * SCREEN_WIDTH / 2
    screen_y = SCREEN_HEIGHT / 2 - scale * camera_y * SCREEN_HEIGHT / 2
    screen_width = scale * ROAD_WIDTH * SCREEN_WIDTH / 2
    return screen_x, screen_y, screen_width


def projected_road(track, position, player_x, camera_y):
    """Project visible segments using Jake Gordon's x/dx curve accumulation."""
    segment_count = len(track)
    track_length = segment_count * SEGMENT_LENGTH
    base_index = int(position / SEGMENT_LENGTH) % segment_count
    base_percent = (position % SEGMENT_LENGTH) / SEGMENT_LENGTH
    curve_offset = 0.0
    curve_velocity = -(track[base_index][0] * base_percent)
    max_y = SCREEN_HEIGHT
    visible = []

    for distance in range(DRAW_DISTANCE):
        segment_index = (base_index + distance) % segment_count
        curve, far_world_y = track[segment_index]
        near_world_y = track[(segment_index - 1) % segment_count][1]
        loop_offset = track_length if segment_index < base_index else 0
        near_z = segment_index * SEGMENT_LENGTH + loop_offset
        far_z = near_z + SEGMENT_LENGTH

        near = project_point(
            player_x * ROAD_WIDTH - curve_offset,
            near_world_y - camera_y,
            near_z - position,
        )
        far = project_point(
            player_x * ROAD_WIDTH - curve_offset - curve_velocity,
            far_world_y - camera_y,
            far_z - position,
        )

        curve_offset += curve_velocity
        curve_velocity += curve

        if near is None or far is None:
            continue

        # A segment whose far edge is below the crest line is hidden behind a
        # hill. Its road is not drawn, but it is kept so its trees can still
        # peek over the crest.
        hidden = far[1] >= max_y
        visible.append((near, far, segment_index, hidden))
        if not hidden:
            max_y = far[1]

    return visible


def build_sky():
    """Pre-render the gradient sky and its sun once, at startup.

    The surface is twice the screen wide so it can scroll sideways through
    curves and wrap without a seam, and it is blitted bottom-aligned to the
    horizon so it rises and falls with the road.
    """
    # Some displays (macOS) carry an alpha channel. Making the sky a real alpha
    # surface lets the glow blend into it instead of punching see-through holes
    # that later turn sprite edges black.
    sky = pygame.Surface((SKY_WIDTH, SKY_HEIGHT), pygame.SRCALPHA)
    for y in range(SKY_HEIGHT):
        blend = (y / (SKY_HEIGHT - 1)) ** SKY_GRADIENT_BIAS
        color = [
            round(top + (horizon - top) * blend)
            for top, horizon in zip(SKY_TOP_COLOR, SKY_HORIZON_COLOR)
        ]
        pygame.draw.line(sky, color, (0, y), (SKY_WIDTH, y))

    # Draw the sun oversized and scale it down, so the disc edge and the steps
    # between glow rings are smoothed instead of aliased. The outermost ring
    # must land on alpha zero, or it shows up as a hard arc against the sky.
    span = round(SUN_RADIUS * SUN_GLOW_EXTENT * 2)
    layer = pygame.Surface((span * SUN_SUPERSAMPLE,) * 2, pygame.SRCALPHA)
    layer_center = (span * SUN_SUPERSAMPLE // 2,) * 2
    for step in range(SUN_GLOW_STEPS, 0, -1):
        fade = step / SUN_GLOW_STEPS
        pygame.draw.circle(
            layer,
            (*SUN_COLOR, round(30 * (1 - fade) ** 2)),
            layer_center,
            SUN_RADIUS * (1 + (SUN_GLOW_EXTENT - 1) * fade) * SUN_SUPERSAMPLE,
        )
    pygame.draw.circle(layer, SUN_COLOR, layer_center, SUN_RADIUS * SUN_SUPERSAMPLE)
    layer = pygame.transform.smoothscale(layer, (span, span))

    sun_center = (SKY_WIDTH // 4, SKY_HEIGHT - SUN_HEIGHT_ABOVE_HORIZON)
    sky.blit(layer, layer.get_rect(center=sun_center))
    # Every pixel is opaque now, so drop per-pixel alpha for fast plain copies.
    return sky.convert()


def draw_background(screen, sky, sky_offset, horizon):
    """Sky above the horizon, ground below it."""
    left = -(sky_offset % SKY_WIDTH)
    sky_top = horizon - SKY_HEIGHT
    screen.blit(sky, (left, sky_top))
    screen.blit(sky, (left + SKY_WIDTH, sky_top))
    pygame.draw.rect(
        screen,
        "forestgreen",
        (0, horizon, SCREEN_WIDTH, SCREEN_HEIGHT - horizon),
    )


def draw_segment(screen, near, far, segment_index):
    near_x, near_y, near_width = near
    far_x, far_y, far_width = far
    stripe = (segment_index // RUMBLE_LENGTH) % 2
    grass_color = "forestgreen" if stripe else "green4"
    road_color = "gray30" if stripe else "gray35"
    rumble_color = "white" if stripe else "red3"

    pygame.draw.polygon(
        screen,
        grass_color,
        [(0, near_y), (SCREEN_WIDTH, near_y), (SCREEN_WIDTH, far_y), (0, far_y)],
    )

    near_rumble = near_width * KERB_WIDTH
    far_rumble = far_width * KERB_WIDTH
    pygame.draw.polygon(
        screen,
        rumble_color,
        [
            (near_x - near_width - near_rumble, near_y),
            (near_x - near_width, near_y),
            (far_x - far_width, far_y),
            (far_x - far_width - far_rumble, far_y),
        ],
    )
    pygame.draw.polygon(
        screen,
        rumble_color,
        [
            (near_x + near_width, near_y),
            (near_x + near_width + near_rumble, near_y),
            (far_x + far_width + far_rumble, far_y),
            (far_x + far_width, far_y),
        ],
    )
    pygame.draw.polygon(
        screen,
        road_color,
        [
            (near_x - near_width, near_y),
            (near_x + near_width, near_y),
            (far_x + far_width, far_y),
            (far_x - far_width, far_y),
        ],
    )

    if stripe:
        near_lane_width = near_width * 2 / LANES
        far_lane_width = far_width * 2 / LANES
        near_marker_width = near_width / 32
        far_marker_width = far_width / 32

        for lane in range(1, LANES):
            near_lane_x = near_x - near_width + near_lane_width * lane
            far_lane_x = far_x - far_width + far_lane_width * lane
            pygame.draw.polygon(
                screen,
                "white",
                [
                    (near_lane_x - near_marker_width / 2, near_y),
                    (near_lane_x + near_marker_width / 2, near_y),
                    (far_lane_x + far_marker_width / 2, far_y),
                    (far_lane_x - far_marker_width / 2, far_y),
                ],
            )


def blit_scaled(screen, image, rect):
    """Draw ``image`` stretched to ``rect``, scaling only the on-screen part.

    A sprite passing the camera can project thousands of pixels tall. Scaling
    just the visible piece keeps the cost under one screen however close it is.
    """
    visible = rect.clip(screen.get_rect())
    if not visible.width or not visible.height:
        return
    to_image_x = image.get_width() / rect.width
    to_image_y = image.get_height() / rect.height
    source = pygame.Rect(
        int((visible.left - rect.left) * to_image_x),
        int((visible.top - rect.top) * to_image_y),
        max(1, math.ceil(visible.width * to_image_x)),
        max(1, math.ceil(visible.height * to_image_y)),
    ).clip(image.get_rect())
    if not source.width or not source.height:
        return
    screen.blit(pygame.transform.scale(image.subsurface(source), visible.size), visible)


def sprite_rect(image, width, x, y):
    """A rect ``width`` wide with the image's proportions, standing on (x, y)."""
    height = width * image.get_height() / image.get_width()
    if height < 1:
        return None
    rect = pygame.Rect(0, 0, round(width), round(height))
    rect.midbottom = (round(x), round(y))
    return rect


def draw_trees(screen, tree_image, segment_trees, near):
    """Stand each tree on the segment's near edge, sized by the road there."""
    road_x, road_y, half_width = near
    for offset, size in segment_trees:
        rect = sprite_rect(
            tree_image,
            half_width * TREE_WIDTH * size,
            road_x + offset * half_width,
            road_y,
        )
        if rect:
            blit_scaled(screen, tree_image, rect)


def draw_cars(screen, segment_cars, near, far):
    """Place each car at its exact spot inside the segment.

    Trees sit on the near edge, but cars move, so snapping them to an edge
    would make them hop a whole segment at a time. Blending between the near
    and far projections keeps their motion smooth.
    """
    for car in segment_cars:
        percent = (car.distance % SEGMENT_LENGTH) / SEGMENT_LENGTH
        road_x, road_y, half_width = (
            n + (f - n) * percent for n, f in zip(near, far)
        )
        rect = sprite_rect(
            car.image,
            half_width * CAR_WIDTH * car.size,
            road_x + car.x * half_width,
            road_y,
        )
        if rect:
            blit_scaled(screen, car.image, rect)


def draw_road(
    screen,
    track,
    trees,
    tree_image,
    cars,
    position,
    player_x,
    camera_y,
    sky,
    sky_offset,
):
    cars_by_segment = {}
    for car in cars:
        segment_index = int(car.distance // SEGMENT_LENGTH) % len(track)
        cars_by_segment.setdefault(segment_index, []).append(car)

    projected = projected_road(track, position, player_x, camera_y)
    horizon = min(
        (far[1] for _, far, _, hidden in projected if not hidden),
        default=SCREEN_HEIGHT / 2,
    )

    draw_background(screen, sky, sky_offset, horizon)
    # Far to near: nearer road and grass paint over anything behind them, which
    # also hides the part of a tree that sits below a hill crest.
    # Near the horizon most segments are thinner than a pixel, so they are
    # gathered into one span and drawn together once it is a pixel tall.
    span_far = None
    for near, far, segment_index, hidden in reversed(projected):
        if hidden:
            span_far = None
        else:
            span_far = span_far or far
            if near[1] - span_far[1] >= 1:
                draw_segment(screen, near, span_far, segment_index)
                span_far = None
        if trees[segment_index]:
            draw_trees(screen, tree_image, trees[segment_index], near)
        if segment_index in cars_by_segment:
            draw_cars(screen, cars_by_segment[segment_index], near, far)


def draw_countdown(screen, font, race):
    """3, 2, 1 over the grid, then GO! for a moment after the start."""
    if race.countdown > 0:
        text, color = str(math.ceil(race.countdown)), "white"
    elif race.clock < GO_DISPLAY_SECONDS:
        text, color = "GO!", HUD_BEST_COLOR
    else:
        return
    shadow = font.render(text, True, "black")
    label = font.render(text, True, color)
    center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
    screen.blit(shadow, shadow.get_rect(center=(center[0] + 4, center[1] + 4)))
    screen.blit(label, label.get_rect(center=center))


def draw_results(screen, font, race):
    """Finishing order, filled in live as the other racers cross the line."""
    rows = []
    for place, car in enumerate(standings(race), start=1):
        result = (
            format_lap_time(car.finish_time)
            if car.finish_time is not None
            else "racing"
        )
        color = "white" if car is race.player else HUD_MUTED_COLOR
        name = font.render(f"{place}. {car.name}", True, color)
        rows.append((name, font.render(result, True, color)))
    title = font.render("Results", True, HUD_BEST_COLOR)
    footer = font.render("R to restart", True, HUD_MUTED_COLOR)

    # Names and times in two columns; the font is not monospaced.
    name_width = max(name.get_width() for name, _ in rows)
    time_width = max(time.get_width() for _, time in rows)
    line_height = font.get_linesize()
    width = max(name_width + RESULTS_PADDING + time_width, footer.get_width())
    height = line_height * (len(rows) + 2)
    panel = pygame.Rect(0, 0, width + 2 * RESULTS_PADDING, height + 2 * RESULTS_PADDING)
    panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)
    pygame.draw.rect(screen, MINIMAP_BACKGROUND, panel, border_radius=HUD_PADDING)

    left = panel.left + RESULTS_PADDING
    top = panel.top + RESULTS_PADDING
    screen.blit(title, (left, top))
    for index, (name, time) in enumerate(rows, start=1):
        y = top + index * line_height
        screen.blit(name, (left, y))
        screen.blit(time, (left + width - time.get_width(), y))
    screen.blit(footer, (left, top + (len(rows) + 1) * line_height))


def main():
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(
        "Self-Driving Racer | W/Up: accelerate | S/Down: brake | A/D: steer"
        " | R: restart"
    )

    car_path = Path(__file__).resolve().parent.parent / "assets" / "car-rear.png"
    car_image = pygame.image.load(car_path).convert_alpha()
    car_image = pygame.transform.smoothscale(
        car_image, (PLAYER_CAR_WIDTH, PLAYER_CAR_HEIGHT)
    )
    turning_car_path = (
        Path(__file__).resolve().parent.parent
        / "assets"
        / "car-rear-turn-left-subtle.png"
    )
    car_turn_left = pygame.image.load(turning_car_path).convert_alpha()
    car_turn_left = pygame.transform.smoothscale(
        car_turn_left, (PLAYER_CAR_WIDTH, PLAYER_CAR_HEIGHT)
    )
    car_turn_right = pygame.transform.flip(car_turn_left, True, False)
    car_rect = car_image.get_rect(
        midbottom=(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - PLAYER_CAR_BOTTOM_MARGIN,
        )
    )

    car_shadow = pygame.Surface((PLAYER_CAR_WIDTH, CAR_SHADOW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(
        car_shadow,
        (0, 0, 0, 45),
        (0, 0, PLAYER_CAR_WIDTH, CAR_SHADOW_HEIGHT),
    )
    pygame.draw.ellipse(
        car_shadow,
        (0, 0, 0, 90),
        (30, 10, PLAYER_CAR_WIDTH - 60, CAR_SHADOW_HEIGHT - 20),
    )
    car_shadow_rect = car_shadow.get_rect(
        center=(
            car_rect.centerx,
            car_rect.top + round(car_rect.height * CAR_SHADOW_VERTICAL_POSITION),
        )
    )

    sky = build_sky()
    track = build_track()
    track_length = len(track) * SEGMENT_LENGTH
    minimap, minimap_path = build_minimap(track)
    trees = build_trees(track)
    tree_image = build_tree_image()
    race = build_race(car_image, track)
    sky_offset = 0.0
    visual_steering = 0.0
    accumulator = 0.0
    hud_font = pygame.font.Font(None, HUD_FONT_SIZE)
    countdown_font = pygame.font.Font(None, COUNTDOWN_FONT_SIZE)
    results_font = pygame.font.Font(None, RESULTS_FONT_SIZE)
    running = True

    while running:
        # tick() sleeps, and on macOS the sleep overshoots unevenly; some frames
        # then run no physics step and others two, which reads as jumping.
        # tick_busy_loop() waits precisely at the cost of a little CPU.
        frame_time = min(clock.tick_busy_loop(FPS) / 1000, 0.25)
        accumulator += frame_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                race = build_race(car_image, track)
                sky_offset = 0.0
                visual_steering = 0.0

        keys = pygame.key.get_pressed()
        steering = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        throttle = int(keys[pygame.K_w] or keys[pygame.K_UP])
        brake = int(keys[pygame.K_s] or keys[pygame.K_DOWN])
        player = race.player

        while accumulator >= FIXED_STEP:
            controls = (steering, throttle, brake)
            update_race(race, track, track_length, controls, FIXED_STEP)
            road_curve = road_curve_at(track, player.distance % track_length)
            sky_offset += SKY_PARALLAX_SPEED * road_curve * player.speed * FIXED_STEP
            animation_target = player.steering if player.speed > 0 else 0
            animation_blend = min(1.0, STEERING_ANIMATION_RESPONSE * FIXED_STEP)
            visual_steering += (animation_target - visual_steering) * animation_blend
            accumulator -= FIXED_STEP

        # The camera sits PLAYER_Z_OFFSET behind the car it follows.
        position = (player.distance - PLAYER_Z_OFFSET) % track_length
        camera_y = road_elevation_at(track, position) + CAMERA_HEIGHT
        draw_road(
            screen,
            track,
            trees,
            tree_image,
            race.cars[1:],
            position,
            player.x,
            camera_y,
            sky,
            sky_offset,
        )
        car_center_x = SCREEN_WIDTH // 2 + round(visual_steering * PLAYER_CAR_SWAY)
        car_shadow_rect.centerx = car_center_x
        if visual_steering < -STEERING_SPRITE_THRESHOLD:
            rendered_car = car_turn_left
        elif visual_steering > STEERING_SPRITE_THRESHOLD:
            rendered_car = car_turn_right
        else:
            rendered_car = car_image
        rendered_car_rect = rendered_car.get_rect(
            midbottom=(
                car_center_x,
                SCREEN_HEIGHT - PLAYER_CAR_BOTTOM_MARGIN,
            )
        )
        screen.blit(car_shadow, car_shadow_rect)
        screen.blit(rendered_car, rendered_car_rect)
        draw_minimap(screen, minimap, minimap_path, race, track_length)
        draw_hud(screen, hud_font, race)
        draw_countdown(screen, countdown_font, race)
        if player.finish_time is not None:
            draw_results(screen, results_font, race)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
