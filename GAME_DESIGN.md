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
| Weapon/armor shop        | **Hyphen8d's Hut**        | Buy/sell gear and cyberware — 4-item daily rotating stock, Charisma haggles the price down, one slot has a daily price event |
| Healer                    | **Doc Wire's Clinic**     | Heal HP for credits, cure status effects |
| Trainer                  | **RoboDOJO**              | Spar with training drones to train stats, learn new abilities |
| Arena                     | **The Pit**               | PvE gladiator fights for reputation/credits |
| Leaderboard/contracts    | **Fixer Board**           | Leaderboard, contracts posted    |

## 3. Core Loop

1. Player logs in (loads save).
2. Player picks a hub location from the menu.
3. Combat/dialogue/contract resolves, stats and credits update.
4. Player keeps navigating the hub for as long as they want within a
   day — no limit on how many locations/actions they visit before
   leaving. (Decided during phase 5+6 review: cut a hard turn limit to
   keep sessions unconstrained.)
5. Choosing Leave asks for a Yes/No confirmation first — it's a
   consequential action (resets Faction Heat, the daily drink limit,
   the Chrome Noodle Bar free rest, RoboDOJO's daily sparring cap, and
   Hyphen8d's stock/market), not a plain menu back-out. Confirming
   sends the merc home to sleep: the day counter increments, HP fully
   restores, status effects clear, and a "Daily Data Feed" panel
   summarizes standing. This is also when Faction Heat (section 8)
   resolves and daily kill counts reset.
6. Save file persists between sessions.

## 4. Character

The player is a cyber mercenary (**merc**) working Neo Meridian's edges.

- Core stats: HP, Attack (Chrome/Melee), Defense (Armor), Tech (hacking/
  ranged), Charisma (contract-gating, shop discounts, trauma bill
  reduction), Credits, XP/Level.
- Class flavor at creation: **Street Samurai** (melee-focused), **Netrunner**
  (tech/hacking-focused). A third, charisma-focused class (previously
  **Grifter**) is pulled for now pending a redesign — Charisma stays a
  live stat regardless of class, carrying real mechanical weight instead
  of only gating two Chrome Noodle Bar contracts — see section 6 and
  section 7 for the shop discount and trauma bill reduction it grants.
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
- **Daryl** — RoboDOJO's front-desk drone, repurposed from a
  decommissioned delivery unit, handles intake behind plexiglass
- **Agent Parker** — NetVault's security enforcer, works the floor
  alongside a robotic K9 partner; a second NPC at NetVault alongside
  Ms. Kessler (`npc_at` still surfaces Kessler as the primary teller;
  Parker's dialogue is fetched separately for the security flavor line)

## 6. Contracts

Multi-step contract objects: talk/kill chains (fetch/deliver not yet built)
with a credit + XP + reputation reward. Two contract boards: the **Fixer
Board** (gated by Reputation, run by The Fixer) and **Endr3am's board** at
the Chrome Noodle Bar (gated by Charisma). A third gate, **Level**, applies
to contracts on either board and is tied to the same tiers that unlock
Undercity's tougher enemies (`min_reputation`, `min_charisma`, `min_level`
in the schema). 16 contracts total as of this pass (9 Fixer Board, 7
Chrome Noodle Bar) — weighted toward the higher reputation/level end,
since that's where a repeat player ran out of new contracts first.
Beyond gating
Endr3am's board, Charisma also gets Hyphen8d's Hut prices down (2%
off per point, capped at 40%) — a general economic lever any class can
lean into, not tied to a specific class right now (see section 4). Some
contracts unlock new hub locations or NPCs — not used yet, but the hook
exists.

**Dynamic economy** (`engine/shop.py`, rolled by `roll_daily_market` in
`_sleep_and_advance_day`): each day, Hyphen8d's Hut restocks to a
random 4 items out of the full catalog, and one cyberware slot gets a
random price event — a 10-30% discount or surge — that stacks with the
Charisma discount rather than replacing it. Both are stored on
`Character` (`market_stock`, `market_modifier`) and re-roll on sleep;
`get_daily_catalog`/`discounted_cost` are the read paths the shop UI
uses, so nothing else needs to know the roll happened.

**Quantum Cores** (`Character.quantum_cores`): a rare secondary
currency, LORD-gem-style. 4% drop chance (`QUANTUM_CORE_DROP_CHANCE`
in `hub.py`) on a successful Slice Drop Box crack and on a top-tier
Pit win only (gladiators carry a `tier` field in `content/pit.json`;
`visit_the_pit` computes the top tier from whatever's in the file
rather than a hardcoded number, so adding a new toughest gladiator —
as of this pass, tier 4's **Kingpin Draxx** — moves the drop
eligibility with it instead of requiring a code change). Spent at a
hidden **Black Market** inside Hyphen8d's Hut
— reachable via an `[M]` hotkey deliberately left off the visible
Buy/Sell/Leave menu text, so it's undiscoverable without either
digging through the code or trying keys — selling four elite
prototype cyberware pieces (`content/black_market.json`, one per
slot, roughly double the top normal-tier bonus) priced only in Cores,
no Charisma discount or market event. `engine/shop.py`'s `get_item`
resolves ids across both catalogs so equipped Black Market gear works
everywhere normal gear does (loadout, sell menu); `unequip` refunds
whichever currency the item was actually priced in.

## 7. Combat

Turn-based, text-narrated. Player picks an action each round (Attack,
Tech/Hack, Defend, Flee, plus Items whenever inventory is non-empty —
see `content/usable_items.json`). Simple damage formulas (stat + roll
vs. defense). Status effects are implemented: Stunned (skip your
action) and Bleeding (damage over time), inflicted by specific
enemies. Droid enemies (`is_droid: true` in encounter data — currently
just Rogue Drone) are immune to Bleed from any source, enforced
centrally in `status_effects.apply_effect`. `EFFECT_LABELS` in
`status_effects.py` bakes in a colored glyph badge per effect (e.g.
`[🩸 BLEED]`), pre-wrapped in the WARNING theme color, so every
consumer gets the same styled badge for free.

`run_combat`'s round loop clears and redraws a two-panel HUD
(`_print_combat_hud`) at the top of every round — player left, enemy
right, both via `_combatant_panel`, HP shown as a number plus a
`make_hp_bar()` block meter. Only that round's narrative streams below
before a `press_any_key` pause; skipping that pause was a real bug
(narration flashed and vanished under the next round's clear) fixed by
gating the pause on the fight still being live. Narration lines are
tagged with a directional prefix — `»»»` (`_player_line`) for the
player's turn, an indented, darker `«««` (`_enemy_line`) for the
enemy's — via `PLAYER_ARROW`/`ENEMY_ARROW` in `engine/theme.py`.

Enemy content (`content/encounters.json`, `content/pit.json`) carries
a `scan_desc` string, rendered in the enemy panel under Faction/Status
along with a `_scan_readout()` line that shifts with the enemy's HP
percentage (Nominal / Structural Degradation / Catastrophic Hardware
Failure). Attack/Tech/Hack narration in `_player_hit` is gear-aware —
`_hit_flavor` picks the line by what's equipped in the relevant
cyberware slot (arm for Attack, eyes for Tech) instead of a generic
empty-slot line — and every hit line's verb is chosen by damage
magnitude via `_impact_verb` (grazes/strikes/shatters tiers), so the
same weapon reads differently at 2 damage vs. 15.

Each class also has a signature special move on a 3-round cooldown:
Street Samurai's **Samurai Slash** (1.5x damage, guaranteed Bleed,
still dodgeable) and Netrunner's **Override System** (no damage,
guaranteed 2-round Stun, bypasses dodge). Cooldown state lives in
`run_combat`'s local loop, not on the saved Character — it resets
every fight.

**RoboDOJO abilities** (`content` is Python, not JSON, for now —
see `engine/combat.py`'s `ABILITIES` and `_learn_ability` in
`engine/hub.py`): a second, class-independent tier of combat moves,
purchased once for credits and permanent afterward
(`Character.learned_abilities`). A class special and any learned
abilities are unified into one `Move` list per fight
(`_character_moves`), each with its own hotkey and cooldown, so a
Street Samurai who's bought both abilities fights with three extra
options beyond the core four. Two exist so far: **Adrenal Surge**
(heal on demand, 4-round cooldown) and **Kill Switch** (a guaranteed
hit that ignores enemy dodge_chance entirely, 4-round cooldown).

Sparring itself (training a stat) is capped at `TRAINING_ATTEMPTS_PER_DAY`
(3) bouts, shared across all three stats rather than per-stat, tracked on
`Character.training_attempts_today` and reset on sleep — spent on the
attempt regardless of win or loss, same "one training day" framing as
Chrome Noodle Bar's Buy a Round. Learning an ability is unlimited and
untouched by the cap, since it's a one-time purchase, not a repeatable
action.

Charisma talks down the trauma bill from a lost fight: 3% off per
point, capped at 45%. A high-Charisma build still goes down in a
fight the same as anyone else, but pays less to get patched up.

## 8. The Undercity

Not a single random roll — the player picks an approach, framed as a
physical street heist rather than an abstract cyberspace dive:
**[S] Slice Drop Box** (`_jack_in` — crack a corporate hardware drop
box bolted to a wall, credits scaled by Tech, a failed crack trips
Black-ICE and forces a Corp-faction fight on the spot),
**[F] Find a Fight** (guaranteed combat, random enemy), or
**[H] Hunt Cache** (`_scavenge` — a passive scanner sweep for
forgotten black-market drop boxes, the old low-risk loot/nothing
pool). The location panel's arrival text carries a "LOCAL AREA
NETSCAN" readout listing all three with their risk profile, so the
mechanical hints live in the environment description instead of
cluttering the hotkey prompt itself. Combat pool is 10 enemies as of
this pass: five at L1 (Street Ganger, Rogue Drone, Corp Patrol
Trooper, Scav Prowler, Sewer Hound — enough that the earliest,
most-repeated fights don't all read the same) plus level-gated tiers
above that (Ganger Boss L4+, Ronin Netrunner L3+, Corp Strike Team
L5+, Chrome Beast L7+, Corp Blacksite Enforcer L9+) so difficulty
keeps rising instead of flattening out once a player out-levels
Chrome Beast. Hunt Cache's loot/nothing pool is six entries (three
loot, three nothing) for the same reason — no single flavor line
repeating every single low-risk sweep.

**Faction Heat** (`engine/heat.py`): killing more than 3 enemies of the
same faction in a single day builds heat with that faction — currently
Corp and Street Gang only, the two with organized street presence to
retaliate. While hot, there's a 15% chance per Hunt Cache roll of an
ambush interrupting it instead of the normal loot/nothing outcome, and
the same 15% roll happens once on waking at the safehouse. Heat is
tracked on `Character.daily_kills` and wiped every time the player
sleeps (leaves the hub) — see section 3 on the day cycle.

Hunt Cache also has a flat `CACHE_BASE_RISK_CHANCE` (10%) that applies
on every attempt regardless of Heat — an unconditional counter to
farming it as a risk-free credit loop. It's checked only after the
Heat-triggered ambush misses (or doesn't apply), rolls a
faction-unlocked `roll_combat_encounter`, and is deliberately flavored
as opportunistic bad luck rather than a targeted retaliation.

## 9. Aesthetic Rules

- Color palette: magenta/cyan/purple on black, used for headers, NPC
  names, and important numbers — not every line (avoid visual noise).
- Terse, noir-flavored narration. Short punchy sentences.
- ASCII/box-drawn panels for the hub menu and stat sheet.
- **Interaction Deck** (`engine/hub.py`: `_interaction_deck`,
  `_npc_panel`, `_station_data_panel`): the shared layout for a
  location's sub-screen, used by NetVault, Doc Wire's Clinic,
  RoboDOJO, Fixer Board, and Chrome Noodle Bar. A `Table.grid(padding=
  (0, 4), expand=True)` splits the 120-column layout into an NPC
  dialogue panel (bio, a `Rule`, one quoted line) on the left and a
  titled operational-data panel (key/value rows, optionally an extra
  table like RoboDOJO's training costs) on the right. Anything that
  doesn't fit a compact side panel — the Fixer/Endr3am contract
  listings — stays its own full-width block below the deck instead of
  being squeezed in.

## 10. Build Phases (suggested order)

1. Character creation + save/load + main menu skeleton
2. Hub navigation between locations (no content yet, just movement)
3. Combat engine + Undercity random encounters
4. NPCs + dialogue system (data-driven)
5. Contracts
6. ~~Daily turn limit + day-end/reset cycle~~ — cut, see section 3
7. Hyphen8d's Hut economy + cyberware
8. Polish: color palette, ASCII panels, flavor text pass

## 11. Future Ideas (not built)

- **RoboDOJO belt ranks**: hitting stat thresholds through training could
  unlock a small permanent passive (e.g. +crit chance) instead of just
  more flat stat points — floated alongside the RoboDOJO abilities work
  in section 7, parked for later rather than built now. Likely makes
  more sense as part of a broader **Achievement system** (belts, contract
  streaks, faction standing, etc.) than as a RoboDOJO-only mechanic, so
  worth revisiting once that idea has more shape.

## Notes

This doc is a starting skeleton, not a spec to follow rigidly. Change
names, mechanics, and scope as the game takes shape in play. The point is
to keep updating this file as decisions get made, so it stays the source
of truth for what the game currently is.
