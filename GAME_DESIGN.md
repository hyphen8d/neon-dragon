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
   resolves and daily kill counts reset. The feed also leads with two
   **City Conditions** rows — a weather line and a fake news headline,
   both rolled from `content/city_conditions.json` via
   `engine/city.py`'s `roll_weather()`/`roll_headline()` and stored on
   `Character.current_weather`/`current_headline` so they persist for
   the whole day rather than being re-rolled every time they're
   displayed. No longer purely cosmetic: some conditions carry a `type`
   field that has a real mechanical effect elsewhere — see section 6
   (market-moving headlines) and section 7 (Tech Interference weather).
   Most entries still have no `type` and stay pure worldbuilding, so
   the city keeps feeling alive even on the days nothing mechanically
   happens.
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
- Leveling up is no longer fully deterministic: on top of the flat
  `STAT_GROWTH` (+3 Max HP, +1 Attack, +1 Defense, +1 Tech, full heal),
  the player picks one of Attack/Defense/Tech/**Charisma** to bump an
  extra point (`engine/leveling.py`'s `LEVEL_UP_BONUS_STATS`, prompted
  via `hotkey_prompt`) — the one build-crafting decision between
  character creation and cyberware, so two Street Samurai builds can
  diverge over a playthrough instead of following an identical curve.
  Charisma is deliberately left out of the automatic `STAT_GROWTH` (it
  stays opt-in rather than growing on every level regardless of build)
  but was previously missing an organic growth path entirely — its only
  source was skin-slot cyberware (Synth-Derm/Mirrorskin, and only one
  at a time). It now also grows via this level-up choice and via one of
  Buy a Round's stat outcomes (section 7), so a Charisma build is a real
  investment over time instead of being capped by whichever skin item
  you happened to buy.

## 5. NPCs

Data-driven (see CLAUDE.md) — not hardcoded. Each NPC has:
- Name, location, a short bio/flavor text
- A pool of dialogue lines (randomized on visit)
- Optionally: `conditional_lines` — an array of `{condition, min, line}`
  entries checked against the visiting Character (`engine/npcs.py`'s
  `_condition_value`/`random_line`); once a threshold is met (kills by
  faction, Quantum Cores held, contracts completed, Charisma, banked
  credits, being in debt, abilities learned), the NPC draws only from
  the eligible conditional pool instead of the generic one — the world
  reacting to what this specific merc has actually done, reusing
  existing Character state rather than adding new tracking just for
  flavor. Any `equipped_<item_id>` condition (e.g. `equipped_singularity_fist`)
  resolves against `Character.cyberware`'s values instead of a stat —
  NPCs physically reacting to whatever's currently bolted on, not just
  to accumulated history. `corp_kills`/`street_gang_kills` both carry a
  second, higher tier (15) on top of their original threshold (5) —
  eligible lines stack (both tiers' lines are in the pool together once
  the higher one's met), so the richer pool of reactions grows instead
  of replacing the earlier one. At 15 Street Gang kills specifically,
  Hyphen8d's line also functions as a hint that his hidden Street-Modded
  stash (section 6) just unlocked. `charisma` (a straight read of
  `character.charisma`) is the one condition several NPCs share at the
  same threshold — Static Rin, The Fixer, and Hyphen8d all open a
  noticeably warmer, secret-revealing pool at Charisma 8 — making
  Charisma feel like a real conversational stat across the roster, not
  a one-off Endr3am quirk.
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

Multi-step contract objects with a credit + XP + reputation reward. Two
contract boards: the **Fixer Board** (gated by Reputation, run by The
Fixer) and **Endr3am's board** at the Chrome Noodle Bar (gated by
Charisma). A third gate, **Level**, applies to contracts on either board
and is tied to the same tiers that unlock Undercity's tougher enemies
(`min_reputation`, `min_charisma`, `min_level` in the schema). 20
contracts total as of this pass (11 Fixer Board, 9 Chrome Noodle Bar) —
weighted toward the higher reputation/level end, since that's where a
repeat player ran out of new contracts first.
Beyond gating
Endr3am's board, Charisma also gets Hyphen8d's Hut prices down (2%
off per point, capped at 40%) — a general economic lever any class can
lean into, not tied to a specific class right now (see section 4). Some
contracts unlock new hub locations or NPCs — not used yet, but the hook
exists.

Five step types now, not just talk/kill: **fetch** (`target` is an item
id — checks the item is currently equipped in any cyberware slot, satisfied
either by buying it or by already owning it when the contract's accepted)
and **deliver** (`target` is a location, `item` is what's being handed
over — a Y/N confirmation, then the item is removed with no trade-in
refund, unlike a normal sell) are usually chained together, the way "A
Gift for Endr3am" fetches a Razor Claws from Hyphen8d's Hut and delivers
it to Endr3am. **pay** (`target` a location, `amount` a flat credit sum)
is a straight, all-or-nothing spend, confirmed the same way — "Debt
Collector" is a single-step example, "Clean Getaway" chains it after a
kill step instead of standing alone. talk/kill steps auto-advance
silently on the triggering event (`engine/quests.py`'s `notify_step`);
fetch/deliver/pay all touch something the player would rather not lose by
accident, so they either auto-advance only on a state the player already
chose (fetch) or require the Y/N confirm (deliver, pay) — see
`check_fetch_steps`/`pending_deliver_step`/`pending_pay_step` and
`engine/hub.py`'s `_check_deliver_and_pay`.

**coerce** (`target` a location, `min_charisma` the check, `fail_enemy`
the enemy name to fight on failure) is the Charisma-driven step type
that finally gives the stat real narrative weight beyond gating and
discounts: visiting the target location with the step active prompts a
Y/N attempt, showing the Charisma requirement up front so the player
isn't blindsided (also surfaced early — the contract board lists it as
a Risk column before the contract's even accepted). Meeting the
requirement advances the quest with a clean-talk outcome; falling short
and attempting anyway drops straight into `run_combat` against
`fail_enemy` — winning that fight still advances the quest (the job
gets done the hard way instead of the smooth way), losing just costs
the normal trauma bill and leaves the step pending for another attempt
later. `engine/quests.py`'s `pending_coerce_step` and
`engine/hub.py`'s `_check_coerce_step` follow the same
confirm-before-consequential-action shape as deliver/pay. "Silver
Tongue" (Chrome Noodle Bar) is the first contract to use it: coerce a
Scav Prowler in the Undercity out of a stolen datapad, then report back
to Endr3am.

**Dynamic economy** (`engine/shop.py`, rolled by `roll_daily_market` in
`_sleep_and_advance_day`): each day, Hyphen8d's Hut restocks to a
random 4 items out of the full catalog, and one cyberware slot gets a
random price event — a 10-30% discount or surge — that stacks with the
Charisma discount rather than replacing it. Both are stored on
`Character` (`market_stock`, `market_modifier`) and re-roll on sleep;
`get_daily_catalog`/`discounted_cost` are the read paths the shop UI
uses, so nothing else needs to know the roll happened. The event type
isn't always a coin flip: if today's headline (`Character.current_headline`,
rolled just before the market — see section 3) carries a `market_surge`
or `market_discount` type, that forces the event instead
(`HEADLINE_MARKET_EVENT` in `engine/shop.py`) — a corp crackdown or
supply-crunch headline actually drives the price spike it's describing,
rather than the news and the economy rolling independently.

**Quantum Cores** (`Character.quantum_cores`): a rare secondary
currency, LORD-gem-style. 4% drop chance (`QUANTUM_CORE_DROP_CHANCE`
in `hub.py`) on a successful Slice Drop Box crack and on a top-tier
Pit win only (gladiators carry a `tier` field in `content/pit.json`;
`visit_the_pit` computes the top tier from whatever's in the file
rather than a hardcoded number, so adding a new toughest gladiator —
as of this pass, tier 4's **Kingpin Draxx** — moves the drop
eligibility with it instead of requiring a code change). Both drop
narrations are deliberately unsettling rather than a plain "+1 Quantum
Core" — the core hums at a migraine-inducing frequency and reads as
grown, not manufactured, hinting it isn't something that should be
in a merc's pocket. Spent at a hidden **Black Market** inside
Hyphen8d's Hut
— reachable via an `[M]` hotkey deliberately left off the visible
Buy/Sell/Leave menu text, so it's undiscoverable without either
digging through the code or trying keys — selling four elite
prototype cyberware pieces (`content/black_market.json`, one per
slot, roughly double the top normal-tier bonus) priced only in Cores,
no Charisma discount or market event. Each piece's flavor text hints
at the same unexplained thread — purged corp archives, a rogue
intelligence watching through the net, a buried structure older than
the city on top of it — so the Black Market reads as tapping into
something dangerous and half-understood, not just a higher shop tier.
`engine/shop.py`'s `get_item` resolves ids across both catalogs so
equipped Black Market gear works everywhere normal gear does (loadout,
sell menu); `unequip` refunds whichever currency the item was
actually priced in.

**Datashards** (`content/datashards.json`, `engine/datashards.py`,
`Character.datashards`): a pure lore collectible, no stat payoff,
built to give the same unexplained thread the Black Market's flavor
text hints at — purged corp archives, a rogue intelligence on the
grid, the unsettling origin of Quantum Cores, a buried pre-city
structure — actual readable text instead of one-line flavor. A modest
12% chance (`DATASHARD_DROP_CHANCE`) to find one not already owned,
rolled on a clean Slice Drop Box crack or any Hunt Cache sweep that
doesn't end in an ambush (`maybe_find_datashard`, called from both
`_jack_in` and `_scavenge` in `engine/hub.py`) — deliberately a bonus
on top of the credit/Quantum Core payoff, never a competing roll.
Found shards are announced with their own `RARE`-styled panel, and
readable afterward from the hub's `[A]rchives` screen, rendered in a
jagged HEAVY-box panel with a fake signal-diagnostics header to read
as a corrupted terminal dump rather than a normal menu screen — the
same instinct as the Black Market's undiscoverable hotkey and Quantum
Cores' migraine-frequency flavor, worldbuilding that rewards curiosity
rather than being spelled out.

**Street-Modded stash**: a second hidden Hyphen8d's Hut menu, `[K]`,
unlocked once `street_gang_kills` (summed the same way as Faction
Heat/`conditional_lines`) hits 15 — `engine/shop.py`'s
`street_modded_unlocked`. Below the threshold, asking for it just gets
Hyphen8d turning the player away in character; above it, it opens the
same buy flow as the regular catalog (credits, Charisma discount,
daily market event all apply — unlike the Black Market, this one isn't
a separate currency), selling gear defined in
`content/street_modded.json`. The pattern is meant to generalize: any
future reputation-gated shop tier can reuse the same
threshold-check-then-hidden-hotkey shape.

**The Pit champion & Draxx's grudge match**: beating a gladiator
records a kill the same as any other enemy (`character.kills[name]`),
so beating **Kingpin Draxx** specifically is checked the same way as
any other kill-based `conditional_lines` threshold. Once
`character.kills["Kingpin Draxx"] >= 1`, `visit_the_pit`'s arrival text
swaps to acknowledging the player as reigning champion instead of the
default "the crowd wants blood" line. The Undercity also gains a new
weighted combat encounter, `draxx_grudge_match`
(`content/encounters.json`), gated by a `requires_kill` field
`engine/encounters.py`'s `_eligible` checks against `character.kills`
— Draxx and his crew occasionally ambush the player in Find a Fight or
the baseline Hunt Cache risk roll to reclaim his honor, buffed up from
his Pit stats. `requires_kill` is enemy-name-general, not
Draxx-specific, so any future "boss holds a grudge" encounter can reuse
it the same way.

## 7. Combat

Turn-based, text-narrated. Player picks an action each round (Attack,
Tech/Hack, Defend, Flee, plus Items whenever inventory is non-empty —
see `content/usable_items.json`). Simple damage formulas (stat + roll
vs. defense). Status effects are implemented: Stunned (skip your
action) and Bleeding (damage over time), inflicted by specific
enemies. Droid enemies (`is_droid: true` in encounter data — currently
just Rogue Drone) are immune to Bleed from any source, enforced
centrally in `status_effects.apply_effect`. `EFFECT_LABELS` in
`status_effects.py` bakes in an ASCII hazard-tag badge per effect (e.g.
`[ /// BLEED ]`), pre-wrapped in the WARNING theme color, so every
consumer gets the same styled badge for free. Deliberately plain ASCII,
no emoji — a cracked street terminal shouldn't render iOS glyphs; the
tags are meant to read like something a flickering CRT would actually
display.

Two usable-item effect types beyond heal/stun: `attack_buff` (a temporary
Attack boost — see `OVERCLOCK_ATTACK_BONUS` in `combat.py`, shared by the
plain Attack action, Samurai Slash, and Kill Switch via one
`_effective_attack` helper so the buff can't be missed in any of them) and
`guaranteed_flee` (ends the fight immediately, same code path as a
successful Flee). The Attack buff is high-risk/high-reward by design —
`status_effects.py` special-cases its expiry to inflict Bleed the moment
it wears off, the same module that already special-cases Bleed immunity
for droids.

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

**Buy a Round** (`engine/hub.py`'s `ROUND_ENCOUNTERS`/`_resolve_round_encounter`)
is a weighted micro-encounter table, not a flat three-way roll —
9 flavored narratives (a Scav pickpocket, a rambling netrunner, a
synth-arm-wrestling ganger, a war-story veteran, a smooth-talking fixer,
two gossip variants, two drunk variants) each precede their own
mechanical payoff (+1 permanent stat — Attack, Tech, Defense, or
Charisma — +2 reputation, or the `drunk` status effect), weighted to
land close to the old flat 12%/58%/30% split. The arm-wrestling win
also carries its own 10% downside roll (5 damage on top of the stat
gain) — a self-contained example of a narrative outcome with a nested
risk, worth reusing if other flat-roll mechanics get the same
narrative-table treatment later.

Charisma talks down the trauma bill from a lost fight: 3% off per
point, capped at 45%. A high-Charisma build still goes down in a
fight the same as anyone else, but pays less to get patched up.

**Intimidate**: a fifth action, `I[N]timidate`, that only appears once
`character.level - enemy.min_level >= INTIMIDATE_LEVEL_GAP` (3).
Deliberately reuses `min_level` — the level a player needs to be to
randomly run into a given enemy — as that enemy's difficulty tier,
rather than adding a parallel "enemy level" concept that Enemy didn't
otherwise need. Unlike Flee it's guaranteed and draws no counter-attack,
but only hands over the enemy's `credits_reward`; XP and reputation are
skipped entirely, so it's a way to skip tedious rematches against
low-level trash mobs once a character has badly outgrown them, not a
strictly-better Attack. `Enemy.min_level` defaults to `None` ("not
eligible") and is only populated for enemies pulled from the random
Undercity/ambush encounter pools (`engine/hub.py`'s
`_enemy_with_min_level`) — Pit gladiators, RoboDOJO sparring drones,
and quest-triggered fights (e.g. a "coerce" step's fail state) are all
freely repeatable at the player's own initiative, so leaving them
without a `min_level` was a deliberate exploit guard: without it, a
leveled-up character could Intimidate a low-tier Pit gladiator or a
pending coerce fight over and over for a risk-free credit farm, since
neither is gated the way Undercity's random encounters are.

**Tech Interference weather** (`Character.current_weather`, rolled once
per sleep — see section 3): when today's weather carries the
`tech_interference` type (a static storm, a solar flare, ash and ozone
in the air), every Tech/Hack-type action in the fight has a flat 10%
chance to fizzle completely, but deals +2 damage if it connects. This
covers the player's Tech action and a droid enemy's attack (`is_droid`
being the closest thing the engine has to an enemy-side "tech" action,
since enemies don't otherwise carry a distinct action type). An active
interference weather shows a `WEATHER: TECH INTERFERENCE` warning tag
at the top of the combat HUD (`_print_combat_hud` in `engine/combat.py`)
so the risk/reward is visible before committing to an action, not a
surprise after the fact.

## 8. Achievements & Milestones

Data-driven, like everything else — `content/achievements.json` defines
each achievement as `{id, name, description, category, condition}`, read
by `engine/achievements.py`'s `check_achievements(character, console)`.
Unlocked ids live on `Character.achievements` (permanent, saved). Calling
`check_achievements` is cheap and idempotent, so it's called opportunistically
after anything that could unlock one: combat victories
(`combat._handle_victory`), leveling up (`leveling.check_level_up`),
buying cyberware from Hyphen8d's Hut or the Black Market
(`hub._buy_cyberware` / `hub._visit_black_market`), and RoboDOJO sparring
(`hub._spar`). A newly unlocked achievement prints an
`ACHIEVEMENT UNLOCKED` panel in the Black Market's rare magenta styling —
meant to stand out from ordinary narration. `show_character_info` lists
everything unlocked so far in its own Achievements table.

This is also where the previously-floated **RoboDOJO belt ranks** idea
landed: gaining 6 Attack or Defense over your class's starting value
unlocks "Black Belt (Attack)" / "Black Belt (Defense)", each granting a
small permanent combat bonus (`BLACK_BELT_ATTACK_BONUS` /
`BLACK_BELT_DEFENSE_BONUS` in `engine/combat.py`, applied in
`_effective_attack` / `_effective_defense`) on top of whatever the raw
stat happens to be — the achievement is the belt, the bonus doesn't
disappear even if gear or effects change the stat later. Originally a
flat "reach 10" threshold, which was trivial for Street Samurai
(starting Attack 8, +2 away) and a much bigger ask for Netrunner
(starting Attack 3, +7 away) — the `stat_gain` condition type
(`engine/achievements.py`'s `_condition_met`, reading each class's
baseline from `engine.character.CLASSES`) measures the gain instead of
an absolute number, so both classes need the same amount of real
investment regardless of their starting spread.

Other achievements shipped as a first pass: **King Slayer** (defeat
Kingpin Draxx), **Street Sweeper** (15 Street Gang kills — reuses
`shop.street_gang_kills`'s counting logic), and **Chrome Junkie** (4
cyberware slots filled at once). More condition `type`s can be added to
`achievements._condition_met` as new milestones come up; nothing about
the engine assumes only these five.

## 9. The Undercity

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
Chrome Beast.

Higher tiers stack on top of the L1 pool rather than replacing it, so
without a counterbalance the original five low-tier enemies would stay
in the pick weight forever — by level 9 they made up roughly 59% of
`roll_combat_encounter`'s total weight, meaning most "endgame" Undercity
fights were still trash mobs. `engine/encounters.py`'s
`_combat_weight`/`OUTLEVEL_GRACE`/`OUTLEVEL_HALVING_CAP` fixes this by
halving an encounter's weight for every level the player is past a
2-level grace window above its `min_level` (floored at 1, capped at 4
halvings) — tapering instead of hard-excluding, so low-tier enemies
still turn up occasionally rather than vanishing outright (which is
also exactly what Intimidate, section 7, is for). `requires_kill`
encounters (the Draxx grudge match) are exempt from decay — they're
meant to persist as a callback fight, not fade out.

Hunt Cache's loot/nothing pool is six entries (three
loot, three nothing) for the same reason — no single flavor line
repeating every single low-risk sweep. `roll_combat_encounter`/
`roll_scavenge_encounter` take the full `Character` (not just level)
so an encounter can also gate on `requires_kill` — see section 6's
Pit champion/Draxx grudge match for the current example.

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

## 10. Aesthetic Rules

- Color palette: magenta/cyan/purple on black, used for headers, NPC
  names, and important numbers — not every line (avoid visual noise).
- Terse, noir-flavored narration. Short punchy sentences.
- ASCII/box-drawn panels for the hub menu and stat sheet.
- **Interaction Deck** (`engine/hub.py`: `_interaction_deck`,
  `_npc_panel`, `_station_data_panel`): the shared layout for a
  location's sub-screen, used by every location with a primary NPC —
  NetVault, Doc Wire's Clinic, RoboDOJO, Fixer Board, Chrome Noodle
  Bar, Hyphen8d's Hut, and Endr3am's Contract Booth (a sub-screen off
  Chrome Noodle Bar, not a separate hub location — he's the same
  bar's back booth, not somewhere you travel to). Every primary NPC
  interaction in the game goes through this same treatment now; there
  used to be three holdouts (Hyphen8d, Endr3am, and NetVault's
  secondary Agent Parker) that printed as plain text instead of a
  bordered panel — fixed for visual consistency. A `Table.grid(padding=
  (0, 4), expand=True)` splits the 120-column layout into an NPC
  dialogue panel (bio, a `Rule`, one quoted line) on the left and a
  titled operational-data panel (key/value rows, optionally an extra
  table like RoboDOJO's training costs) on the right. Anything that
  doesn't fit a compact side panel — the Fixer/Endr3am contract
  listings — stays its own full-width block below the deck instead of
  being squeezed in. A *secondary* NPC in the same room (Agent Parker)
  gets `_npc_panel` printed standalone, full-width, rather than paired
  in the two-column grid — visually distinct from the primary pairing
  without falling back to plain dim text.
- The main hub menu's Actions table surfaces active contract count
  inline on the Character Info row ("contracts (N active)") rather
  than as a new column on the persistent `print_status` HUD strip —
  that table is reused on every location screen, so adding a column
  there risked the fixed 120-column layout everywhere, not just the hub.

## 11. Build Phases (suggested order)

1. Character creation + save/load + main menu skeleton
2. Hub navigation between locations (no content yet, just movement)
3. Combat engine + Undercity random encounters
4. NPCs + dialogue system (data-driven)
5. Contracts
6. ~~Daily turn limit + day-end/reset cycle~~ — cut, see section 3
7. Hyphen8d's Hut economy + cyberware
8. Polish: color palette, ASCII panels, flavor text pass

## 12. Future Ideas (not built)

- ~~RoboDOJO belt ranks~~ — built, see section 8 (Achievements & Milestones).
- More achievement condition types beyond the first five shipped
  (e.g. contract streaks, faction standing, day-count milestones) —
  the engine (`achievements._condition_met`) already supports adding new
  `condition.type` values without touching the check/unlock/announce
  plumbing.

## Notes

This doc is a starting skeleton, not a spec to follow rigidly. Change
names, mechanics, and scope as the game takes shape in play. The point is
to keep updating this file as decisions get made, so it stays the source
of truth for what the game currently is.
