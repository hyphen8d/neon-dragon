# Neon Dragon — Admin Guide

A single-file reference wiki for whoever's running/editing this game, as
opposed to `PLAYER_GUIDE.md` (in-character, player-facing, also readable
in-game via `?`). This doc pulls every number and gate from the actual
`content/*.json` files and `engine/*.py` constants as of **Alpha 2.6** —
if a number here ever disagrees with the code, the code wins; update this
file to match rather than the other way around.

Cross-reference: `GAME_DESIGN.md` explains *why* things work this way
and tracks decisions/future ideas. This doc is *what currently exists*,
laid out for lookup rather than narrative reading.

## Contents

1. [Quick facts](#quick-facts)
2. [Classes](#classes)
3. [Progression](#progression)
4. [Locations](#locations)
5. [NPCs](#npcs)
6. [Combat system](#combat-system)
7. [Bestiary — Undercity](#bestiary--undercity)
8. [Bestiary — The Pit](#bestiary--the-pit)
9. [Bestiary — RoboDOJO sparring drones](#bestiary--robodojo-sparring-drones)
10. [Contracts](#contracts)
11. [Cyberware](#cyberware)
12. [Usable items](#usable-items)
13. [Economy](#economy)
14. [Daily cycle](#daily-cycle)
15. [Faction Heat](#faction-heat)
16. [Save files](#save-files)
17. [Content map — what to edit where](#content-map--what-to-edit-where)

---

## Quick facts

| | |
|---|---|
| Version | Alpha 2.6 |
| Classes | 2 (Street Samurai, Netrunner) — third charisma-focused class pulled, pending redesign |
| Hub locations | 8 |
| NPCs | 8 |
| Undercity combat encounters | 11 (10 open + 1 kill-gated: the Draxx grudge match) |
| Undercity scavenge/loot flavor entries | 6 (3 loot, 3 nothing) |
| Pit gladiators | 5 (2 Tier 1, 1 Tier 2, 1 Tier 3, 1 Tier 4) |
| RoboDOJO sparring drones | 3 (one per trainable stat) |
| RoboDOJO purchasable abilities | 2 (Adrenal Surge, Kill Switch) |
| Contracts | 16 (9 Fixer Board, 7 Chrome Noodle Bar) |
| Cyberware (normal) | 8, across 4 slots |
| Cyberware (Black Market) | 4, one per slot |
| Cyberware (Street-Modded) | 1 (arm slot, credits, kill-gated) |
| Buy a Round micro-encounters | 8 (weighted; 3 stat, 2 rep, 2 drunk, 1 rep-scav) |
| Usable/consumable items | 2 |
| Status effects | 3 (Bleed, Stunned, Drunk) |
| City Conditions flavor entries | 12 weather + 17 headlines |
| Save format | one JSON file per character under `saves/`, gitignored |

---

## Classes

Defined in `engine/character.py`'s `CLASSES` dict.

| Class | HP | ATK | DEF | Tech | Charisma | Notes |
|---|---|---|---|---|---|---|
| Street Samurai | 30 | 8 | 6 | 2 | 3 | Melee-focused. Special: Samurai Slash |
| Netrunner | 22 | 3 | 3 | 9 | 4 | Tech-focused. Special: Override System |
| ~~Grifter~~ | 24 | 4 | 4 | 4 | 9 | **Pulled.** Was charisma-focused; no combat special existed for it. A redesigned third class is pending — see `GAME_DESIGN.md` §4 |

Charisma remains a fully live stat regardless of class — see [Economy](#economy). It is **not** grown by leveling (`STAT_GROWTH` in `engine/leveling.py` omits it); the "Buy a Round" stat-gain outcomes only touch Attack/Defense/Tech (`ROUND_ENCOUNTERS` in `engine/hub.py`), so **cyberware is the only way to raise Charisma after character creation.**

---

## Progression

- XP curve (`engine/leveling.py`): `xp_for_level(level) = 50 * level * (level - 1) / 2`. Level 2 = 50 XP, level 3 = 150, level 4 = 300 (each level costs 50 more than the last step).
- Per level: `STAT_GROWTH = {max_hp: +3, attack: +1, defense: +1, tech: +1}`, plus a full heal. Charisma does **not** grow on level-up.
- **Player choice on level-up**: on top of the flat `STAT_GROWTH`, the player picks one of Attack/Defense/Tech via `hotkey_prompt` to get an extra +1 (`LEVEL_UP_BONUS_STATS` in `engine/leveling.py`). This is the only build-crafting decision in the leveling system — everything else is deterministic. Prompted once per level gained, so a multi-level XP jump asks once per level in the loop.
- A single large XP reward can trigger multiple level-ups at once (`check_level_up` loops).
- XP sources: combat kills (`enemy_data["xp_reward"]`) and contract completion (`quest["reward"]["xp"]`).

---

## Locations

All defined in `engine/hub.py` (`LOCATION_HOTKEYS`, `LOCATIONS`, `LOCATION_DESCRIPTIONS`, and each has a `visit_*` function).

| Hotkey | Location | Function |
|---|---|---|
| `C` | Chrome Noodle Bar | Free rest (once/day), Buy a Round (once/day), Endr3am's charisma-gated contract board |
| `U` | Undercity | Slice Drop Box (hack), Find a Fight (guaranteed combat), Hunt Cache (scavenge) |
| `N` | NetVault | Deposit/withdraw credits — banked credits are safe from trauma-bill loss |
| `H` | Hyphen8d's Hut | Buy/sell cyberware; daily rotating 4-item stock + price event; hidden Black Market; hidden Street-Modded stash (kill-gated) |
| `D` | Doc Wire's Clinic | Heal HP for credits, cure status effects, buy consumables |
| `R` | RoboDOJO | Spar to train stats (capped 3/day), buy permanent abilities |
| `P` | The Pit | Gladiator fights for reputation/credits, rare Quantum Core on a top-tier win |
| `F` | Fixer Board | Reputation-gated contract board |

Plus `I` (Character Info), `?` (in-game help/PLAYER_GUIDE.md), `L` (Leave — sleep, advances the day).

The main hub menu's Character Info action row shows a live `len(character.active_quests)` count (`"contracts (N active)"` / `"contracts (none active)"`, `print_hub_menu` in `engine/hub.py`) so active contracts don't require a trip to a specific board or the Character Info screen to notice. Deliberately not added as a column to `print_status` — that HUD table is reused on every location screen, so widening it there would risk the fixed 120-column layout everywhere, not just the hub.

### Chrome Noodle Bar
- **Free rest**: tops HP to `REST_THRESHOLD` (50%) of max, once per day (`Character.rested_today`). No-op if already at/above the floor.
- **Buy a Round** (`BUY_ROUND_COST` = 25cr, once/day via `bought_round_today`; free if `corp_kills >= CORP_HERO_KILL_THRESHOLD` (15) — Static Rin comps "local hero" mercs): rolls a weighted micro-encounter table, `ROUND_ENCOUNTERS`/`_resolve_round_encounter` in `engine/hub.py` — 8 flavored outcomes, weighted to land close to the old flat split (~12% stat / ~58% rep / ~28% drunk): 3 stat entries (+1 permanent Attack/Defense/Tech each, weight 4 each — the Attack one also has a 10% chance of an extra 5 damage on top), 1 "Scav pickpocket" rep entry (weight 4, +2 rep), 2 generic gossip rep entries (weight 28 each, +2 rep), 2 drunk entries (weight 14 each, **Drunk** status, 3 rounds).
- **Contract Booth** (`[C]`, `_visit_endr3am`): Endr3am's charisma-gated board (see [Contracts](#contracts)), reached via the back-booth sub-screen, not a separate hub location. Uses the same Interaction Deck treatment as every other primary-NPC screen (right panel: Charisma, Contracts Active/Completed for this board) — labeled "Check the shady booth in the back" and printed as plain unbordered text before this pass; both fixed for consistency with the rest of the hub.

### Undercity
Three approaches, picked each visit (`_jack_in`, `_find_a_fight`, `_scavenge` in `engine/hub.py`):

- **Slice Drop Box** — success chance `min(0.85, 0.30 + tech * 0.04)`. On success: `random(15,35) + tech//2` credits, plus a 4% (`QUANTUM_CORE_DROP_CHANCE`) chance of +1 Quantum Core (narrated as unsettling — "grown, not manufactured" — not a plain pickup). On failure: forces a Corp-faction combat encounter ("Black-ICE" trace).
- **Find a Fight** — guaranteed combat, any level-eligible enemy.
- **Hunt Cache** — layered risk: if any faction is "hot" (Faction Heat), 15% ambush chance rolls a combat encounter against that faction first; otherwise a flat 10% (`CACHE_BASE_RISK_CHANCE`) chance of a random combat encounter regardless of Heat; otherwise rolls the loot/nothing pool.

`roll_combat_encounter`/`roll_scavenge_encounter` (`engine/encounters.py`) now take the full `Character`, not just level — `_eligible` filters on `min_level` as before, plus an optional `requires_kill` field (an enemy name that must already be in `character.kills`). Currently used only by the Draxx grudge match (see [Bestiary — The Pit](#bestiary--the-pit)), which is otherwise an ordinary weighted entry in the same combat pool Find a Fight and the Hunt Cache baseline-risk roll draw from — it never surfaces in the Corp-only Jack In trace or a Heat ambush, since its faction is `Gladiator`, not `Corp`/`Street Gang`.

### Hyphen8d's Hut
- Now uses the Interaction Deck too (right panel: "Today's Event"); previously the only primary-location NPC printed as plain text instead of the bordered panel everyone else got.
- Daily stock: 4 random cyberware items (`DAILY_STOCK_SIZE`), re-rolled on sleep.
- Daily market event: one random slot gets a discount or surge, 10-30% (`MARKET_EVENT_MIN/MAX_PERCENT`), stacking with the Charisma discount.
- **Black Market** (`[M]` hotkey, deliberately not shown in the visible menu text): 4 elite items priced in Quantum Cores, no Charisma/market modifiers apply. Flavor text now hints at a shared conspiracy thread (purged corp archives, something watching through the net, pre-city buried tech) rather than reading as a plain higher shop tier.
- **Street-Modded stash** (`[K]` hotkey, also not shown in the visible menu text): unlocks once `street_gang_kills >= STREET_MODDED_KILL_THRESHOLD` (15, `engine/shop.py`'s `street_modded_unlocked`). Below the threshold, selecting it just prints Hyphen8d turning the player away in character. Above it, buys like the normal catalog — credits, Charisma discount, and the daily market event all apply (unlike the Black Market's fixed Quantum Core pricing). 1 item currently: Riot Knuckles (arm, 220cr, +9 Attack, Bleed 30%/2rd).
- Sell-back rate: 50% of cost (`SELL_BACK_RATE`), refunded in whichever currency the item was priced in.

### Doc Wire's Clinic
- Heal: 2 credits/HP (`HEAL_COST_PER_HP`), amount capped by what's affordable.
- Cure all status effects: flat 15 credits (`CURE_COST`).
- Buy Supplies: sells the usable-item catalog.

### RoboDOJO
- **Sparring** (train Attack/Defense/Tech): a real fight against a themed drone (see [Bestiary — RoboDOJO](#bestiary--robodojo-sparring-drones)). Win → +1 to the stat, then charge `_train_cost(current) = 40 + current * 5` credits (deducted even into debt). Lose/flee → no stat gain, no extra charge beyond whatever the fight itself cost.
- Capped at `TRAINING_ATTEMPTS_PER_DAY` = 3 bouts/day, **shared across all three stats**, spent on the attempt regardless of outcome. Resets on sleep.
- **Abilities**: one-time credit purchases, permanent, independent of class — see [Combat system](#combat-system).

### The Pit
- Fixed roster of 5 gladiators (see [Bestiary — The Pit](#bestiary--the-pit)), no level gating.
- Win grants credits/XP/reputation.
- Quantum Core drop (4% chance) only on beating whichever gladiator currently has the **highest tier** in `content/pit.json` (`top_tier = max(tier)`, computed dynamically — not hardcoded to a specific tier, so adding a new toughest gladiator moves the drop-eligible tier automatically). Narration is the same "grown, not manufactured" unsettling flavor as the Slice Drop Box drop.
- **Reigning champion callout**: `visit_the_pit`'s arrival text checks `character.kills.get("Kingpin Draxx", 0) > 0` and, once true, permanently swaps the default "the crowd wants blood" line for a champion-acknowledgment line instead.
- **Draxx grudge match**: see [Bestiary — Undercity](#bestiary--undercity)'s nemesis-encounter note — beating Draxx unlocks a kill-gated Undercity ambush where he (and his crew) show up to reclaim his honor, buffed above his Pit stats.

### Fixer Board
- Reputation-gated contracts (see [Contracts](#contracts)).

---

## NPCs

Defined in `content/npcs.json`. Each has an `id`, `location`, `bio`, a pool of randomized `lines`, and an optional `conditional_lines` array.

| ID | Name | Location | Role |
|---|---|---|---|
| `doc_wire` | Doc Wire | Doc Wire's Clinic | Clinic owner, gruff healer |
| `ms_kessler` | Ms. Kessler | NetVault | Bank teller, deadpan corp-speak |
| `agent_parker` | Agent Parker | NetVault | Security enforcer + K9 drone (secondary NPC there; `npc_at` still surfaces Kessler as primary) |
| `hyphen8d` | Hyphen8d | Hyphen8d's Hut | Cyberware dealer, shady |
| `static_rin` | Static Rin | Chrome Noodle Bar | Bartender, hears everything |
| `the_fixer` | The Fixer | Fixer Board | Posts reputation-gated contracts |
| `endr3am` | Endr3am | Chrome Noodle Bar | Posts charisma-gated contracts (back booth) |
| `daryl` | Daryl | RoboDOJO | Front-desk drone, handles intake/training/abilities |

### Conditional dialogue

`random_line(npc, character)` in `engine/npcs.py`: when a `character` is passed, each entry in `npc["conditional_lines"]` (`{condition, min, line}`) is checked against `_condition_value(character, condition)`; if any threshold is met, the line is drawn **only** from the eligible conditional pool (not mixed with the generic `lines` pool) until the condition stops applying. Every hub screen that shows an NPC now passes `character` through — every primary-NPC screen goes through `_npc_panel`/`_interaction_deck`, and the one secondary NPC (Agent Parker) gets `_npc_panel` printed standalone. Calling `random_line(npc)` with no character still works and just uses the generic pool (used nowhere currently, kept for API safety).

Supported `condition` keys (add more by extending `_condition_value` — no new Character fields needed, all reuse existing state):

| Condition | Reads | Current usage |
|---|---|---|
| `corp_kills` | Sum of `character.kills` for Corp-faction enemy names | Static Rin, min 5 and min 15 (higher tier adds to the pool, doesn't replace it) |
| `street_gang_kills` | Same, Street Gang faction | Hyphen8d, min 15 (also the Street-Modded stash unlock threshold) |
| `total_kills` | Sum of all `character.kills` values | Agent Parker, min 10 |
| `quantum_cores` | `character.quantum_cores` | Hyphen8d, min 1 |
| `completed_quests` | `len(character.completed_quests)` | The Fixer, min 3 |
| `charisma` | `character.charisma` | Endr3am, min 9 |
| `banked_credits` | `character.banked_credits` | Ms. Kessler, min 500 |
| `in_debt` | `1` if `character.credits < 0` else `0` | Doc Wire, min 1 |
| `learned_abilities` | `len(character.learned_abilities)` | Daryl, min 2 |
| `equipped_<item_id>` | `1` if `item_id` is in `character.cyberware.values()` else `0` | Doc Wire (`equipped_singularity_fist`), Static Rin (`equipped_target_lock_eyes`), Hyphen8d (`equipped_razor_claws`), Agent Parker (`equipped_ghost_protocol_derm`), Ms. Kessler (`equipped_oracle_retinas`) — all min 1 |

---

## Combat system

Turn-based, resolved in `engine/combat.py`'s `run_combat`. Core actions every fight: **Attack** (stat: Attack), **Tech/Hack** (stat: Tech), **Defend** (halves incoming damage, unless the enemy `ignores_defend`), **Flee** (50/50, no reward either way), plus **Items** whenever inventory is non-empty.

- **Damage formula**: `max(1, stat + random(1,6) - enemy_defense)`.
- **Critical hit**: 20% chance (`CRIT_CHANCE`), ×1.5 damage (`CRIT_MULTIPLIER`).
- **Dodge**: some enemies have `dodge_chance` — a miss deals no damage and doesn't trigger gear on-hit effects.
- **Gear-aware flavor**: hit narration depends on what's equipped in the relevant slot (arm for Attack, eyes for Tech); higher-tier gear can also inflict a status effect on-hit (`inflict_effect`/`inflict_chance`/`inflict_duration` on the item).

### Moves (class specials + RoboDOJO abilities)

Unified into one `Move` list per fight (`_character_moves` in `engine/combat.py`), each with its own hotkey and independent cooldown, tracked locally to the fight (resets every combat, not saved on Character).

| Move | Source | Hotkey | Cooldown | Effect |
|---|---|---|---|---|
| Samurai Slash | Street Samurai class special | `S` | 3 rounds | 1.5× Attack-based damage, guaranteed Bleed. Still dodgeable. |
| Override System | Netrunner class special | `O` | 3 rounds | No damage, guaranteed 2-round Stun. Bypasses dodge (not a physical hit). |
| Adrenal Surge | RoboDOJO ability (120cr) | `H` | 4 rounds | Heal 15 HP on demand. No-op message if already full. |
| Kill Switch | RoboDOJO ability (180cr) | `K` | 4 rounds | Guaranteed-hit Attack-based strike (+3 flat bonus), **ignores enemy dodge_chance** entirely. |

A character can have a class special *and* both abilities active simultaneously (up to 3 extra moves beyond the core four).

### Status effects

Defined in `engine/status_effects.py`.

| Effect | Badge | Mechanic |
|---|---|---|
| Bleed | `[ /// BLEED ]` | 3 damage/round (`BLEED_DAMAGE`) at the start of the bleeding combatant's round. Droids (`is_droid: true`) are immune. |
| Stunned | `[ !!! STUN ]` | Skips the stunned combatant's action that round. |
| Drunk | `[ ERR: DRUNK ]` | Player-only (from Buy a Round). `-3` (`DRUNK_STAT_PENALTY`) to Attack/Tech rolls in combat. |

Effects tick down once per round and don't clear on leaving combat (carry into the next fight) unless cured at Doc Wire's Clinic or the character sleeps.

### Trauma bill (on defeat)

`_handle_defeat`: HP set to 1, credits deducted by `trauma_bill(level) = 40 + (level - 1) * 15`, discounted by Charisma (`3%/point, capped at 45%`). Can push credits negative — no floor.

---

## Bestiary — Undercity

`content/encounters.json`. `min_level` gates eligibility; `weight` is relative pick chance among eligible entries at the player's current level (via `roll_combat_encounter`).

| Enemy | Faction | Min Lvl | Weight | HP | ATK | DEF | Credits | XP | Gimmick |
|---|---|---|---|---|---|---|---|---|---|
| Street Ganger | Street Gang | 1 | 30 | 16 | 5 | 2 | 25 | 12 | Bleed 25%/2rd |
| Rogue Drone | Corp | 1 | 20 | 12 | 4 | 5 | 30 | 15 | Droid; Stun 25%/1rd |
| Corp Patrol Trooper | Corp | 1 | 12 | 22 | 7 | 6 | 45 | 25 | Stun 30%/1rd |
| Scav Prowler | Scavs | 1 | 18 | 14 | 5 | 3 | 28 | 13 | Dodge 15% |
| Sewer Hound | Feral | 1 | 16 | 15 | 6 | 2 | 26 | 13 | Bleed 30%/2rd |
| Ronin Netrunner | Ronin | 3 | 15 | 26 | 9 | 8 | 60 | 25 | Dodge 20% |
| Ganger Boss | Street Gang | 4 | 12 | 30 | 10 | 7 | 70 | 30 | Bleed 30%/2rd |
| Corp Strike Team | Corp | 5 | 12 | 35 | 13 | 8 | 85 | 35 | Ignores Defend |
| Chrome Beast | Feral | 7 | 8 | 50 | 12 | 10 | 110 | 45 | Bleed 35%/3rd |
| Corp Blacksite Enforcer | Corp | 9 | 6 | 60 | 15 | 12 | 140 | 55 | Dodge 15%; Stun 30%/1rd |

**Nemesis encounter** — kill-gated, not level-gated, via the `requires_kill` field (only enters the pool once that enemy name is in `character.kills`):

| Enemy | Faction | Min Lvl | Weight | Requires kill | HP | ATK | DEF | Credits | XP | Rep | Gimmick |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Kingpin Draxx (grudge match) | Gladiator | 4 | 7 | Kingpin Draxx | 46 | 16 | 10 | 130 | 45 | 30 | Dodge 20%; Bleed 30%/2rd |

**Scavenge/loot pool** (`roll_scavenge_encounter`, same `min_level`/`weight` mechanism, type `loot` or `nothing`):

| ID | Type | Weight | Credits range |
|---|---|---|---|
| `scavenger_stash` | loot | 18 | 10–35 |
| `forgotten_terminal` | loot | 15 | 8–30 |
| `black_market_cache` | loot | 10 | 15–40 |
| `nothing_static` | nothing | 20 | — |
| `dead_signal` | nothing | 16 | — |
| `false_positive` | nothing | 14 | — |

**Factions**: Street Gang, Corp, Scavs, Feral, Ronin currently appear in the Undercity pool. Only **Corp** and **Street Gang** are tracked for Faction Heat (see below) — Scavs/Feral/Ronin kills never build Heat.

---

## Bestiary — The Pit

`content/pit.json`. No level gating — the full roster of 5 is always available. `tier` drives display order and the top-tier Quantum Core drop eligibility (computed dynamically as `max(tier)`, currently tier 4).

| Gladiator | Tier | HP | ATK | DEF | Credits | XP | Rep | Gimmick |
|---|---|---|---|---|---|---|---|---|
| Scrap Dog Vex | 1 | 20 | 6 | 3 | 35 | 10 | 10 | Bleed 30%/2rd |
| Volt Jockey | 1 | 18 | 7 | 4 | 38 | 11 | 11 | Stun 25%/1rd |
| Ironclad Marta | 2 | 30 | 8 | 7 | 55 | 18 | 18 | None |
| The Widow | 3 | 26 | 11 | 5 | 80 | 28 | 28 | Bleed 35%/2rd |
| Kingpin Draxx | 4 (current top tier) | 40 | 14 | 9 | 110 | 38 | 38 | Dodge 20% |

Faction: all `Gladiator` — never builds Faction Heat.

---

## Bestiary — RoboDOJO sparring drones

`engine/bestiary.py`'s `TRAINING_DRONES`, keyed by trainable stat. Flat stats, no level scaling (the rising credit fee is the real gate over time). All `is_droid: true` (immune to Bleed), faction `Training` (never builds Heat, `credits_reward: 0` — the reward for winning is the stat point + XP, not credits).

| Trains | Enemy name | HP | ATK | DEF | XP |
|---|---|---|---|---|---|
| Attack | Melee Drone | 18 | 5 | 3 | 8 |
| Defense | Heavy-Frame Drone | 20 | 6 | 3 | 8 |
| Tech | Sparring ICE | 16 | 5 | 4 | 8 |

---

## Contracts

`content/quests.json`. Two boards, gated independently by Reputation (Fixer Board), Charisma (Chrome Noodle Bar/Endr3am), and Level (both boards). Each contract is a "talk"/"kill" step chain; `notify_step` advances any active contract whose current step matches, regardless of where the step happens, and multiple active contracts can share a kill/talk target and all advance off one action.

### Fixer Board (9, gated by Reputation)

| ID | Title | Steps | Reward (cr/xp/rep) | Min Rep | Min Lvl |
|---|---|---|---|---|---|
| `word_on_the_street` | Word on the Street | talk Chrome Noodle Bar → talk Fixer Board | 20/10/5 | 0 | 1 |
| `chrome_debt` | Chrome Debt | kill Street Ganger → talk Fixer Board | 40/20/10 | 0 | 1 |
| `drone_bounty` | Drone Bounty | kill Rogue Drone → talk Fixer Board | 45/20/8 | 10 | 1 |
| `corp_trouble` | Corp Trouble | kill Corp Patrol Trooper → talk Fixer Board | 60/30/15 | 20 | 1 |
| `turf_war` | Turf War | kill Ganger Boss → talk Fixer Board | 75/32/16 | 12 | 4 |
| `ghost_protocol` | Ghost Protocol | kill Ronin Netrunner → talk Fixer Board | 70/30/15 | 15 | 3 |
| `corporate_housecleaning` | Corporate Housecleaning | kill Corp Strike Team → talk Fixer Board | 90/40/18 | 0 | 5 |
| `somethings_loose` | Something's Loose | kill Chrome Beast → talk Fixer Board | 150/60/30 | 30 | 7 |
| `blacksite_leak` | Blacksite Leak | kill Corp Blacksite Enforcer → talk Fixer Board | 200/80/40 | 40 | 9 |

### Chrome Noodle Bar (7, gated by Charisma)

| ID | Title | Steps | Reward (cr/xp/rep) | Min Cha | Min Lvl |
|---|---|---|---|---|---|
| `loose_ends` | Loose Ends | kill Street Ganger → talk Chrome Noodle Bar | 15/8/3 | 0 | 1 |
| `something_in_the_pipes` | Something in the Pipes | kill Sewer Hound → talk Chrome Noodle Bar | 20/10/4 | 0 | 1 |
| `loose_lips` | Loose Lips | talk NetVault → talk Chrome Noodle Bar | 25/12/5 | 6 | 1 |
| `fence_trouble` | Fence Trouble | kill Scav Prowler → talk Chrome Noodle Bar | 35/16/7 | 6 | 1 |
| `new_blood` | New Blood | talk NetVault → talk Chrome Noodle Bar | 30/15/6 | 0 | 3 |
| `friends_in_high_places` | Friends in High Places | kill Corp Patrol Trooper → talk Chrome Noodle Bar | 65/30/12 | 9 | 1 |
| `steady_hands` | Steady Hands | kill Rogue Drone → talk Chrome Noodle Bar | 55/25/10 | 6 | 5 |

Note: some kill targets are shared across both boards (e.g. Street Ganger, Corp Patrol Trooper, Rogue Drone) — this is intentional; a player with both contracts active advances both from a single kill.

---

## Cyberware

`content/items.json` (normal catalog, credits) and `content/black_market.json` (Quantum Cores, no discounts apply). 4 slots: arm, eyes, spine, skin. Buying swaps out (and sells back at 50%) whatever's currently in that slot.

### Normal catalog (8 items)

| ID | Name | Slot | Cost | Bonus | Gimmick |
|---|---|---|---|---|---|
| `chrome_arm_mk1` | Chrome Arm Mk.I | arm | 80 | +3 Attack | — |
| `razor_claws` | Razor Claws | arm | 150 | +6 Attack | Bleed 25%/2rd |
| `optic_scanner` | Optic Scanner | eyes | 90 | +4 Tech | — |
| `target_lock_eyes` | Target-Lock Eyes | eyes | 160 | +7 Tech | Stun 20%/1rd |
| `spinal_brace` | Spinal Brace | spine | 100 | +4 Defense | — |
| `reflex_booster` | Reflex Booster | spine | 170 | +7 Defense | — |
| `synth_derm` | Synth-Derm | skin | 70 | +3 Charisma | — |
| `mirrorskin` | Mirrorskin | skin | 140 | +6 Charisma | — |

### Black Market (4 items, one per slot, ~2× the normal top-tier bonus)

Reached via the hidden `[M]` hotkey at Hyphen8d's Hut (not shown in the visible menu text — discoverable only by trying keys or reading code).

| ID | Name | Slot | Cost (Quantum Cores) | Bonus | Gimmick |
|---|---|---|---|---|---|
| `singularity_fist` | Singularity Fist | arm | 3 | +12 Attack | Bleed 40%/3rd |
| `oracle_retinas` | Oracle Retinas | eyes | 3 | +13 Tech | Stun 35%/2rd |
| `monolith_spine` | Monolith Spine | spine | 4 | +13 Defense | — |
| `ghost_protocol_derm` | Ghost Protocol Derm | skin | 4 | +12 Charisma | — |

### Street-Modded stash (1 item, credits-priced, kill-gated)

Reached via the hidden `[K]` hotkey at Hyphen8d's Hut, gated on `street_gang_kills >= 15` (`engine/shop.py`'s `street_modded_unlocked`). Unlike the Black Market, priced in credits and subject to the normal Charisma discount and daily market event.

| ID | Name | Slot | Cost | Bonus | Gimmick |
|---|---|---|---|---|---|
| `riot_knuckles` | Riot Knuckles | arm | 220 | +9 Attack | Bleed 30%/2rd |

---

## Usable items

`content/usable_items.json`, sold at Doc Wire's Clinic, used mid-combat via the Items menu.

| ID | Name | Cost | Effect |
|---|---|---|---|
| `nanite_patch` | Nanite Patch | 20 | Heal 15 HP |
| `emp_grenade` | EMP Grenade | 35 | Stun a **Corp**-faction enemy for 2 rounds; fizzles harmlessly (but is still consumed) on any other faction |

Items are only consumed on an actual effect — a heal at full HP or a faction-mismatched stun does **not** consume the item.

---

## Economy

- **Charisma → cyberware discount**: 2%/point, capped at 40% (`CHARISMA_DISCOUNT_PER_POINT`/`CAP` in `engine/shop.py`). Stacks with the daily market event.
- **Charisma → trauma bill discount**: 3%/point, capped at 45% (`engine/combat.py`).
- **Charisma → contract gating**: Chrome Noodle Bar board only (Fixer Board is Reputation-gated).
- **Quantum Cores**: rare secondary currency. 4% drop chance (`QUANTUM_CORE_DROP_CHANCE`) on a successful Slice Drop Box crack, and on a top-tier Pit win. Spent only at the hidden Black Market.
- **Street Gang kills → Street-Modded stash**: at 15+ `street_gang_kills`, a second hidden Hyphen8d's Hut menu (`[K]`) unlocks — see [Cyberware](#cyberware). Credits-priced, unlike the Quantum-Core-only Black Market.
- **Corp kills → free drinks**: at 15+ `corp_kills` (`CORP_HERO_KILL_THRESHOLD`), Buy a Round waives its 25cr cost — Static Rin treats the player as a local hero.
- **Reputation**: earned from Fixer Board contracts and Pit wins (`reputation_reward`). Gates Fixer Board contracts.
- **Banked credits** (NetVault): immune to trauma-bill loss on defeat — only credits on hand are at risk.

---

## Daily cycle

Leaving the hub (`L`, with Yes/No confirmation) triggers `_sleep_and_advance_day`:

- Day counter +1, full HP heal, all status effects cleared.
- **Resets**: `bought_round_today`, `rested_today`, `training_attempts_today`, `daily_kills` (Faction Heat), Hyphen8d's daily stock + market event (`roll_daily_market`).
- Faction Heat resolves: if any faction is hot, a 15% (`AMBUSH_CHANCE`) chance of a waking ambush.
- Prints the "Daily Data Feed" summary panel — now leads with two **City Conditions** rows (`engine/city.py`'s `random_weather()`/`random_headline()`, pulled from `content/city_conditions.json`: 12 weather lines, 17 fake headlines) before level, credits, reputation, HP, cleared effects, heat, kills by faction, and today's market event. Purely cosmetic — no mechanical effect, re-rolled fresh every sleep.

---

## Faction Heat

`engine/heat.py`. Killing **more than 3** (`HEAT_KILL_THRESHOLD`) enemies of the same faction in a single day (tracked in `Character.daily_kills`) makes that faction "hot." Only **Corp** and **Street Gang** are tracked (`HEAT_FACTIONS`) — they're the two with organized enough street presence to retaliate. While hot: 15% (`AMBUSH_CHANCE`) chance per Hunt Cache attempt of an ambush instead of the normal loot roll, and the same 15% roll once on waking. Resets every sleep. Intentionally has **no proactive in-game UI hint** — it's meant to be discovered through consequence, not shown as a meter (a deliberate genre-authentic choice, not an oversight — see conversation history / `GAME_DESIGN.md`).

---

## Save files

`engine/save.py`. One JSON file per character under `saves/` (gitignored), named by a sanitized slug of the character name (`re.sub(r"[^a-z0-9]+", "_", name.strip().lower())`, collapsing anything non-alphanumeric — prevents path traversal or crashes from stray characters like `/`).

**Autosave triggers**: on returning to the main menu after Leave (normal path), and via a `try/finally` around the hub loop in `main.py` — so a crash or Ctrl+C mid-session also saves whatever state existed at that point, not just clean exits.

**Known limitation**: `engine/ui.py`'s `read_choice` only ever reads a single keystroke, so numbered lists (Load Merc, Delete Merc, etc.) with 10+ entries can't select past position 9 through the normal UI. Tracked as a follow-up; not yet fixed as of Alpha 2.6.

---

## Content map — what to edit where

| To change... | Edit |
|---|---|
| NPC bios/dialogue | `content/npcs.json` |
| Contracts | `content/quests.json` |
| Undercity enemies + scavenge flavor | `content/encounters.json` |
| Pit gladiators | `content/pit.json` |
| Cyberware (normal) | `content/items.json` |
| Cyberware (Black Market) | `content/black_market.json` |
| Cyberware (Street-Modded) | `content/street_modded.json` |
| City Conditions (weather/headlines) | `content/city_conditions.json` |
| Consumable items | `content/usable_items.json` |
| Class base stats/flavor | `engine/character.py` (`CLASSES`) — **not** JSON, unlike the above |
| Class specials / RoboDOJO abilities | `engine/combat.py` (`CLASS_SPECIALS`, `ABILITIES`) — also Python, not JSON |
| RoboDOJO sparring drones | `engine/bestiary.py` (`TRAINING_DRONES`) — also Python, not JSON |
| Balance constants (costs, chances, caps) | Scattered as named constants near the top of the relevant `engine/*.py` module — grep for `_COST`, `_CHANCE`, `_CAP`, `_THRESHOLD` |

Everything under `content/` is intentionally data-only — adding or tuning an NPC, contract, enemy, or item is a JSON edit, no code change. Class templates, combat specials/abilities, and RoboDOJO's drones are the deliberate exceptions (kept in Python for now since they're small, bespoke, and tightly coupled to combat logic) — see `GAME_DESIGN.md` for the reasoning if that ever needs revisiting.
