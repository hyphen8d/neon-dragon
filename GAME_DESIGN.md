# NEON DRAGON — Game Design Document

A single-player, terminal-based RPG set in a cyberpunk vaporwave world.
Local save file, hub-and-spoke structure, text-driven combat and dialogue.
No daily turn limit — see section 3.

## 1. Setting

**City name:** Neo Meridian (working title — change freely)
A sprawling, rain-slicked megacity run by corps, fixers, and street gangs.
Neon signage, synth pop bleeding out of noodle bars, chrome and static.
Tone: equal parts Blade Runner grime and Miami-vaporwave color palette —
magenta, cyan, deep purple, hot pink against black.

## 2. The Hub

A menu of locations the player travels between:

| Hub role               | Neon Dragon location   | Function                              |
|-----------------------|-------------------------|----------------------------------------|
| Rest stop               | **The Chrome Noodle Bar** | Rest, heal, hear rumors/gossip, flavor NPCs |
| Random encounters       | **The Undercity**         | Random encounters, fights, loot        |
| Bank                     | **NetVault**              | Deposit/withdraw credits (safe from death-loss) |
| Weapon/armor shop        | **Hyphen8d's Hut**        | Buy/sell gear and cyberware             |
| Healer                    | **Doc Wire's Clinic**     | Heal HP for credits, cure status effects |
| Trainer                  | **RoboDOJO**              | Spar with training drones to train stats, learn new abilities |
| Arena                     | **The Pit**               | PvE gladiator fights for reputation/credits |
| Romance NPC (Violet)    | **[NPC of your choosing]** | Flavor relationship subplot             |
| Leaderboard/contracts    | **Fixer Board**           | Leaderboard, contracts posted    |

## 3. Core Loop

1. Player logs in (loads save).
2. Player picks a hub location from the menu.
3. Combat/dialogue/contract resolves, stats and credits update.
4. Player keeps navigating the hub for as long as they want — no daily
   turn limit. (Decided during phase 5+6 review: cut for now to keep
   sessions unconstrained; revisit later if the game needs a pacing
   mechanism.)
5. Save file persists between sessions.

## 4. Character

The player is a cyber mercenary (**merc**) working Neo Meridian's edges.

- Core stats: HP, Attack (Chrome/Melee), Defense (Armor), Tech (hacking/
  ranged), Charisma (contract-gating), Credits, XP/Level.
- Class flavor at creation: **Street Samurai** (melee-focused), **Netrunner**
  (tech/hacking-focused). A third class, **Fixer** (charisma-focused), stays
  deferred — Charisma currently only gates two Chrome Noodle Bar contracts
  (see section 6), with no effect on combat, dialogue, or shop prices. A
  charisma-build class would still be a diluted hybrid of the other two
  until Charisma carries more weight.
- Cyberware slots instead of traditional armor slots (arm, eyes, spine,
  skin) — each grants a stat bonus, sourced from Hyphen8d's Hut.

## 5. NPCs

Data-driven (see CLAUDE.md) — not hardcoded. Each NPC has:
- Name, location, a short bio/flavor text
- A pool of dialogue lines (randomized on visit)
- Optionally: a contract hook, a shop inventory, or a relationship-track flag

Starter NPC roster (flavor only — expand freely):
- **Doc Wire** — clinic owner, gruff, healer
- **Ms. Kessler** — NetVault teller, deadpan corp-speak
- **Hyphen8d** — Hyphen8d's Hut dealer, sells cyberware, shady
- **Static Rin** — bartender at the Chrome Noodle Bar, hears everything
- **The Fixer** — posts contracts on the Fixer Board
- **Endr3am** — tall merc who works the Chrome Noodle Bar's back booth,
  brokers merc-to-merc contracts there (charisma-gated, see section 6)

## 6. Contracts

Multi-step contract objects: talk/kill chains (fetch/deliver not yet built)
with a credit + XP + reputation reward. Two contract boards: the **Fixer
Board** (gated by Reputation, run by The Fixer) and **Endr3am's board** at
the Chrome Noodle Bar (gated by Charisma). A third gate, **Level**, applies
to contracts on either board and is tied to the same tiers that unlock
Undercity's tougher enemies (`min_reputation`, `min_charisma`, `min_level`
in the schema). 12 contracts total as of this pass. Some contracts unlock
new hub locations or NPCs — not used yet, but the hook exists.

## 7. Combat

Turn-based, text-narrated. Player picks an action each round (Attack,
Tech/Hack, Defend, Flee — no item-use yet, no inventory beyond
cyberware). Simple damage formulas (stat + roll vs. defense). Status
effects are implemented: Stunned (skip your action) and Bleeding
(damage over time), inflicted by specific enemies.

## 8. The Undercity

Not a single random roll — the player picks an approach: **Jack In**
(steal credits, odds/payout scaled by Tech, failure forces a Corp-faction
fight), **Find a Fight** (guaranteed combat, random enemy), or **Scavenge**
(the old low-risk loot/nothing pool). Combat pool includes three
level-gated tiers (Ronin Netrunner L3+, Corp Strike Team L5+, Chrome
Beast L7+) so difficulty rises with the player instead of staying flat.

## 9. Aesthetic Rules

- Color palette: magenta/cyan/purple on black, used for headers, NPC
  names, and important numbers — not every line (avoid visual noise).
- Terse, noir-flavored narration. Short punchy sentences.
- ASCII/box-drawn panels for the hub menu and stat sheet.

## 10. Build Phases (suggested order)

1. Character creation + save/load + main menu skeleton
2. Hub navigation between locations (no content yet, just movement)
3. Combat engine + Undercity random encounters
4. NPCs + dialogue system (data-driven)
5. Contracts
6. ~~Daily turn limit + day-end/reset cycle~~ — cut, see section 3
7. Hyphen8d's Hut economy + cyberware
8. Polish: color palette, ASCII panels, flavor text pass

## Notes

This doc is a starting skeleton, not a spec to follow rigidly. Change
names, mechanics, and scope as the game takes shape in play. The point is
to keep updating this file as decisions get made, so it stays the source
of truth for what the game currently is.
