import pytest

from racer.physics import move_sideways, move_speed, surface_drag
from racer.settings import (
    BOOST_FADE,
    BOOST_MAX_SPEED,
    FIXED_STEP,
    KERB_WIDTH,
    MAX_SPEED,
    MUD_MAX_SPEED,
    OFF_ROAD_MAX_SPEED,
)

DT = FIXED_STEP


def run_speed(speed, seconds, **controls):
    """Apply move_speed for ``seconds`` with fixed controls."""
    controls = {"throttle": 1, "brake": 0.0, "player_x": 0.0, **controls}
    for _ in range(round(seconds / DT)):
        speed = move_speed(speed, controls["throttle"], controls["brake"],
                           controls["player_x"], DT,
                           controls.get("boosting", False), controls.get("on_mud", False))
    return speed


def test_engine_alone_stops_at_top_speed():
    assert run_speed(0.0, 20) == pytest.approx(MAX_SPEED)


def test_boost_lifts_speed_past_top_speed_but_no_further_than_its_cap():
    speed = run_speed(MAX_SPEED, 5, boosting=True)
    assert speed == pytest.approx(BOOST_MAX_SPEED)


def test_boost_speed_fades_even_with_the_throttle_held():
    # Regression: holding the throttle used to keep a boost's extra speed
    # forever, and the evolved driver learned to exploit it.
    one_second_later = run_speed(BOOST_MAX_SPEED, 1.0)
    assert one_second_later == pytest.approx(BOOST_MAX_SPEED - BOOST_FADE, rel=1e-3)
    fade_time = (BOOST_MAX_SPEED - MAX_SPEED) / BOOST_FADE
    assert run_speed(BOOST_MAX_SPEED, fade_time + 0.1) == pytest.approx(MAX_SPEED)


@pytest.mark.parametrize(
    ("surface", "limit"),
    [({"on_mud": True}, MUD_MAX_SPEED), ({"player_x": 3.0}, OFF_ROAD_MAX_SPEED)],
    ids=["mud", "grass"],
)
def test_slow_surfaces_pull_speed_down_to_their_limit(surface, limit):
    assert run_speed(MAX_SPEED, 5, **surface) == pytest.approx(limit)


def test_braking_never_makes_speed_negative():
    assert run_speed(MAX_SPEED, 10, throttle=0, brake=1.0) == 0.0


def test_surface_zones():
    assert surface_drag(0.0)[1] == MAX_SPEED  # asphalt: no drag
    assert surface_drag(1 + KERB_WIDTH / 2)[1] < MAX_SPEED  # kerb
    assert surface_drag(-2.0)[1] == OFF_ROAD_MAX_SPEED  # grass, either side


def test_steering_right_moves_right_and_no_input_holds_the_line():
    x, _ = move_sideways(0.0, 0.0, 1.0, 0.0, MAX_SPEED / 2, 0.0, DT)
    assert x > 0
    x, drift = move_sideways(0.0, 0.0, 0.0, 0.0, MAX_SPEED / 2, 0.0, DT)
    assert (x, drift) == (0.0, 0.0)


def test_a_bend_pushes_the_car_outward_harder_at_speed():
    slow, _ = move_sideways(0.0, 0.0, 0.0, 1.0, MAX_SPEED / 4, 0.0, DT)
    fast, _ = move_sideways(0.0, 0.0, 0.0, 1.0, MAX_SPEED, 0.0, DT)
    assert fast < slow < 0
