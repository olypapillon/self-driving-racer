"""Train the two learned drivers and save their weights to src/weights/.

    uv run python src/train_drivers.py imitation   # behaviour cloning + DAgger
    uv run python src/train_drivers.py evolve      # evolution strategy, starts from imitation

Training uses numpy (a dev dependency); driving does not, so the trained
networks also run in the browser build.
"""

import importlib.util
import json
import os
import random
import sys
import time
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import numpy as np  # noqa: E402

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
import drivers  # noqa: E402

spec = importlib.util.spec_from_file_location("game", SRC / "3D-game.py")
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)

WEIGHTS = SRC / "weights"
MAX_TIME = 60.0


# ---------------------------------------------------------------------------
# Network parameters <-> one flat vector (handy for evolution)
# ---------------------------------------------------------------------------


def init_params(rng):
    scale1 = 1 / np.sqrt(drivers.INPUTS)
    scale2 = 1 / np.sqrt(drivers.HIDDEN)
    return {
        "w1": rng.normal(0, scale1, (drivers.HIDDEN, drivers.INPUTS)),
        "b1": np.zeros(drivers.HIDDEN),
        "w2": rng.normal(0, scale2, (2, drivers.HIDDEN)),
        "b2": np.zeros(2),
    }


def flatten(params):
    return np.concatenate([params[k].ravel() for k in ("w1", "b1", "w2", "b2")])


def unflatten(vector):
    shapes = {
        "w1": (drivers.HIDDEN, drivers.INPUTS),
        "b1": (drivers.HIDDEN,),
        "w2": (2, drivers.HIDDEN),
        "b2": (2,),
    }
    params, start = {}, 0
    for key, shape in shapes.items():
        size = int(np.prod(shape))
        params[key] = vector[start : start + size].reshape(shape)
        start += size
    return params


def to_net(params):
    return drivers.TinyNet(*(params[k].tolist() for k in ("w1", "b1", "w2", "b2")))


def save(params, name, info):
    WEIGHTS.mkdir(exist_ok=True)
    data = {k: params[k].tolist() for k in ("w1", "b1", "w2", "b2")}
    data["info"] = info
    (WEIGHTS / name).write_text(json.dumps(data))


class NetDriver(drivers.NeuralDriver):
    """A neural driver whose network is given directly instead of loaded."""

    name = "candidate"

    def __init__(self, net):
        self.net = net


# ---------------------------------------------------------------------------
# Imitation: behaviour cloning with DAgger
# ---------------------------------------------------------------------------


class DaggerDriver(drivers.Driver):
    """Drives with the student (or the expert, with probability ``beta``) and
    asks the expert what it would have done every few steps."""

    name = "dagger"

    def __init__(self, student, beta, rng, label_every=4):
        self.student, self.beta, self.rng = student, beta, rng
        self.label_every = label_every
        self.expert = drivers.MPCPlanner()
        self.samples = []

    def reset(self):
        self.expert.reset()
        self.step = 0
        self.held = (0.0, 0, 0.0)

    def drive(self, world, car):
        if self.step % self.label_every == 0:
            expert_action = self.expert.label(world, car)
            self.samples.append(
                (drivers.observe(world, car), drivers.action_to_target(*expert_action))
            )
            self.held = expert_action
        self.step += 1
        if self.student is None or self.rng.random() < self.beta:
            return self.held
        return self.student.drive(world, car)


def fit(params, inputs, targets, epochs=4000, lr=0.01):
    """Plain gradient descent (Adam) on mean squared error."""
    keys = ("w1", "b1", "w2", "b2")
    m = {k: np.zeros_like(params[k]) for k in keys}
    v = {k: np.zeros_like(params[k]) for k in keys}
    n = len(inputs)
    for epoch in range(1, epochs + 1):
        hidden = np.tanh(inputs @ params["w1"].T + params["b1"])
        out = np.tanh(hidden @ params["w2"].T + params["b2"])
        error = out - targets
        # Steering errors matter more than pedal errors for staying on the road.
        error = error * np.array([2.0, 1.0])
        d_out = 2 * error * (1 - out**2) / n
        grads = {"w2": d_out.T @ hidden, "b2": d_out.sum(0)}
        d_hidden = (d_out @ params["w2"]) * (1 - hidden**2)
        grads["w1"] = d_hidden.T @ inputs
        grads["b1"] = d_hidden.sum(0)
        for k in keys:
            m[k] = 0.9 * m[k] + 0.1 * grads[k]
            v[k] = 0.999 * v[k] + 0.001 * grads[k] ** 2
            m_hat = m[k] / (1 - 0.9**epoch)
            v_hat = v[k] / (1 - 0.999**epoch)
            params[k] -= lr * m_hat / (np.sqrt(v_hat) + 1e-8)
    return float((error**2).mean())


def race_time(race):
    """Finish time, or a penalty that still rewards getting further."""
    car = race.player
    if car.finish_time is not None:
        return car.finish_time
    remaining = race.world.track_length - car.distance
    return MAX_TIME + max(0.0, remaining) / game.MAX_SPEED


def train_imitation(rounds=5, seeds=(0, 1, 2, 3)):
    rng = random.Random(0)
    params = init_params(np.random.default_rng(0))
    inputs, targets = [], []
    student = None
    for round_index in range(rounds):
        beta = 1.0 if round_index == 0 else 0.5**round_index
        started = time.time()
        for seed in seeds:
            dagger = DaggerDriver(student, beta, rng)
            game.simulate("Baseline", "Time trial", seed, MAX_TIME, brain=dagger)
            for obs, target in dagger.samples:
                inputs.append(obs)
                targets.append(target)
        loss = fit(params, np.array(inputs), np.array(targets))
        student = NetDriver(to_net(params))
        times = [
            race_time(game.simulate("Baseline", "Time trial", s, MAX_TIME, brain=NetDriver(to_net(params))))
            for s in seeds
        ]
        print(
            f"round {round_index}: {len(inputs)} samples, loss {loss:.4f}, "
            f"student times {[round(t, 2) for t in times]} ({time.time() - started:.0f}s)",
            flush=True,
        )
    save(params, "imitation.json", {"samples": len(inputs), "rounds": rounds})
    return params


def evaluate(vector, seeds):
    net = to_net(unflatten(vector))
    return float(
        np.mean(
            [race_time(game.simulate("Baseline", "Time trial", s, MAX_TIME, brain=NetDriver(net))) for s in seeds]
        )
    )


def train_evolution(generations=30, pairs=8, sigma=0.03, lr=0.02, seeds=(0, 1)):
    """OpenAI-style evolution strategy with mirrored noise and rank fitness."""
    start = json.loads((WEIGHTS / "imitation.json").read_text())
    theta = flatten({k: np.array(start[k]) for k in ("w1", "b1", "w2", "b2")})
    rng = np.random.default_rng(1)
    best_vector, best_time = theta.copy(), evaluate(theta, seeds)
    print(f"start (imitation): {best_time:.2f}s", flush=True)
    for generation in range(generations):
        started = time.time()
        noise = rng.normal(0, 1, (pairs, theta.size))
        times = []
        for eps in noise:
            times.append(evaluate(theta + sigma * eps, seeds))
            times.append(evaluate(theta - sigma * eps, seeds))
        # Rank-based fitness: robust to a few disastrous (off-road) runs.
        ranks = np.empty(len(times))
        ranks[np.argsort(times)] = np.arange(len(times))
        fitness = 0.5 - ranks / (len(times) - 1)  # fastest gets +0.5
        gradient = sum(
            (fitness[2 * i] - fitness[2 * i + 1]) * noise[i] for i in range(pairs)
        )
        theta = theta + lr / (2 * pairs * sigma) * gradient
        current = evaluate(theta, seeds)
        if current < best_time:
            best_vector, best_time = theta.copy(), current
            save(unflatten(best_vector), "evolved.json", {"generation": generation, "time": best_time})
        print(
            f"gen {generation}: mean {current:.2f}s, best candidate {min(times):.2f}s, "
            f"best so far {best_time:.2f}s ({time.time() - started:.0f}s)",
            flush=True,
        )
    if not (WEIGHTS / "evolved.json").exists():
        save(unflatten(best_vector), "evolved.json", {"generation": -1, "time": best_time})


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "imitation"
    if what == "imitation":
        train_imitation()
    elif what == "evolve":
        train_evolution()
    else:
        sys.exit(__doc__)
