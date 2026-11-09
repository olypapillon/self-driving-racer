"""Play the racer:

    uv run python src/game.py
"""

import asyncio

from racer.app import main

if __name__ == "__main__":
    asyncio.run(main())
