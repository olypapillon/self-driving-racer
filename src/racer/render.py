"""The pseudo-3D road view: projecting segments and drawing road, scenery and cars."""

import random

import pygame

from .settings import (
    BOOST_COLORS,
    CAMERA_DEPTH,
    CAR_WIDTH,
    DRAW_DISTANCE,
    FEATURE_HALF_WIDTH,
    KERB_WIDTH,
    LANES,
    MIN_TREE_PIXELS,
    MUD_COLORS,
    ROAD_WIDTH,
    RUMBLE_LENGTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SEGMENT_LENGTH,
    SKY_HEIGHT,
    SKY_WIDTH,
    TREE_CHANCE,
    TREE_MAX_OFFSET,
    TREE_MAX_SIZE,
    TREE_MIN_OFFSET,
    TREE_MIN_SIZE,
    TREE_SEED,
    TREE_SPACING,
    TREE_WIDTH,
)
from .sprites import blit_scaled, sprite_rect


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
    previous_far = None

    for distance in range(DRAW_DISTANCE):
        segment_index = (base_index + distance) % segment_count
        curve, far_world_y = track[segment_index]
        near_world_y = track[(segment_index - 1) % segment_count][1]
        loop_offset = track_length if segment_index < base_index else 0
        near_z = segment_index * SEGMENT_LENGTH + loop_offset
        far_z = near_z + SEGMENT_LENGTH

        # Each segment starts exactly where the previous one ended (same x
        # offset, height and depth), so its near edge is the last far edge.
        if distance:
            near = previous_far
        else:
            near = project_point(
                player_x * ROAD_WIDTH - curve_offset,
                near_world_y - camera_y,
                near_z - position,
            )
        far = previous_far = project_point(
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


def draw_features(screen, near, far, segment_features, segment_index):
    """Paint boost pads and mud patches as lane-wide strips on the road."""
    near_x, near_y, near_width = near
    far_x, far_y, far_width = far
    stripe = segment_index % 2
    for kind, lane_x in segment_features:
        color = (BOOST_COLORS if kind == "boost" else MUD_COLORS)[stripe]
        left, right = lane_x - FEATURE_HALF_WIDTH, lane_x + FEATURE_HALF_WIDTH
        pygame.draw.polygon(
            screen,
            color,
            [
                (near_x + left * near_width, near_y),
                (near_x + right * near_width, near_y),
                (far_x + right * far_width, far_y),
                (far_x + left * far_width, far_y),
            ],
        )


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
        if rect and rect.height >= MIN_TREE_PIXELS:
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
    features,
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
                if features[segment_index]:
                    draw_features(
                        screen, near, span_far, features[segment_index], segment_index
                    )
                span_far = None
        if trees[segment_index]:
            draw_trees(screen, tree_image, trees[segment_index], near)
        if segment_index in cars_by_segment:
            draw_cars(screen, cars_by_segment[segment_index], near, far)
