import pygame
import pytest

from racer.drivers import ALGORITHMS
from racer.race import build_race, count_laps, simulate, standings
from racer.settings import RACE_LAPS, SEGMENT_LENGTH
from racer.track import build_track


def test_races_are_deterministic():
    first = simulate("Stanley", "Time trial", seed=3, max_time=60)
    second = simulate("Stanley", "Time trial", seed=3, max_time=60)
    assert first.player.finish_time == second.player.finish_time
    assert first.recording == second.recording


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_every_algorithm_finishes_a_time_trial(algorithm):
    race = simulate(algorithm, "Time trial", seed=0, max_time=60)
    assert race.player.finish_time is not None
    assert 20 < race.player.finish_time < 40


def test_a_battle_has_every_algorithm_and_ranks_finishers_by_time():
    race = simulate("Evolved NN", "Battle", seed=0, max_time=60)
    racers = standings(race)
    assert sorted(car.algorithm for car in racers) == sorted(ALGORITHMS)
    times = [car.finish_time for car in racers if car.finish_time is not None]
    assert times == sorted(times)


def test_a_bump_back_over_the_line_cannot_finish_a_lap_twice():
    pygame.init()
    track = build_track()
    track_length = len(track) * SEGMENT_LENGTH
    race = build_race(pygame.Surface((4, 4), pygame.SRCALPHA), track, "Baseline", "Time trial")
    car = race.player
    race.clock = 10.0
    car.distance = RACE_LAPS * track_length + 1  # crosses the line
    count_laps(race, car, track_length)
    assert car.finish_time == 10.0

    race.clock = 11.0
    car.distance -= 2  # knocked back behind the line...
    count_laps(race, car, track_length)
    car.distance += 2  # ...and across it again
    count_laps(race, car, track_length)
    assert car.finish_time == 10.0
    assert car.laps == RACE_LAPS
