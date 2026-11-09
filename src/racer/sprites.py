"""Images built in code: the sky, trees, tinted cars and the ghost, plus a
cache of scaled sprites."""

import math

import pygame

from .settings import (
    CAR_HEAVY_DARKEN,
    CAR_TINT_LIFT,
    GHOST_OPACITY,
    GHOST_TINT,
    SKY_GRADIENT_BIAS,
    SKY_HEIGHT,
    SKY_HORIZON_COLOR,
    SKY_TOP_COLOR,
    SKY_WIDTH,
    SUN_COLOR,
    SUN_GLOW_EXTENT,
    SUN_GLOW_STEPS,
    SUN_HEIGHT_ABOVE_HORIZON,
    SUN_RADIUS,
    SUN_SUPERSAMPLE,
    TRAFFIC_MAX_MASS,
    TRAFFIC_MIN_MASS,
    TREE_CROWN_COLORS,
    TREE_IMAGE_SIZE,
    TREE_TRUNK_COLOR,
)

# Scaled copies of sprites, keyed by (image id, width, height); see blit_scaled.
SCALED_SPRITES = {}
SCALED_SPRITE_LIMIT = 3000


def build_tree_image():
    """Draw one pine tree at startup; every tree on the road is a scaled copy."""
    width, height = TREE_IMAGE_SIZE
    tree = pygame.Surface(TREE_IMAGE_SIZE, pygame.SRCALPHA)
    trunk_width = width // 7
    trunk_height = height // 5
    pygame.draw.rect(
        tree,
        TREE_TRUNK_COLOR,
        (width / 2 - trunk_width / 2, height - trunk_height, trunk_width, trunk_height),
    )

    # Three stacked triangles, each narrower and lighter than the one below.
    crown_bottom = height - trunk_height * 0.6
    layer_height = crown_bottom / 2.2
    for layer, color in enumerate(TREE_CROWN_COLORS):
        base_y = crown_bottom - layer * layer_height * 0.6
        half = width / 2 * (1 - layer * 0.22)
        pygame.draw.polygon(
            tree,
            color,
            [
                (width / 2 - half, base_y),
                (width / 2 + half, base_y),
                (width / 2, base_y - layer_height),
            ],
        )
    return tree.convert_alpha()


def build_ghost_image(car_image):
    """A pale blue, see-through copy of the car."""
    image = pygame.transform.grayscale(car_image)
    image.fill((CAR_TINT_LIFT,) * 3, special_flags=pygame.BLEND_RGB_ADD)
    image.fill(GHOST_TINT, special_flags=pygame.BLEND_RGB_MULT)
    # Scale each pixel's own alpha, so the see-through look survives scaling.
    image.fill((255, 255, 255, GHOST_OPACITY), special_flags=pygame.BLEND_RGBA_MULT)
    return image


def build_car_image(car_image, color, mass):
    """Repaint the player's car: heavier cars come out darker."""
    heaviness = (mass - TRAFFIC_MIN_MASS) / (TRAFFIC_MAX_MASS - TRAFFIC_MIN_MASS)
    shade = 1.0 - CAR_HEAVY_DARKEN * heaviness
    image = pygame.transform.grayscale(car_image)
    # Lift the greys before tinting, or the red body turns out nearly black.
    image.fill((CAR_TINT_LIFT,) * 3, special_flags=pygame.BLEND_RGB_ADD)
    image.fill(
        [round(channel * shade) for channel in color],
        special_flags=pygame.BLEND_RGB_MULT,
    )
    return image


def build_sky():
    """Pre-render the gradient sky and its sun once, at startup.

    The surface is twice the screen wide so it can scroll sideways through
    curves and wrap without a seam, and it is blitted bottom-aligned to the
    horizon so it rises and falls with the road.
    """
    # Some displays (macOS) carry an alpha channel. Making the sky a real alpha
    # surface lets the glow blend into it instead of punching see-through holes
    # that later turn sprite edges black.
    sky = pygame.Surface((SKY_WIDTH, SKY_HEIGHT), pygame.SRCALPHA)
    for y in range(SKY_HEIGHT):
        blend = (y / (SKY_HEIGHT - 1)) ** SKY_GRADIENT_BIAS
        color = [
            round(top + (horizon - top) * blend)
            for top, horizon in zip(SKY_TOP_COLOR, SKY_HORIZON_COLOR)
        ]
        pygame.draw.line(sky, color, (0, y), (SKY_WIDTH, y))

    # Draw the sun oversized and scale it down, so the disc edge and the steps
    # between glow rings are smoothed instead of aliased. The outermost ring
    # must land on alpha zero, or it shows up as a hard arc against the sky.
    span = round(SUN_RADIUS * SUN_GLOW_EXTENT * 2)
    layer = pygame.Surface((span * SUN_SUPERSAMPLE,) * 2, pygame.SRCALPHA)
    layer_center = (span * SUN_SUPERSAMPLE // 2,) * 2
    for step in range(SUN_GLOW_STEPS, 0, -1):
        fade = step / SUN_GLOW_STEPS
        pygame.draw.circle(
            layer,
            (*SUN_COLOR, round(30 * (1 - fade) ** 2)),
            layer_center,
            SUN_RADIUS * (1 + (SUN_GLOW_EXTENT - 1) * fade) * SUN_SUPERSAMPLE,
        )
    pygame.draw.circle(layer, SUN_COLOR, layer_center, SUN_RADIUS * SUN_SUPERSAMPLE)
    layer = pygame.transform.smoothscale(layer, (span, span))

    sun_center = (SKY_WIDTH // 4, SKY_HEIGHT - SUN_HEIGHT_ABOVE_HORIZON)
    sky.blit(layer, layer.get_rect(center=sun_center))
    # Every pixel is opaque now, so drop per-pixel alpha for fast plain copies.
    return sky.convert()


def blit_scaled(screen, image, rect):
    """Draw ``image`` stretched to ``rect``, scaling only the on-screen part.

    A sprite passing the camera can project thousands of pixels tall. Scaling
    just the visible piece keeps the cost under one screen however close it is.
    """
    visible = rect.clip(screen.get_rect())
    if not visible.width or not visible.height:
        return
    if visible == rect:
        # Fully on screen: sprites recur at the same few sizes frame after
        # frame, so keep each scaled copy instead of rescaling it every time.
        key = (id(image), rect.width, rect.height)
        scaled = SCALED_SPRITES.get(key)
        if scaled is None:
            if len(SCALED_SPRITES) > SCALED_SPRITE_LIMIT:
                SCALED_SPRITES.clear()
            scaled = SCALED_SPRITES[key] = pygame.transform.scale(image, rect.size)
        screen.blit(scaled, rect)
        return
    to_image_x = image.get_width() / rect.width
    to_image_y = image.get_height() / rect.height
    source = pygame.Rect(
        int((visible.left - rect.left) * to_image_x),
        int((visible.top - rect.top) * to_image_y),
        max(1, math.ceil(visible.width * to_image_x)),
        max(1, math.ceil(visible.height * to_image_y)),
    ).clip(image.get_rect())
    if not source.width or not source.height:
        return
    screen.blit(pygame.transform.scale(image.subsurface(source), visible.size), visible)


def sprite_rect(image, width, x, y):
    """A rect ``width`` wide with the image's proportions, standing on (x, y)."""
    height = width * image.get_height() / image.get_width()
    if height < 1:
        return None
    rect = pygame.Rect(0, 0, round(width), round(height))
    rect.midbottom = (round(x), round(y))
    return rect
