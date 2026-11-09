"""Browser entry point for pygbag.

pygbag needs a ``main.py`` with an async game loop. web/build.sh copies this
file next to src/, assets/ and ghosts/, so the game finds its files exactly as
it does on the desktop.
"""

import asyncio
import importlib.util
import sys
from pathlib import Path

import pygame  # noqa: F401  (tells pygbag to bundle pygame)

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

# The game file's name starts with a digit, so it can't be a normal import.
spec = importlib.util.spec_from_file_location("game", SRC / "3D-game.py")
game = importlib.util.module_from_spec(spec)
spec.loader.exec_module(game)

asyncio.run(game.main())
