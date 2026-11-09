"""Browser entry point for pygbag.

pygbag needs a ``main.py`` with an async game loop. web/build.sh copies this
file next to src/, assets/ and ghosts/, so the game finds its files exactly as
it does on the desktop.
"""

import asyncio
import sys
from pathlib import Path

import pygame  # noqa: F401  (tells pygbag to bundle pygame)

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from racer.app import main  # noqa: E402

asyncio.run(main())
