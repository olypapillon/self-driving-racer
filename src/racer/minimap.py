"""The mini map of the whole lap in the corner of the race view."""

import math

import pygame

from .settings import (
    GHOST_COLOR,
    MINIMAP_BACKGROUND,
    MINIMAP_FLAG_COLUMNS,
    MINIMAP_FLAG_SQUARE,
    MINIMAP_MARGIN,
    MINIMAP_PADDING,
    MINIMAP_PLAYER_COLOR,
    MINIMAP_PLAYER_RADIUS,
    MINIMAP_RACER_RADIUS,
    MINIMAP_ROAD_COLOR,
    MINIMAP_ROAD_WIDTH,
    MINIMAP_SIZE,
    MINIMAP_TRAFFIC_RADIUS,
    SCREEN_WIDTH,
    SEGMENT_LENGTH,
    TURN_DEGREES_PER_CURVE,
)


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


def draw_minimap(screen, minimap, path, race, track_length, ghost_car=None):
    left = SCREEN_WIDTH - MINIMAP_SIZE - MINIMAP_MARGIN
    top = MINIMAP_MARGIN
    screen.blit(minimap, (left, top))
    if ghost_car is not None:
        point = minimap_point(path, left, top, ghost_car.distance % track_length)
        pygame.draw.circle(screen, GHOST_COLOR, point, MINIMAP_PLAYER_RADIUS, 2)

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
