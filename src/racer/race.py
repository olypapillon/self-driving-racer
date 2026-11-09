"""A race: the cars, the built-in AI, one fixed physics step, and headless runs."""

import random
from dataclasses import dataclass, field
from types import SimpleNamespace

import pygame

from . import drivers
from .drivers import ALGORITHMS
from .physics import bump_cars, move_sideways, move_speed, update_wander
from .settings import (
    AI_BRAKE_SLACK,
    AI_BRAKING,
    AI_FOLLOW_GAIN,
    AI_FOLLOW_GAP,
    AI_LANE_MARGIN,
    AI_LANE_SWITCH_MARGIN,
    AI_MAX_CORRECTION,
    AI_MERGE_CLEARANCE,
    AI_STEER_D,
    AI_STEER_P,
    AI_TRAFFIC_VIEW,
    ALGORITHM_COLORS,
    BOOST_DURATION,
    CAR_LENGTH,
    CAR_WIDTH,
    COUNTDOWN_SECONDS,
    DRIFT_RESPONSE_FAST,
    DRIFT_RESPONSE_SLOW,
    FIXED_STEP,
    GRID_ROW_GAP,
    HANDLING_REFERENCE_SPEED,
    KERB_WIDTH,
    LANES_X,
    MAX_SPEED,
    MINIMAP_PLAYER_COLOR,
    PLAYER_LATERAL_SPEED,
    PLAYER_MASS,
    RACE_LAPS,
    RACER_SEED,
    ROAD_CURVE_DRIFT_SPEED,
    ROAD_WIDTH,
    SEGMENT_LENGTH,
    STEERING_GRIP_FALLOFF,
    TRACK_FEATURES,
    TRAFFIC_COLOR,
    TRAFFIC_COUNT,
    TRAFFIC_DRIFT_DAMPING,
    TRAFFIC_LANE_CHANGE_INTERVAL,
    TRAFFIC_LANE_RESPONSE,
    TRAFFIC_MAX_MASS,
    TRAFFIC_MAX_SPEED,
    TRAFFIC_MIN_MASS,
    TRAFFIC_MIN_SPEED,
    TRAFFIC_SEED,
    TRAFFIC_SPEED_RECOVERY,
    WANDER_SEED,
)
from .sprites import build_car_image
from .track import (
    build_features,
    build_speed_plan,
    build_track,
    feature_at,
    planned_speed,
    road_curve_at,
    track_gap,
)

# The physics constants handed to the self-driving algorithms (World.P).
PHYSICS = SimpleNamespace(
    MAX_SPEED=MAX_SPEED,
    HANDLING_REFERENCE_SPEED=HANDLING_REFERENCE_SPEED,
    STEERING_GRIP_FALLOFF=STEERING_GRIP_FALLOFF,
    PLAYER_LATERAL_SPEED=PLAYER_LATERAL_SPEED,
    ROAD_CURVE_DRIFT_SPEED=ROAD_CURVE_DRIFT_SPEED,
    DRIFT_RESPONSE_SLOW=DRIFT_RESPONSE_SLOW,
    DRIFT_RESPONSE_FAST=DRIFT_RESPONSE_FAST,
    AI_BRAKE_SLACK=AI_BRAKE_SLACK,
    AI_BRAKING=AI_BRAKING,
    BOOST_DURATION=BOOST_DURATION,
    ROAD_WIDTH=ROAD_WIDTH,
    CAR_LENGTH=CAR_LENGTH,
    CAR_WIDTH=CAR_WIDTH,
)


@dataclass
class Car:
    """Anything driving on the track: the player, an AI racer, or slow traffic.

    ``distance`` is how far the car has driven from the start line and is never
    wrapped, so ``distance // track_length`` counts its finished laps and the
    grid can start at a negative distance, just behind the line.
    """

    name: str
    driver: str  # "player", "racer" or "traffic"
    distance: float
    x: float
    mass: float
    size: float
    color: tuple
    image: pygame.Surface
    rng: random.Random
    speed: float = 0.0
    drift_speed: float = 0.0
    target_x: float = 0.0
    steering: float = 0.0
    skill: float = 1.0
    cruise_speed: float = 0.0
    wander: float = 0.0
    wander_target: float = 0.0
    boost_time: float = 0.0
    surface: str | None = None  # "boost" or "mud" under the car, else None
    algorithm: str = "Baseline"
    brain: object = None  # a drivers.Driver, or None for the built-in baseline
    # Race statistics, for the leaderboard.
    mud_time: float = 0.0
    grass_time: float = 0.0
    boosts: int = 0
    # Lap bookkeeping, timed on the race clock. ``laps`` is -1 on the grid.
    laps: int = -1
    lap_start: float | None = None
    last_lap: float | None = None
    best_lap: float | None = None
    finish_time: float | None = None


@dataclass
class Race:
    cars: list
    player: Car
    speed_plan: tuple
    countdown: float = COUNTDOWN_SECONDS
    clock: float = 0.0
    # Physics steps since GO, and the player's (distance, x) after each one;
    # recording[0] is the grid position. A finished recording becomes a ghost.
    steps: int = 0
    recording: list = field(default_factory=list)
    features: list = field(default_factory=list)  # per segment, see build_features
    mode: str = "Battle"
    world: object = None


def build_race(car_image, track, algorithm="Baseline", mode="Battle", seed=0):
    """A fresh race for the player's car, driven by ``algorithm``.

    Battle: every other algorithm races too, on a grid shuffled by ``seed``,
    with slow traffic on the road. Time trial: the player's car alone.
    The player is first in ``cars``. Bumps only ever move the second car of a
    pair, so the camera car is never teleported.
    """
    track_length = len(track) * SEGMENT_LENGTH
    player = Car(
        name=algorithm,
        driver="player",
        distance=0.0,
        x=0.0,
        mass=PLAYER_MASS,
        size=1.0,
        color=MINIMAP_PLAYER_COLOR,
        image=car_image,
        rng=random.Random(WANDER_SEED + 1000 * seed),
        algorithm=algorithm,
        brain=drivers.make_driver(algorithm),
    )
    racers = []
    traffic = []
    if mode == "Battle":
        rivals = [name for name in ALGORITHMS if name != algorithm]
        random.Random(RACER_SEED + seed).shuffle(rivals)
        for index, name in enumerate(rivals):
            color = ALGORITHM_COLORS[name]
            racers.append(
                Car(
                    name=name,
                    driver="racer",
                    distance=0.0,
                    x=0.0,
                    mass=PLAYER_MASS,
                    size=1.0,
                    color=color,
                    image=build_car_image(car_image, color, PLAYER_MASS),
                    rng=random.Random(WANDER_SEED + 1000 * seed + 1 + index),
                    algorithm=name,
                    brain=drivers.make_driver(name),
                )
            )
        rng = random.Random(TRAFFIC_SEED + seed)
        for index in range(TRAFFIC_COUNT):
            mass = rng.uniform(TRAFFIC_MIN_MASS, TRAFFIC_MAX_MASS)
            speed = rng.uniform(TRAFFIC_MIN_SPEED, TRAFFIC_MAX_SPEED)
            lane = rng.choice(LANES_X)
            traffic.append(
                Car(
                    name="Traffic",
                    driver="traffic",
                    distance=track_length * (index + 1) / (TRAFFIC_COUNT + 1),
                    x=lane,
                    target_x=lane,
                    mass=mass,
                    # Bigger with mass, but gently: a cube root keeps 1.6x mass
                    # about 1.2x wider rather than 1.6x.
                    size=mass ** (1 / 3),
                    color=TRAFFIC_COLOR,
                    image=build_car_image(car_image, TRAFFIC_COLOR, mass),
                    rng=rng,
                    speed=speed,
                    cruise_speed=speed,
                )
            )

    # Fill the grid two by two from the front; the player starts last. In a
    # time trial the player is alone, so it starts on the front row.
    grid = racers + [player]
    for slot, car in enumerate(grid):
        car.distance = -CAR_LENGTH - (slot // 2) * GRID_ROW_GAP
        car.x = car.target_x = LANES_X[0] if slot % 2 else LANES_X[2]

    race = Race(
        cars=[player] + racers + traffic,
        player=player,
        speed_plan=build_speed_plan(track),
        features=build_features(track),
        recording=[(player.distance, player.x)],
        mode=mode,
    )
    race.world = World(race, track, track_length)
    return race


class World:
    """What the self-driving algorithms in drivers.py are allowed to know.

    Keeping this the only door into the game means every algorithm sees the
    same information, and a new algorithm never needs game internals.
    """

    def __init__(self, race, track, track_length):
        self.race = race
        self.track = track
        self.track_length = track_length
        self.P = PHYSICS

    @staticmethod
    def state(car):
        return (car.distance, car.x, car.drift_speed, car.speed, car.boost_time)

    def curve(self, distance):
        return road_curve_at(self.track, distance % self.track_length)

    def planned_speed(self, distance):
        return planned_speed(self.race.speed_plan, distance % self.track_length)

    def feature(self, distance, x):
        return feature_at(self.race.features, distance, x)

    def features_ahead(self, distance, horizon):
        """Pads and mud whose start is within ``horizon`` ahead (0 if already on)."""
        z = distance % self.track_length
        found = []
        for kind, first, count, lane_x in TRACK_FEATURES:
            start = first * SEGMENT_LENGTH
            end = (first + count) * SEGMENT_LENGTH
            if start <= z < end:
                gap = 0.0
            else:
                gap = (start - z) % self.track_length
            if gap < horizon:
                found.append((gap, kind, lane_x))
        return found

    def others(self, car):
        return [
            (track_gap(car.distance, other.distance, self.track_length), other.x, other.speed)
            for other in self.race.cars
            if other is not car
        ]

    def step(self, state, steering, throttle, brake, dt):
        """The game's physics for one step, minus the random wander."""
        distance, x, drift, speed, boost_time = state
        surface = feature_at(self.race.features, distance, x)
        if surface == "boost":
            boost_time = BOOST_DURATION
        on_mud = surface == "mud"
        speed = move_speed(speed, throttle, brake, x, dt, boost_time > 0, on_mud)
        boost_time = max(0.0, boost_time - dt)
        distance += speed * dt
        x, drift = move_sideways(
            x, drift, steering, self.curve(distance), speed, 0.0, dt, on_mud
        )
        return (distance, x, drift, speed, boost_time)


def free_road(car, cars, lane_x, clearance, track_length):
    """How clear ``lane_x`` is ahead of ``car``, and the car in the way.

    ``clearance`` also counts cars this far behind as in the way: moving into
    another lane needs space beside us as well as in front.
    """
    nearest, blocker = AI_TRAFFIC_VIEW, None
    for other in cars:
        if other is car:
            continue
        gap = track_gap(car.distance, other.distance, track_length)
        reach = CAR_WIDTH * (car.size + other.size) / 2 + AI_LANE_MARGIN
        if -clearance < gap < nearest and abs(other.x - lane_x) < reach:
            nearest, blocker = max(0.0, gap), other
    return nearest, blocker


def ai_driver(car, race, track, track_length):
    """Decide steering, throttle and brake, the same three values a player gives.

    Pick the clearest lane, aim for the fastest speed that still makes the bends
    ahead, and steer with a PD controller toward the lane.
    """
    # Lane: stay put unless a car blocks the way and another lane is clearly
    # better. Ignoring small gains stops the car weaving between lanes.
    cars = race.cars
    free, blocker = free_road(car, cars, car.target_x, 0.0, track_length)
    if blocker is not None:
        for lane_x in LANES_X:
            if lane_x == car.target_x:
                continue
            lane_free, _ = free_road(
                car, cars, lane_x, AI_MERGE_CLEARANCE, track_length
            )
            if lane_free > free + AI_LANE_SWITCH_MARGIN:
                free, car.target_x = lane_free, lane_x
        free, blocker = free_road(car, cars, car.target_x, 0.0, track_length)

    # Speed.
    z = car.distance % track_length
    target_speed = car.skill * planned_speed(race.speed_plan, z)
    if blocker is not None:
        follow_speed = blocker.speed + AI_FOLLOW_GAIN * (free - AI_FOLLOW_GAP)
        target_speed = min(target_speed, max(0.0, follow_speed))
    throttle = brake = 0
    if car.speed < target_speed:
        throttle = 1
    elif car.speed > target_speed + AI_BRAKE_SLACK:
        brake = min(1.0, (car.speed - target_speed) / AI_BRAKE_SLACK - 1)

    # Steering. These mirror the terms in move_sideways.
    speed_ratio = car.speed / HANDLING_REFERENCE_SPEED
    grip = 1.0 - STEERING_GRIP_FALLOFF * car.speed / MAX_SPEED
    wheel_strength = PLAYER_LATERAL_SPEED * speed_ratio * grip
    if wheel_strength <= 0:
        return 0.0, throttle, brake
    push = ROAD_CURVE_DRIFT_SPEED * speed_ratio**2
    road_turn = road_curve_at(track, z) * push
    sideways_speed = car.drift_speed - road_turn
    # P: head toward the lane. D: oppose the sideways speed already there.
    correction = AI_STEER_P * (car.target_x - car.x) - AI_STEER_D * sideways_speed
    correction = max(-AI_MAX_CORRECTION, min(AI_MAX_CORRECTION, correction))
    # The slide takes about 1 / response seconds to follow the wheel, so lean
    # against the push the bend will have by then, not the push it has now.
    response = DRIFT_RESPONSE_SLOW + (
        DRIFT_RESPONSE_FAST - DRIFT_RESPONSE_SLOW
    ) * car.speed / MAX_SPEED
    lead_z = (z + car.speed / response) % track_length
    steering = (road_curve_at(track, lead_z) * push + correction) / wheel_strength
    return max(-1.0, min(1.0, steering)), throttle, brake


def drive(car, track, track_length, steering, throttle, brake, dt, features):
    """Move a player or racer with the shared vehicle physics."""
    car.steering = steering
    previous_surface = car.surface
    car.surface = feature_at(features, car.distance, car.x)
    if car.surface == "boost":
        car.boost_time = BOOST_DURATION
        if previous_surface != "boost" and car.finish_time is None:
            car.boosts += 1
    if car.finish_time is None:
        car.mud_time += dt * (car.surface == "mud")
        car.grass_time += dt * (abs(car.x) > 1 + KERB_WIDTH)
    on_mud = car.surface == "mud"
    car.speed = move_speed(
        car.speed, throttle, brake, car.x, dt, car.boost_time > 0, on_mud
    )
    car.boost_time = max(0.0, car.boost_time - dt)
    car.distance += car.speed * dt
    car.wander, car.wander_target = update_wander(
        car.wander, car.wander_target, car.rng, dt
    )
    car.x, car.drift_speed = move_sideways(
        car.x,
        car.drift_speed,
        steering,
        road_curve_at(track, car.distance % track_length),
        car.speed,
        car.wander,
        dt,
        on_mud,
    )


def drive_traffic(car, dt):
    """Cruise forward, glide toward the chosen lane, and settle after bumps."""
    car.speed += (car.cruise_speed - car.speed) * min(
        1.0, TRAFFIC_SPEED_RECOVERY * dt
    )
    car.distance += car.speed * dt
    if car.rng.random() < dt / TRAFFIC_LANE_CHANGE_INTERVAL:
        car.target_x = car.rng.choice(LANES_X)
    car.drift_speed -= car.drift_speed * min(1.0, TRAFFIC_DRIFT_DAMPING * dt)
    car.x += (car.target_x - car.x) * min(
        1.0, TRAFFIC_LANE_RESPONSE * dt
    ) + car.drift_speed * dt


def count_laps(race, car, track_length):
    """Time a lap each time the car first reaches a new lap.

    Taking the furthest lap reached means a bump that knocks a car back over
    the line cannot count the same lap twice.
    """
    laps = int(car.distance // track_length)
    if laps <= car.laps:
        return
    car.laps = laps
    if car.lap_start is not None:
        lap = race.clock - car.lap_start
        car.last_lap = lap
        car.best_lap = lap if car.best_lap is None else min(car.best_lap, lap)
    car.lap_start = race.clock
    if laps >= RACE_LAPS and car.finish_time is None:
        car.finish_time = race.clock


def standings(race):
    """Player and racers in race order: finishers by time, then by distance."""
    return sorted(
        (car for car in race.cars if car.driver != "traffic"),
        key=lambda car: (
            car.finish_time is None,
            car.finish_time or 0.0,
            -car.distance,
        ),
    )


def update_race(race, track, track_length, controls, dt):
    """One fixed physics step. ``controls`` is the keyboard's (steer, throttle, brake),
    or None when the autopilot drives the player's car.

    Once the player finishes, the AI takes over their car for the lap of honour.
    """
    if race.countdown > 0:
        race.countdown -= dt
        return
    race.clock += dt
    race.steps += 1
    for car in race.cars:
        if car.driver == "traffic":
            drive_traffic(car, dt)
            continue
        if car is race.player and car.finish_time is None and controls is not None:
            steering, throttle, brake = controls
        elif car.brain is not None:
            steering, throttle, brake = car.brain.drive(race.world, car)
        else:
            steering, throttle, brake = ai_driver(car, race, track, track_length)
        drive(car, track, track_length, steering, throttle, brake, dt, race.features)
        count_laps(race, car, track_length)
    bump_cars(race.cars, track_length)
    player = race.player
    # Record every step up to and including the one that crosses the line.
    if player.finish_time is None or player.finish_time == race.clock:
        race.recording.append((round(player.distance, 1), round(player.x, 4)))


def simulate(algorithm, mode="Time trial", seed=0, max_time=90.0, brain=None, on_step=None):
    """Run one race with no window, as fast as the computer allows.

    ``brain`` replaces the player's driver (used when training a network);
    ``on_step(race)`` is called after every physics step. Returns the race.
    """
    if not pygame.get_init():
        pygame.init()
    track = build_track()
    track_length = len(track) * SEGMENT_LENGTH
    race = build_race(pygame.Surface((4, 4), pygame.SRCALPHA), track, algorithm, mode, seed)
    if brain is not None:
        brain.reset()
        race.player.brain = brain
    racers = [car for car in race.cars if car.driver != "traffic"]
    race.countdown = 0.0  # no need to wait for 3-2-1 without a screen
    while race.clock < max_time:
        update_race(race, track, track_length, None, FIXED_STEP)
        if on_step is not None:
            on_step(race)
        if all(car.finish_time is not None for car in racers):
            break
    return race
