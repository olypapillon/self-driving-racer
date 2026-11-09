"""Race every algorithm and write the leaderboard.

    uv run python src/benchmark.py

Time trial: each algorithm alone on the track, over several seeds (the seed
changes the random sideways "wander" of the slippery surface). Ranks raw
driving: lines, braking, boost pads and mud.

Battle: all six algorithms on one grid with traffic, over many seeds. The
grid is reshuffled each seed and the camera car (which bumps never move) is
rotated through the algorithms, so no one keeps an advantage.

Writes leaderboard.json, ghosts/<algorithm>.json (each one's best time-trial
run), the leaderboard table in README.md, and updates ghosts/leader.json if an
algorithm beat the stored leader.

    uv run python src/benchmark.py --readme-only   # just redraw the README table
"""

import json
import os
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
sys.path.insert(0, str(SRC))
from racer import drivers  # noqa: E402
from racer.ghost import Ghost, load_ghost, save_ghost  # noqa: E402
from racer.race import simulate, standings  # noqa: E402
from racer.settings import RULES_VERSION  # noqa: E402

README = ROOT / "README.md"
TABLE_START = "<!-- leaderboard:start -->"
TABLE_END = "<!-- leaderboard:end -->"

TRIAL_SEEDS = range(5)
BATTLE_SEEDS = range(12)
MAX_TIME = 60.0


def slug(name):
    return name.lower().replace(" ", "-")


def describe(name):
    cls = drivers.DRIVER_CLASSES.get(name)
    if cls is None:
        return {
            "family": "Rule-based lane keeping (PD control + speed plan)",
            "inspired_by": "Classic hand-written driving logic, like pre-v12 Tesla Autopilot code",
        }
    return {"family": cls.family, "inspired_by": cls.inspired_by}


def time_trials(name):
    runs = []
    for seed in TRIAL_SEEDS:
        started = time.perf_counter()
        race = simulate(name, "Time trial", seed, MAX_TIME)
        car = race.player
        runs.append(
            {
                "seed": seed,
                "time": car.finish_time,
                "mud": round(car.mud_time, 2),
                "grass": round(car.grass_time, 2),
                "boosts": car.boosts,
                "cpu_ms_per_race_second": round(
                    1000 * (time.perf_counter() - started) / max(race.clock, 1e-6), 2
                ),
                "frames": list(race.recording),
            }
        )
    return runs


def battles():
    results = {name: [] for name in drivers.ALGORITHMS}
    for seed in BATTLE_SEEDS:
        camera = drivers.ALGORITHMS[seed % len(drivers.ALGORITHMS)]
        race = simulate(camera, "Battle", seed, MAX_TIME)
        for place, car in enumerate(standings(race), start=1):
            results[car.algorithm].append(place)
    return results


def leaderboard_table(leaderboard):
    """The README's markdown table for the rows of leaderboard.json."""
    lines = [
        "| # | Algorithm | Approach | Trial avg | Best | Battle avg place | Battle wins | CPU ms per race second |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for e in leaderboard["algorithms"]:
        if e["trial_mean"] is None:
            trial = "DNF"
        else:
            trial = f"{e['trial_mean']:.2f} s"
            if not e["trial_finished"].startswith(str(leaderboard["trial_seeds"])):
                trial += f" ({e['trial_finished']} finished)"
        best = f"{e['trial_best']:.2f} s" if e["trial_best"] is not None else "-"
        lines.append(
            f"| {e['rank']} | {e['name']} | {e['family']} | {trial} | {best} | "
            f"{e['battle_avg_place']:.2f} | {e['battle_wins']} | {e['cpu_ms_per_race_second']:.1f} |"
        )
    return "\n".join(lines)


def with_table(readme_text, table):
    """``readme_text`` with the text between the leaderboard markers replaced."""
    start = readme_text.index(TABLE_START) + len(TABLE_START)
    end = readme_text.index(TABLE_END)
    return readme_text[:start] + "\n" + table + "\n" + readme_text[end:]


def update_readme():
    leaderboard = json.loads((ROOT / "leaderboard.json").read_text())
    README.write_text(with_table(README.read_text(), leaderboard_table(leaderboard)))
    print("README.md leaderboard table updated")


def main():
    if "--readme-only" in sys.argv:
        update_readme()
        return
    board = []
    best_run = None
    for name in drivers.ALGORITHMS:
        runs = time_trials(name)
        finished = [r for r in runs if r["time"] is not None]
        times = [r["time"] for r in finished]
        entry = {
            "name": name,
            **describe(name),
            "trial_finished": f"{len(finished)}/{len(runs)}",
            "trial_mean": round(statistics.mean(times), 2) if times else None,
            "trial_best": round(min(times), 2) if times else None,
            "mud_s": round(statistics.mean(r["mud"] for r in runs), 2),
            "grass_s": round(statistics.mean(r["grass"] for r in runs), 2),
            "boosts": round(statistics.mean(r["boosts"] for r in runs), 1),
            "cpu_ms_per_race_second": round(
                statistics.mean(r["cpu_ms_per_race_second"] for r in runs), 2
            ),
        }
        if finished:
            best = min(finished, key=lambda r: r["time"])
            ghost = Ghost(name, best["time"], best["frames"])
            (ROOT / "ghosts").mkdir(exist_ok=True)
            (ROOT / "ghosts" / f"{slug(name)}.json").write_text(
                json.dumps({"rules": RULES_VERSION, "name": name, "time": best["time"], "frames": best["frames"]})
            )
            if best_run is None or ghost.time < best_run.time:
                best_run = ghost
        board.append(entry)
        print(f"time trial  {name:13s} {entry['trial_mean']}  ({entry['trial_finished']} finished)", flush=True)

    places = battles()
    for entry in board:
        mine = places[entry["name"]]
        entry["battle_avg_place"] = round(statistics.mean(mine), 2)
        entry["battle_wins"] = sum(1 for p in mine if p == 1)

    board.sort(key=lambda e: (e["trial_mean"] is None, e["trial_mean"] or 0))
    for rank, entry in enumerate(board, start=1):
        entry["rank"] = rank
    (ROOT / "leaderboard.json").write_text(
        json.dumps(
            {
                "rules": RULES_VERSION,
                "trial_seeds": len(TRIAL_SEEDS),
                "battle_seeds": len(BATTLE_SEEDS),
                "algorithms": board,
            },
            indent=2,
        )
    )

    update_readme()

    leader = load_ghost()
    if best_run is not None and (leader is None or best_run.time < leader.time):
        save_ghost(best_run)
        print(f"new leader ghost: {best_run.name} {best_run.time:.2f}s")

    print()
    print(f"{'#':>2} {'algorithm':13s} {'trial avg':>9} {'best':>6} {'mud':>5} {'grass':>5} {'boosts':>6} {'battle':>6} {'wins':>4} {'cpu':>6}")
    for e in board:
        print(
            f"{e['rank']:>2} {e['name']:13s} {e['trial_mean'] or 'DNF':>9} {e['trial_best'] or '-':>6} "
            f"{e['mud_s']:>5} {e['grass_s']:>5} {e['boosts']:>6} {e['battle_avg_place']:>6} "
            f"{e['battle_wins']:>4} {e['cpu_ms_per_race_second']:>6}"
        )


if __name__ == "__main__":
    main()
