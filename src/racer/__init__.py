"""Self-Driving Racer: a pseudo-3D racer where self-driving algorithms race one lap.

Modules, from the bottom up:

    settings   every tunable number
    track      the road, its bends, hills and features, and the AI speed plan
    physics    speed, slide, surfaces and bumps, shared by every car
    drivers    the self-driving algorithms
    race       cars, the built-in AI, one physics step, headless runs
    ghost      replay of the fastest run
    sprites, render, minimap, hud, panels   drawing
    app        the window and main loop
"""
