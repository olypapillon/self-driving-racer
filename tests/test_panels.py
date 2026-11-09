from types import SimpleNamespace

from racer.drivers import ALGORITHMS
from racer.panels import leaderboard_rows, load_leaderboard, record_your_finish
from racer.settings import HUMAN


def names(rows):
    return [name for _, name, _, _ in rows]


def test_without_a_lap_you_are_listed_last():
    rows = leaderboard_rows(load_leaderboard(), {})
    assert names(rows)[-1] == HUMAN
    assert sorted(names(rows)[:-1]) == sorted(ALGORITHMS)


def test_your_best_lap_is_ranked_among_the_algorithms():
    board = load_leaderboard()
    times = sorted(entry["trial_mean"] for entry in board)
    between = (times[0] + times[1]) / 2
    rows = leaderboard_rows(board, {"time_trial": between})
    assert names(rows).index(HUMAN) == 1


def test_only_a_better_time_trial_replaces_your_best():
    best = {}
    trial = SimpleNamespace(mode="Time trial", player=SimpleNamespace(finish_time=30.0))
    assert record_your_finish(best, trial)
    trial.player.finish_time = 31.0
    assert not record_your_finish(best, trial)
    trial.player.finish_time = 29.5
    assert record_your_finish(best, trial)
    assert best == {"time_trial": 29.5}
