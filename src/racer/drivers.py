"""Self-driving algorithms that can drive any car in the racer.

Every driver sees the race through a ``world`` object built by the game and
returns the same three values a keyboard gives: ``(steering, throttle, brake)``
with steering in -1..1, throttle 0 or 1 and brake 0..1. That shared interface
is what lets them race each other fairly.

What a driver may ask the world (see ``World`` in race.py):

    world.state(car)                 -> (distance, x, drift_speed, speed, boost_time)
    world.curve(distance)            -> how hard the road bends there
    world.planned_speed(distance)    -> fastest speed that still makes the bends ahead
    world.feature(distance, x)       -> "boost", "mud" or None at that spot
    world.features_ahead(distance, horizon) -> [(gap, kind, lane_x), ...]
    world.others(car)                -> [(gap, x, speed), ...] for the other cars
    world.step(state, steering, throttle, brake, dt) -> the state a moment later
    world.P                          -> the physics constants

``x`` is the sideways position in road half-widths: 0 is the centre line, the
asphalt ends at +-1 and the three lanes sit at -2/3, 0 and +2/3.
"""

import json
import math
from pathlib import Path

DISTANCE, X, DRIFT, SPEED, BOOST = range(5)
LANES = (-2 / 3, 0.0, 2 / 3)
WEIGHTS_DIR = Path(__file__).resolve().parents[1] / "weights"


def clamp(value, low, high):
    return max(low, min(high, value))


# ---------------------------------------------------------------------------
# Building blocks shared by several drivers
# ---------------------------------------------------------------------------


def wheel_strength(world, speed):
    """How fast (half-widths per second) full steering can slide the car."""
    P = world.P
    speed_ratio = speed / P.HANDLING_REFERENCE_SPEED
    grip = 1.0 - P.STEERING_GRIP_FALLOFF * min(1.0, speed / P.MAX_SPEED)
    return P.PLAYER_LATERAL_SPEED * speed_ratio * grip


def road_push(world, distance, speed):
    """How fast the bend at ``distance`` pushes a car at ``speed`` outward."""
    P = world.P
    speed_ratio = speed / P.HANDLING_REFERENCE_SPEED
    return world.curve(distance) * P.ROAD_CURVE_DRIFT_SPEED * speed_ratio**2


def slide_lag(world, speed):
    """Roughly how many seconds the slide takes to follow the wheel."""
    P = world.P
    fraction = min(1.0, speed / P.MAX_SPEED)
    response = P.DRIFT_RESPONSE_SLOW + (
        P.DRIFT_RESPONSE_FAST - P.DRIFT_RESPONSE_SLOW
    ) * fraction
    return 1.0 / response


def steer_for_slide(world, state, wanted_slide):
    """Steering that makes the car slide sideways at ``wanted_slide`` (relative
    to the road), leaning in advance against the bend it will be in by the time
    the slide has caught up with the wheel."""
    speed = state[SPEED]
    strength = wheel_strength(world, speed)
    if strength <= 0:
        return 0.0
    lead = state[DISTANCE] + speed * slide_lag(world, speed)
    return clamp((wanted_slide + road_push(world, lead, speed)) / strength, -1.0, 1.0)


def pd_steer(world, state, target_x, p_gain=1.5, d_gain=1.0, max_correction=0.6):
    """The baseline's lane keeper: P pulls toward the target, D damps the slide."""
    sliding = state[DRIFT] - road_push(world, state[DISTANCE], state[SPEED])
    correction = p_gain * (target_x - state[X]) - d_gain * sliding
    return steer_for_slide(
        world, state, clamp(correction, -max_correction, max_correction)
    )


BRAKE_LOOK = tuple(range(0, 34000, 2000))  # world units ahead to check


def target_speed(world, distance, caution=1.0):
    """The fastest speed now that can still brake down for every bend ahead.

    The game's speed plan stops at the normal top speed, but a boost pad can
    push a car well past it, and then braking has to start much earlier. So
    apply the braking equation, v_now = sqrt(v_bend**2 + 2 * a * d), to the
    plan at several distances ahead. Where no bend is coming there is no limit
    at all, so a car never brakes away a boost it just got.
    """
    P = world.P
    best = math.inf
    for ahead in BRAKE_LOOK:
        planned = world.planned_speed(distance + ahead)
        if planned < P.MAX_SPEED * 0.999:
            best = min(best, math.sqrt(planned**2 + 2 * P.AI_BRAKING * ahead))
    return best * caution


def pedals(world, speed, wanted_speed):
    """Throttle below the wanted speed, a proportional brake well above it."""
    slack = world.P.AI_BRAKE_SLACK
    if speed < wanted_speed:
        return 1, 0.0
    if speed > wanted_speed + slack:
        return 0, clamp((speed - wanted_speed) / slack - 1, 0.0, 1.0)
    return 0, 0.0


def boost_is_safe(world, pad_distance, speed):
    """A boost keeps pushing for a while and overpowers the brakes, so it only
    helps if no bend arrives before it has worn off (plus room to brake)."""
    P = world.P
    reach = BOOST_REACH_FACTOR * P.BOOST_DURATION * max(speed, P.MAX_SPEED)
    for ahead in range(0, int(reach), 2000):
        if world.planned_speed(pad_distance + ahead) < P.MAX_SPEED * 0.97:
            return False
    return True


BOOST_REACH_FACTOR = 1.6


def choose_lane(world, state, current_lane, others):
    """A small route planner: score each lane over the road ahead and pick the
    cheapest. Mud costs a lot, a boost pad is a reward, a slower car in the way
    costs some, and changing lanes costs a little so the car does not weave."""
    speed = max(state[SPEED], 0.3 * world.P.MAX_SPEED)
    horizon = speed * 1.6
    features = world.features_ahead(state[DISTANCE], horizon)
    best_lane, best_cost = current_lane, math.inf
    for lane in LANES:
        cost = 0.4 * abs(lane - state[X]) + (0.0 if lane == current_lane else 0.6)
        for gap, kind, lane_x in features:
            if abs(lane_x - lane) < 0.01:
                # Things very close are hard to reach in time; weight them less.
                reach = clamp(gap / (speed * 0.35), 0.2, 1.0)
                if kind == "mud":
                    cost += reach * 10.0
                elif boost_is_safe(world, state[DISTANCE] + gap, speed):
                    cost -= reach * 3.0
                else:
                    cost += reach * 6.0  # it would shove us into a bend
        for gap, x, other_speed in others:
            if 0 < gap < horizon and abs(x - lane) < 0.45 and other_speed < state[SPEED]:
                cost += 5.0
        if cost < best_cost:
            best_lane, best_cost = lane, cost
    return best_lane


class Driver:
    name = "Driver"
    family = ""
    inspired_by = ""

    def reset(self):
        pass

    def drive(self, world, car):
        raise NotImplementedError


# ---------------------------------------------------------------------------
# 1. Pure Pursuit: chase a point on the path ahead (geometric path tracking)
# ---------------------------------------------------------------------------


class PurePursuit(Driver):
    """Aim at a point a lookahead distance ahead on the planned path.

    Classic pure pursuit picks the circle arc through the car and the
    lookahead point; its curvature is 2 * error / lookahead**2. In this game's
    road-relative model that becomes a wanted sideways slide of
    2 * error / (time to reach the point). The lookahead grows with speed, the
    usual "velocity-scheduled" variant: short and sharp when slow, long and
    smooth when fast.
    """

    name = "Pure Pursuit"
    family = "Geometric path tracking"
    inspired_by = "CMU, 1992; still a standard baseline in F1TENTH racing"

    LOOKAHEAD_TIME = 0.55  # seconds of travel
    MIN_LOOKAHEAD = 900.0  # world units

    def reset(self):
        self.lane = None

    def drive(self, world, car):
        state = world.state(car)
        others = world.others(car)
        if self.lane is None:
            self.lane = min(LANES, key=lambda lane: abs(lane - state[X]))
        self.lane = choose_lane(world, state, self.lane, others)

        speed = state[SPEED]
        throttle, brake = pedals(world, speed, target_speed(world, state[DISTANCE]))
        if speed < 1.0:
            return 0.0, throttle, brake
        lookahead = max(self.MIN_LOOKAHEAD, speed * self.LOOKAHEAD_TIME)
        time_to_point = lookahead / speed
        # Where the car would be at the lookahead point if it kept sliding as
        # it is now (relative to the road, which bends away under it).
        sliding = state[DRIFT] - road_push(world, state[DISTANCE], speed)
        error = self.lane - (state[X] + sliding * time_to_point)
        wanted_slide = clamp(2.0 * error / time_to_point, -0.8, 0.8)
        return steer_for_slide(world, state, wanted_slide), throttle, brake


# ---------------------------------------------------------------------------
# 2. Stanley: fix the heading, then the sideways error, at the front axle
# ---------------------------------------------------------------------------


class Stanley(Driver):
    """Steer to cancel the heading error plus atan(k * error / speed).

    This is the controller of Stanford's car "Stanley", winner of the 2005
    DARPA Grand Challenge. It looks at the error right at the front axle rather
    than at a point ahead, and the atan term makes it gentle at speed and firm
    when slow.
    """

    name = "Stanley"
    family = "Geometric path tracking"
    inspired_by = "Stanford, DARPA Grand Challenge 2005 (the team behind Google's, now Waymo's, first cars)"

    GAIN = 2.5  # k: how hard the sideways error is corrected
    SOFTENING = 2000.0  # keeps atan sane near zero speed

    def reset(self):
        self.lane = None

    def drive(self, world, car):
        state = world.state(car)
        others = world.others(car)
        if self.lane is None:
            self.lane = min(LANES, key=lambda lane: abs(lane - state[X]))
        self.lane = choose_lane(world, state, self.lane, others)

        speed = state[SPEED]
        throttle, brake = pedals(world, speed, target_speed(world, state[DISTANCE]))
        if speed < 1.0:
            return 0.0, throttle, brake
        half_width = world.P.ROAD_WIDTH
        # Heading relative to the lane: sideways speed over forward speed.
        sliding = state[DRIFT] - road_push(world, state[DISTANCE], speed)
        heading = math.atan2(sliding * half_width, speed)
        error = (self.lane - state[X]) * half_width
        wanted_heading = -heading + math.atan2(self.GAIN * error, speed + self.SOFTENING)
        # Turn the wanted heading change back into a wanted slide.
        wanted_slide = math.tan(clamp(heading + wanted_heading, -0.5, 0.5)) * speed / half_width
        return steer_for_slide(world, state, clamp(wanted_slide, -0.8, 0.8)), throttle, brake


# ---------------------------------------------------------------------------
# 3. MPC planner: imagine several futures with the physics model, pick the best
# ---------------------------------------------------------------------------


class MPCPlanner(Driver):
    """Model-predictive planning by sampling, the "predict, plan, check" idea.

    Every PLAN_EVERY steps it imagines each candidate plan (a sideways target
    and a level of caution) for HORIZON seconds with the game's own physics,
    including boost pads, mud and where the other cars will be, scores the
    imagined futures, and commits to the best one until the next re-plan.
    This is receding-horizon control: plan far, act a little, plan again.
    Real stacks (Waymo, Apollo) solve a much richer version of this, with
    learned predictions of other road users and a safety check on the chosen
    trajectory before it is driven.
    """

    name = "MPC Planner"
    family = "Model-predictive control (sampling-based)"
    inspired_by = "Modular planners in Waymo / Apollo stacks; MPPI and MPC in racing research"

    TARGETS = (-0.8, -2 / 3, -1 / 3, 0.0, 1 / 3, 2 / 3, 0.8)
    CAUTIONS = (1.0, 0.92)
    HORIZON = 2.5  # seconds imagined ahead
    MODEL_DT = 0.1  # coarse steps keep the imagining cheap
    PLAN_EVERY = 10  # physics steps between re-plans (1/6 s)

    def reset(self):
        self.plan = None
        self.countdown = 0

    def rollout(self, world, state, others, target_x, caution):
        P = world.P
        cost = 0.0
        start = state[DISTANCE]
        t = 0.0
        steps = int(self.HORIZON / self.MODEL_DT)
        for _ in range(steps):
            steer = pd_steer(world, state, target_x)
            throttle, brake = pedals(
                world, state[SPEED], target_speed(world, state[DISTANCE], caution)
            )
            state = world.step(state, steer, throttle, brake, self.MODEL_DT)
            t += self.MODEL_DT
            off = abs(state[X])
            if off > 1.0:
                cost += 3000.0 * (off - 1.0 + 0.2)
            if world.feature(state[DISTANCE], state[X]) == "mud":
                cost += 250.0  # the model has no slip noise; mud is worse than it thinks
            for gap, x, other_speed in others:
                ahead = gap + other_speed * t - (state[DISTANCE] - start)
                if abs(ahead) < P.CAR_LENGTH * 1.3 and abs(x - state[X]) < P.CAR_WIDTH * 1.2:
                    cost += 1500.0
        # Arriving faster than the bends allow will cost time later.
        overspeed = state[SPEED] - target_speed(world, state[DISTANCE])
        if overspeed > 0:
            cost += 0.5 * overspeed
        return (state[DISTANCE] - start) - cost

    def replan(self, world, car):
        state = world.state(car)
        others = [o for o in world.others(car) if -2000 < o[0] < 12000]
        best, best_score = None, -math.inf
        for target_x in self.TARGETS:
            for caution in self.CAUTIONS:
                score = self.rollout(world, state, others, target_x, caution)
                # A small preference for the current plan avoids dithering.
                if self.plan == (target_x, caution):
                    score += 30.0
                if score > best_score:
                    best, best_score = (target_x, caution), score
        return best

    def drive(self, world, car):
        if self.plan is None or self.countdown <= 0:
            self.plan = self.replan(world, car)
            self.countdown = self.PLAN_EVERY
        self.countdown -= 1
        target_x, caution = self.plan
        state = world.state(car)
        throttle, brake = pedals(
            world, state[SPEED], target_speed(world, state[DISTANCE], caution)
        )
        return pd_steer(world, state, target_x), throttle, brake

    def label(self, world, car):
        """The expert's action for a state, used to teach the imitation driver."""
        self.plan = self.replan(world, car)
        self.countdown = self.PLAN_EVERY
        return self.drive(world, car)


# ---------------------------------------------------------------------------
# 4 & 5. Neural network drivers: learned instead of hand-written
# ---------------------------------------------------------------------------

LOOK_DISTANCES = (0.0, 1500.0, 3000.0, 6000.0, 10000.0)
FEATURE_VIEW = 8000.0
INPUTS = 4 + len(LOOK_DISTANCES) + 1 + 2 * len(LANES)
HIDDEN = 24


def observe(world, car):
    """What the network sees: a fixed list of numbers, roughly in -1..1."""
    state = world.state(car)
    P = world.P
    distance, speed = state[DISTANCE], state[SPEED]
    obs = [
        state[X],
        state[DRIFT],
        speed / P.MAX_SPEED,
        1.0 if state[BOOST] > 0 else 0.0,
    ]
    obs += [world.curve(distance + d) / 3.0 for d in LOOK_DISTANCES]
    obs.append(min(1.0, world.planned_speed(distance + speed * 0.8) / P.MAX_SPEED))
    nearest = {}
    for gap, kind, lane_x in world.features_ahead(distance, FEATURE_VIEW):
        key = (kind, lane_x)
        nearest[key] = min(nearest.get(key, FEATURE_VIEW), gap)
    for lane in LANES:
        for kind in ("mud", "boost"):
            gap = min(
                (g for (k, l), g in nearest.items() if k == kind and abs(l - lane) < 0.01),
                default=FEATURE_VIEW,
            )
            obs.append(1.0 - gap / FEATURE_VIEW)
    return obs


def action_from_output(steer_out, pedal_out):
    """Network outputs (both -1..1) to the game's controls."""
    throttle = 1 if pedal_out > 0 else 0
    brake = clamp(-pedal_out, 0.0, 1.0)
    return clamp(steer_out, -1.0, 1.0), throttle, brake


def action_to_target(steering, throttle, brake):
    """The game's controls back to the network's two outputs (for training)."""
    return steering, (1.0 if throttle else -brake)


class TinyNet:
    """A two-layer network in plain Python: inputs -> tanh hidden -> tanh outputs.

    Plain Python (no numpy) so it also runs in the browser build.
    """

    def __init__(self, w1, b1, w2, b2):
        self.w1, self.b1, self.w2, self.b2 = w1, b1, w2, b2

    @classmethod
    def load(cls, path):
        data = json.loads(Path(path).read_text())
        return cls(data["w1"], data["b1"], data["w2"], data["b2"])

    def forward(self, inputs):
        hidden = [
            math.tanh(b + sum(w * i for w, i in zip(row, inputs)))
            for row, b in zip(self.w1, self.b1)
        ]
        return [
            math.tanh(b + sum(w * h for w, h in zip(row, hidden)))
            for row, b in zip(self.w2, self.b2)
        ]


class NeuralDriver(Driver):
    weights_file = ""

    def __init__(self):
        path = WEIGHTS_DIR / self.weights_file
        self.net = TinyNet.load(path) if path.exists() else None

    def drive(self, world, car):
        if self.net is None:
            return 0.0, 0, 0.0  # untrained: sits still, so it shows up as DNF
        steer_out, pedal_out = self.net.forward(observe(world, car))
        return action_from_output(steer_out, pedal_out)


class ImitationNN(NeuralDriver):
    """Behaviour cloning: a network trained to copy an expert's actions.

    Tesla's FSD v12+ is the famous large-scale version: one network trained
    on video of human driving, going straight from cameras to controls. Here
    the expert is the MPC Planner, and training uses DAgger: the student drives,
    the expert says what it would have done in the states the student actually
    reached, and the network learns from those corrections too. Without that,
    a copycat drifts into states the expert never visited and has no idea what
    to do there.
    """

    name = "Imitation NN"
    family = "Imitation learning (behaviour cloning + DAgger)"
    inspired_by = "Tesla FSD v12+ end-to-end networks; NVIDIA PilotNet (2016)"
    weights_file = "imitation.json"


class EvolvedNN(NeuralDriver):
    """The same network shape, improved by evolution instead of copying.

    Start from the imitation network, make many slightly mutated copies, race
    them, keep the fastest, repeat. Nobody tells it what the right action is;
    it only ever sees its lap time. That trial-and-error signal is the core
    idea of reinforcement learning, here in its simplest, gradient-free form
    (an evolution strategy).
    """

    name = "Evolved NN"
    family = "Neuroevolution (evolution strategy, reinforcement-style)"
    inspired_by = "OpenAI evolution strategies (2017); NEAT; imitation-then-RL pipelines"
    weights_file = "evolved.json"


# The baseline lives in the game file (ai_driver); it is listed here so every
# algorithm has one entry with its description.
ALGORITHMS = (
    "Baseline",
    "Pure Pursuit",
    "Stanley",
    "MPC Planner",
    "Imitation NN",
    "Evolved NN",
)
DRIVER_CLASSES = {
    cls.name: cls for cls in (PurePursuit, Stanley, MPCPlanner, ImitationNN, EvolvedNN)
}


def make_driver(name):
    """A fresh driver for one car, or None for the game's built-in baseline."""
    cls = DRIVER_CLASSES.get(name)
    if cls is None:
        return None
    driver = cls()
    driver.reset()
    return driver
