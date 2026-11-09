"""The track: building the road from segments, its bends, hills and features,
and the speed plan the built-in AI follows."""

import math

from .settings import (
    AI_BRAKING,
    AI_STEER_BUDGET,
    FEATURE_HALF_WIDTH,
    HANDLING_REFERENCE_SPEED,
    HILL_LOW,
    MAX_SPEED,
    PLAYER_LATERAL_SPEED,
    ROAD_CURVE_DRIFT_SPEED,
    SEGMENT_LENGTH,
    STEERING_GRIP_FALLOFF,
    TRACK_FEATURES,
    TURN_DEGREES_PER_CURVE,
)


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
    """A hilly straight and a 180-degree bend that ends back at height zero.

    One hill per straight keeps the lap short (about 25 s); the bend is left
    unchanged so corners drive exactly as before.
    """
    add_straight(track, 40)
    add_hill(track, 40, HILL_LOW)
    add_hill(track, 40, -HILL_LOW)
    add_straight(track, 20)
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


def build_features(track):
    """Index the track features by segment for fast lookup and drawing."""
    by_segment = [[] for _ in track]
    for kind, first, count, lane_x in TRACK_FEATURES:
        for index in range(first, first + count):
            by_segment[index % len(track)].append((kind, lane_x))
    return by_segment


def feature_at(features, distance, x):
    """'boost', 'mud' or None under a car at ``distance`` and lateral ``x``."""
    segment = int(distance // SEGMENT_LENGTH) % len(features)
    for kind, lane_x in features[segment]:
        if abs(x - lane_x) <= FEATURE_HALF_WIDTH:
            return kind
    return None


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
