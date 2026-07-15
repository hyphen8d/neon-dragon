# Playtest driver

Drives `main.py` end-to-end through scripted-but-reactive persona
playthroughs, so you can review a full transcript afterward instead of
(or in addition to) playing it by hand.

## Why this exists

`engine/ui.py`'s `read_key()` already has a documented non-tty fallback
for exactly this: piped stdin is read line-by-line instead of raw
single-keystroke, so a subprocess talking to `main.py` over plain pipes
works without any special terminal emulation. `driver.py` is a thin
expect/send layer on top of that: it sends a hotkey or answer, waits for
the specific text that means the game is blocked on the *next* input, and
repeats. See the module docstring in `driver.py` for the two non-obvious
gotchas (bracket-hotkey text splitting, and the single-character
`read_key()` limit) baked into how it matches text.

## Running it

```
source .venv/bin/activate   # or: .venv/bin/python3 directly
python3 tools/playtest/run_all.py
```

Runs all three personas back to back and prints a one-line pass/fail per
persona. Transcripts land in `tools/playtest/logs/<persona>.log`
(gitignored) — read the log, not just the pass/fail line, to see what
actually happened (combat rounds, prices, contract text, market rotation).

Run a single persona directly for faster iteration:

```
python3 tools/playtest/rook.py
```

## Personas

- **rook.py** — cautious first-timer, Street Samurai. Reads help first,
  banks credits, plays safe fights, checks status often.
- **ghost.py** — reckless glass-cannon, Netrunner. Dives into Undercity
  immediately, pokes at edge cases (insufficient funds, the undocumented
  Black Market hotkey, an intentionally-mismatched Pit fight).
- **wrench.py** — completionist, Street Samurai. Grinds RoboDOJO training,
  chases contracts and Pit tiers, plays the most in-game days.

Each exposes a `run() -> bool` function and a `NAME` constant (the
persona's save-slug source), so `run_all.py` can drive them without
shelling out. Persona names are prefixed with `"0"` so they always sort
first in the "Load Merc" list — not a style choice, see `driver.py`'s
`save_slug_index()` docstring for why that specifically matters.

## Adding a persona

Copy `rook.py` as a starting point. Use the `visit_*` helpers in
`driver.py` for each hub location; `run_combat_loop` handles a fight to
resolution (win/loss/flee) including any level-up prompts. Keep new
personas playing 1-3 in-game days — enough to exercise the daily reset
(training cap, market rotation, Faction Heat) without ballooning runtime.

## Multi-digit selection bug — now fixed

`read_key()` (`engine/ui.py`) used to only ever consume the first
character of an input line, on a real terminal *and* in the piped
fallback this driver relies on, so no menu with 10+ selectable items (a
shop list, a save list) could have its 10th+ entry chosen. This is what
this driver's `save_slug_index()` was originally working around. As of
the `read_choice()`/`read_line()` split in `engine/ui.py`, numbered lists
with any two-digit choice now read a full Enter-confirmed line instead,
while hotkey-only menus (combat, hub nav, Y/N) are untouched. The
`save_slug_index()` workaround is left in place here since it's still a
harmless, cheap way to guarantee a low-digit index regardless of how many
saves exist -- not because it's load-bearing anymore.
