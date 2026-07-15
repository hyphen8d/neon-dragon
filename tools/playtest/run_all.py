"""Runs every persona playthrough and prints a pass/fail summary.

Usage (from the project root, with the venv active):
    python3 tools/playtest/run_all.py

Transcripts land in tools/playtest/logs/<persona>.log (gitignored) --
read them after a run to see exactly what happened, not just whether it
crashed. See README.md in this directory for more context.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from driver import PROJECT_DIR  # noqa: E402

import ghost  # noqa: E402
import rook  # noqa: E402
import wrench  # noqa: E402

PERSONAS = [rook, ghost, wrench]


def _clear_persona_saves() -> None:
    """Each persona's save is fully regenerated every run -- clear stale
    copies first so a leftover save from a previous run (possibly mid-day,
    possibly from a version of this script with different steps) can't be
    silently resumed instead of created fresh."""
    saves_dir = PROJECT_DIR / "saves"
    for persona in PERSONAS:
        path = saves_dir / f"{persona.NAME.lower()}.json"
        path.unlink(missing_ok=True)


def main() -> int:
    _clear_persona_saves()
    results = {persona.__name__: persona.run() for persona in PERSONAS}

    print("\n--- Playtest summary ---")
    for name, ok in results.items():
        print(f"  {name}: {'OK' if ok else 'FAILED'}")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
