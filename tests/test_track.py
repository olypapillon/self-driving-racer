import pytest

from racer.settings import (
    FEATURE_HALF_WIDTH,
    MAX_SPEED,
    SEGMENT_LENGTH,
    TRACK_FEATURES,
    TURN_DEGREES_PER_CURVE,
)
from racer.track import (
    build_features,
    build_speed_plan,
    build_track,
    feature_at,
    track_gap,
)


@pytest.fixture(scope="module")
def track():
    return build_track()


def test_the_lap_is_a_closed_loop(track):
    assert len(track) == 1680
    total_turn = sum(curve for curve, _ in track) * TURN_DEGREES_PER_CURVE
    assert total_turn == pytest.approx(360.0)
    assert track[0][1] == pytest.approx(track[-1][1])  # back to the same height


def test_speed_plan_slows_for_bends_only(track):
    limits, plan = build_speed_plan(track)
    assert max(plan) == pytest.approx(MAX_SPEED)
    assert min(plan) < MAX_SPEED
    straight = [index for index, (curve, _) in enumerate(track) if curve == 0]
    assert any(plan[index] == pytest.approx(MAX_SPEED) for index in straight)


@pytest.mark.parametrize("kind, first, count, lane_x", TRACK_FEATURES)
def test_every_feature_sits_in_its_lane(track, kind, first, count, lane_x):
    features = build_features(track)
    middle = (first + count / 2) * SEGMENT_LENGTH
    assert feature_at(features, middle, lane_x) == kind
    assert feature_at(features, middle, lane_x + 2 * FEATURE_HALF_WIDTH) != kind
    assert feature_at(features, (first - 1) * SEGMENT_LENGTH, lane_x) is None


def test_track_gap_takes_the_short_way_round():
    length = 1000.0
    assert track_gap(100, 300, length) == 200
    assert track_gap(950, 50, length) == 100  # ahead, across the line
    assert track_gap(50, 950, length) == -100  # behind, across the line
