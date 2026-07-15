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

Each persona now grinds well past the early game (~20-30 in-game days,
several dozen fights) rather than just a 1-3 day smoke test, so a full
`run_all.py` pass takes a couple of minutes, not a few seconds.

Run a single persona directly for faster iteration:

```
python3 tools/playtest/rook.py
```

## Personas

- **rook.py** — cautious first-timer, Street Samurai. Reads help first,
  banks credits, plays safe fights, checks status often, then grinds
  ~15 more days favoring Defense with occasional Charisma picks.
- **ghost.py** — reckless glass-cannon, Netrunner. Dives into Undercity
  immediately, pokes at edge cases (insufficient funds, the undocumented
  Black Market hotkey, an intentionally-mismatched Pit fight), then
  keeps diving for ~18 more days with no restraint.
- **wrench.py** — completionist, Street Samurai. Grinds RoboDOJO training,
  chases contracts and Pit tiers, plays the most in-game days (~24) --
  an Attack-focused first half to be strong enough for the Pit's top
  tier, then a guaranteed-combat, Charisma-only finishing stretch
  specifically aimed at clearing the Charisma 8+ threshold a few NPCs
  gate their warmer dialogue behind (not deterministic run-to-run, since
  it depends on random level-up timing, but reliably gets there most
  runs).

All three now use `grind_day` (see below) for their extended stretch,
cycling Slice Drop Box / Find a Fight / Hunt Cache so Datashards get a
real chance to turn up, and `visit_undercity` opportunistically uses
Intimidate whenever a fight actually offers it instead of always
fighting to resolution.

Each exposes a `run() -> bool` function and a `NAME` constant (the
persona's save-slug source), so `run_all.py` can drive them without
shelling out. Persona names are prefixed with `"0"` so they always sort
first in the "Load Merc" list — not a style choice, see `driver.py`'s
`save_slug_index()` docstring for why that specifically matters.

## Adding a persona

Copy `rook.py` as a starting point. Use the `visit_*` helpers in
`driver.py` for each hub location; `run_combat_loop` handles a fight to
resolution (win/loss/flee) including any level-up prompts, and
`grind_day(s, combat_actions, level_up_pick, fights=N, actions=[...])`
handles a full day of repeatable Undercity play plus sleep, for grinding
a persona from early-game into an advanced state without hand-writing
dozens of unique days. A short hand-written opening (1-3 days) that
exercises the daily reset (training cap, market rotation, Faction Heat)
is still worth keeping before handing off to `grind_day` for the rest.

A "talk" contract can complete (and even trigger a level-up) at almost
any non-Undercity/Pit location, printing an unpredictable number of
notification gates before that location's real menu appears --
`_settle_notifications(s, ready_anchor)` drains these automatically and
is already wired into every `visit_*` helper that can hit one. If you
add a new location helper, route its "send the real choice" step through
it the same way, using that location's `print_menu_divider(...)` label
(or another anchor unique to the real menu, not the arrival flavor text)
as `ready_anchor`.

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
