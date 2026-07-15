# CLAUDE.md — Neon Dragon

Read GAME_DESIGN.md first for the world, hub locations, and mechanics.
This file is the technical/process contract for how we build it.

## What this project is

A local, single-player, terminal-based RPG inspired by Legend of the Red
Dragon, reskinned as a cyberpunk vaporwave game. No server, no multiplayer,
no web frontend — just a Python CLI you run in a terminal.

## Tech stack

- **Python 3.11+**
- **Rich** (https://github.com/Textualize/rich) for colored/styled terminal
  output — panels, tables, colored text for the vaporwave palette. Use
  Rich for the initial build; only reach for Textual (full TUI) later if
  we decide we want persistent multi-pane screens.
- **JSON** for the save file and for all game content (NPCs, quests, items,
  encounter tables). No database.
- No external network calls, no auth, no accounts — everything is local.

## Project structure (adjust as needed, but keep content data-driven)

```
neon-dragon/
  main.py                 # entry point, main loop
  engine/
    character.py          # character stats, leveling
    combat.py              # combat resolution
    save.py                # load/save JSON save file
    hub.py                  # hub menu / navigation
  content/
    npcs.json               # NPC definitions
    quests.json             # quest definitions
    encounters.json         # random encounter tables
    items.json               # shop/cyberware items
  saves/
    (player save files, gitignored)
  CLAUDE.md
  GAME_DESIGN.md
```

## Core principle: content lives in JSON, not code

NPCs, quests, encounter tables, and shop items should be data files under
`content/`, not hardcoded Python. The engine reads them generically. This
means adding a new NPC or quest later is a content edit, not a code change.

## Style

- Keep functions small and readable — this is a hobby project, not
  production software. Favor clarity over cleverness.
- Type hints on function signatures.
- Comments explaining *why*, not restating *what*.
- Don't add features not asked for. Build the current phase, then stop
  and let me play it before moving to the next.

## Workflow

- We're building this in phases (see "Build Phases" in GAME_DESIGN.md).
  Only work on the phase I ask for — don't jump ahead.
- After each phase, tell me how to run it and what to try.
- Commit to git after each working phase so we can roll back cleanly.
- If a design decision in GAME_DESIGN.md turns out to be awkward in
  practice, flag it and suggest an update to that file rather than
  silently deviating from it.

## Playtesting

Two different tools for two different questions — use both, not one instead
of the other:

- **Headless simulation** (a script that drives `run_combat`/`roll_combat_encounter`/
  `check_level_up`/etc. directly, bot-controlled, no terminal UI) for
  *quantitative* balance questions: XP/level pacing, encounter weight
  distributions, drop rates, whether an achievement unlocks at a fair rate
  across classes. A handful of manual playthroughs can't generate enough
  data points to trust the answer to "does this curve actually behave the
  way the numbers suggest" — a sim covering 100+ fights in seconds can.
- **Scripted-stdin or hands-on CLI playthroughs** for anything that touches
  UI, a new screen, or player-facing feel: menu flow, panel rendering,
  text wrapping, a new hotkey actually showing up where expected, whether
  something that measures fine on paper still *feels* tedious or confusing
  in practice. A bot only exercises what it's scripted to do — it's blind
  to everything outside that script, including the actual UX complaint
  that often motivated the change in the first place.

Rule of thumb: reach for headless sim when the question is "what does the
data say," and a real (or scripted-stdin) playthrough when the question is
"does this actually work/feel right."

## Save files

- One JSON save file per character under `saves/`.
- Save files are gitignored — don't commit player saves.

## Non-goals (for now)

- No multiplayer, no server, no web UI.
- No monetization/real accounts — this is a local hobby game.
