"""Vehicle physics shared by every car: speed, sideways slide, surfaces and bumps."""

from .settings import (
    ACCELERATION,
    BOOST_ACCELERATION,
    BOOST_FADE,
    BOOST_MAX_SPEED,
    BRAKE_DECELERATION,
    BUMP_BOUNCE,
    BUMP_SIDE_KICK,
    CAR_LENGTH,
    CAR_WIDTH,
    COAST_DECELERATION,
    DRIFT_RESPONSE_FAST,
    DRIFT_RESPONSE_SLOW,
    HANDLING_REFERENCE_SPEED,
    KERB_DECELERATION,
    KERB_MAX_SPEED,
    KERB_WIDTH,
    MAX_SPEED,
    MUD_DECELERATION,
    MUD_GRIP,
    MUD_MAX_SPEED,
    MUD_SLIP,
    OFF_ROAD_DECELERATION,
    OFF_ROAD_MAX_SPEED,
    PLAYER_LATERAL_SPEED,
    ROAD_CURVE_DRIFT_SPEED,
    STEERING_GRIP_FALLOFF,
    WANDER_INTERVAL,
    WANDER_RESPONSE,
    WANDER_STRENGTH,
)
from .track import track_gap


def surface_drag(player_x):
    """Extra deceleration and the speed it pulls down to, by road zone.

    ``player_x`` is in road half-widths: the asphalt ends at 1 and the kerb
    runs to ``1 + KERB_WIDTH``. Beyond that is grass.
    """
    distance = abs(player_x)
    if distance <= 1:
        return 0.0, MAX_SPEED
    if distance <= 1 + KERB_WIDTH:
        return KERB_DECELERATION, KERB_MAX_SPEED
    return OFF_ROAD_DECELERATION, OFF_ROAD_MAX_SPEED


def move_speed(speed, throttle, brake, player_x, dt, boosting=False, on_mud=False):
    """Accelerate or brake while keeping forward speed within its limits.

    Kerb, grass and mud drag only pull speed down to their limit, so the
    throttle can still crawl the car out. A boost pushes on top of the throttle
    and lifts the top speed; afterwards the extra speed fades instead of
    vanishing at once.
    """
    top_speed = BOOST_MAX_SPEED if boosting else MAX_SPEED
    if throttle:
        # The engine alone never pushes past the normal top speed; only a
        # boost does. (Without this check, holding the throttle out-pushed the
        # fade below and kept a boost's extra speed forever. The evolved
        # driver found and exploited exactly that.)
        if speed < top_speed:
            speed = min(top_speed, speed + ACCELERATION * dt)
    else:
        speed -= COAST_DECELERATION * dt
    speed -= brake * BRAKE_DECELERATION * dt
    if boosting:
        speed += BOOST_ACCELERATION * dt

    drag, limit = surface_drag(player_x)
    if on_mud and limit > MUD_MAX_SPEED:
        drag, limit = MUD_DECELERATION, MUD_MAX_SPEED
    if speed > limit:
        speed = max(limit, speed - drag * dt)
    if speed > top_speed:
        speed = max(top_speed, speed - BOOST_FADE * dt)
    return max(0.0, min(speed, BOOST_MAX_SPEED))


def update_wander(wander, wander_target, rng, dt):
    """Ease the slippery push toward a target that changes now and then.

    Easing, rather than jumping, keeps the car drifting in smooth arcs.
    """
    if rng.random() < dt / WANDER_INTERVAL:
        wander_target = rng.uniform(-1.0, 1.0)
    wander += (wander_target - wander) * min(1.0, WANDER_RESPONSE * dt)
    return wander, wander_target


def move_sideways(
    player_x, drift_speed, steering, road_curve, speed, wander, dt, on_mud=False
):
    """Move a car relative to the road while preserving a straight world heading.

    The player and the AI racers both drive through this, so they face exactly
    the same handling.

    Three effects fight the driver. Steering grows sharper with speed, so a
    tap at the top end moves the car a long way. Cornering load grows with the
    square of speed, the way real centrifugal force does. And the car carries
    sideways momentum: ``drift_speed`` chases the wheel instead of matching it,
    and chases it more lazily as speed rises, so a fast car is late into a
    slide and keeps sliding after the key is released.
    """
    speed_ratio = speed / HANDLING_REFERENCE_SPEED
    # Past the normal top speed (boosting) handling stays as it is at the top.
    speed_fraction = min(1.0, speed / MAX_SPEED)
    grip = 1.0 - STEERING_GRIP_FALLOFF * speed_fraction
    target_speed = steering * PLAYER_LATERAL_SPEED * speed_ratio * grip
    response = DRIFT_RESPONSE_SLOW + (
        DRIFT_RESPONSE_FAST - DRIFT_RESPONSE_SLOW
    ) * speed_fraction
    slip = 1.0
    if on_mud:
        # Mud: the wheel barely bites and the slide is slow to answer it.
        target_speed *= MUD_GRIP
        response *= MUD_GRIP
        slip = MUD_SLIP
    drift_speed += (target_speed - drift_speed) * min(1.0, response * dt)
    # The surface pushes the slide too, so the car wanders even on a straight.
    drift_speed += wander * WANDER_STRENGTH * slip * speed_fraction * dt
    road_turn_speed = road_curve * ROAD_CURVE_DRIFT_SPEED * speed_ratio**2
    return player_x + (drift_speed - road_turn_speed) * dt, drift_speed


def collide(speed_a, speed_b, mass_a, mass_b):
    """New speeds after two bodies meet in a line.

    Each body's change is set by the *other* body's share of the total mass, so
    the heavier one is pushed less. BUMP_BOUNCE runs from 0 (they stick) to 1
    (a perfect rebound).
    """
    closing = speed_a - speed_b
    total = mass_a + mass_b
    return (
        speed_a - (1 + BUMP_BOUNCE) * mass_b / total * closing,
        speed_b + (1 + BUMP_BOUNCE) * mass_a / total * closing,
    )


def bump(a, b, track_length):
    """Resolve contact between two cars; only ``b`` is moved apart."""
    gap_z = track_gap(a.distance, b.distance, track_length)
    gap_x = b.x - a.x
    reach_x = CAR_WIDTH * (a.size + b.size) / 2
    if abs(gap_z) >= CAR_LENGTH or abs(gap_x) >= reach_x:
        return

    # Along the track: only resolve if the cars are closing on each other.
    ahead = 1 if gap_z >= 0 else -1
    if (a.speed - b.speed) * ahead > 0:
        closing = abs(a.speed - b.speed)
        a.speed, b.speed = collide(a.speed, b.speed, a.mass, b.mass)
        a.speed, b.speed = max(0.0, a.speed), max(0.0, b.speed)
        # An off-centre hit also shoves both cars sideways.
        side = 1 if gap_x >= 0 else -1
        kick = BUMP_SIDE_KICK * closing / MAX_SPEED
        total = a.mass + b.mass
        a.drift_speed -= side * kick * b.mass / total
        b.drift_speed += side * kick * a.mass / total
        # Move b just out of contact so one hit is not counted twice.
        b.distance += ahead * CAR_LENGTH - gap_z
    elif (CAR_LENGTH - abs(gap_z)) / CAR_LENGTH < (reach_x - abs(gap_x)) / reach_x:
        # Already pulling apart along the track and barely overlapping that
        # way: just finish separating them.
        b.distance += ahead * CAR_LENGTH - gap_z
    else:
        # Side by side: resolve the sideways speeds the same way.
        side = 1 if gap_x >= 0 else -1
        if (a.drift_speed - b.drift_speed) * side > 0:
            a.drift_speed, b.drift_speed = collide(
                a.drift_speed, b.drift_speed, a.mass, b.mass
            )
        b.x = a.x + side * reach_x


def bump_cars(cars, track_length):
    for index, a in enumerate(cars):
        for b in cars[index + 1 :]:
            bump(a, b, track_length)
