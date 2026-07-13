# Neon Dragon

**Alpha 1.0**

A single-player, terminal-based RPG set in a cyberpunk vaporwave city —
Neo Meridian. No server, no accounts, no web frontend. Just a Python
CLI you run in a terminal, with a local JSON save file per character.

## Requirements

- Python 3.11+
- [Rich](https://github.com/Textualize/rich) (terminal UI/formatting)

## Setup

```bash
git clone <repo-url> neon-dragon
cd neon-dragon
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python main.py
```

## Features

- Character creation — 2 classes (Street Samurai, Netrunner), each a
  different balance of the same stats
- A hub of 8 locations in Neo Meridian, each with real mechanics:
  Undercity (random encounters), NetVault (banking), Chop Shop
  (cyberware), Doc Wire's Clinic (healing + curing), The Dojo (stat
  training), The Pit (gladiator fights), Fixer Board (reputation-gated
  contracts), Chrome Noodle Bar (free rest + charisma-gated contracts)
- Turn-based combat with status effects (Bleeding, Stunned) and
  per-enemy factions (Street Gang, Corp, Gladiator)
- In-game character info (`i`) and help (`?`) screens, accessible
  mid-session without spending a turn
- JSON save/load, one file per character, autosaved on returning to
  the main menu

## Docs

- [`GAME_DESIGN.md`](GAME_DESIGN.md) — world, hub locations, and
  mechanics design notes; the source of truth for what the game
  currently is and how it's meant to evolve
- [`PLAYER_GUIDE.md`](PLAYER_GUIDE.md) — how everything actually works
  right now, including an honest list of what's not built yet. Also
  readable in-game via the `?` command
- [`CLAUDE.md`](CLAUDE.md) — the technical/process contract this
  project is built under (this was built with
  [Claude Code](https://claude.com/claude-code))

## Content is data, not code

NPCs, contracts, encounter tables, shop items, and the Pit's gladiator
roster all live under [`content/`](content/) as JSON. Adding or
tuning content is a data edit, not a code change.

## Status

Alpha 1.0. Every hub location has real mechanics; the current "end
game" is working through Fixer Board contracts. See the "What's not
built yet" section of `PLAYER_GUIDE.md` for known gaps.
