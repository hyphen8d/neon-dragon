"""Hub menu / navigation between Neo Meridian locations."""

from __future__ import annotations

import random

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.table import Table

from engine.bestiary import enemy_faction
from engine.character import CYBERWARE_SLOTS, Character
from engine.combat import run_combat
from engine.encounters import roll_encounter
from engine.help import show_help
from engine.leveling import xp_for_next_level
from engine.npcs import npc_at, random_line
from engine.pit import load_gladiators
from engine.quests import (
    accept_quest,
    available_quests,
    current_step,
    get_quest,
    locked_quests,
    notify_step,
    print_quest_result,
)
from engine.shop import buy_and_equip, get_item, load_cyberware, sell_back_value, unequip
from engine.status_effects import EFFECT_LABELS, cure_all

console = Console(highlight=False)

# Location -> one-line flavor for the hub menu table. Real content (rest,
# shop, combat, etc.) is wired up location by location in later phases.
LOCATIONS: dict[str, str] = {
    "Chrome Noodle Bar": "Rest, heal, and hear rumors over synth-noodles and static pop.",
    "Undercity": "Random encounters — gang fights, scavenger loot, drone ambushes.",
    "NetVault": "Deposit and withdraw credits, safe from death-loss.",
    "Chop Shop": "Buy and sell gear and cyberware.",
    "Doc Wire's Clinic": "Heal HP for credits, cure status effects.",
    "The Dojo": "Train stats, learn new abilities.",
    "The Pit": "PvE gladiator fights for reputation and credits.",
    "Fixer Board": "Leaderboard and posted contracts.",
}

# Location -> longer arrival description, shown when you actually step
# into the place (as opposed to the short blurb in the hub menu table).
LOCATION_DESCRIPTIONS: dict[str, str] = {
    "Chrome Noodle Bar": (
        "Steam curls off the noodle vats under a buzzing pink sign. Synth pop "
        "bleeds from a cracked speaker, and every stool's got a story nobody's "
        "telling straight."
    ),
    "Undercity": (
        "Sublevel streets, sodium light dying orange through the smog. Water "
        "drips from a hundred unseen pipes. Something always seems to be "
        "watching from the dark."
    ),
    "NetVault": (
        "Chrome and glass, cold as a server room because it is one. "
        "Biometric scanners hum behind a counter that's seen a thousand "
        "transactions and trusts none of them."
    ),
    "Chop Shop": (
        "Wires hang from the ceiling like vines. Half-built limbs sit in "
        "bins marked in a shorthand only the shop understands. Smells like "
        "solder and ozone."
    ),
    "Doc Wire's Clinic": (
        "A converted shipping container wired for surgery. Trauma gurneys, "
        "mismatched monitors, and a fridge that's definitely not for food."
    ),
    "The Dojo": (
        "Bare concrete, scorch marks on the walls, a ring of cracked "
        "mirrors. Somewhere a heavy bag swings on its own, still recovering "
        "from the last session."
    ),
    "The Pit": (
        "A sunken arena ringed by chain-link and floodlights, a chanting "
        "crowd lost in the dark beyond. The sand's stained in ways bleach "
        "won't fix."
    ),
    "Fixer Board": (
        "A cracked terminal bolted to a brick wall, scrolling contracts in "
        "glitchy green text. Torn paper flyers underneath it, decades out "
        "of date."
    ),
}


def print_status(character: Character) -> None:
    console.print(
        f"[bright_cyan]{character.name}[/bright_cyan] "
        f"[dim](Lvl {character.level} {character.char_class})[/dim]   "
        f"HP [bold]{character.hp}/{character.max_hp}[/bold]   "
        f"Credits [bold yellow]{character.credits}[/bold yellow]   "
        f"Banked [bold yellow]{character.banked_credits}[/bold yellow]"
    )


def print_hub_menu(character: Character, location_names: list[str]) -> None:
    console.rule("[bright_magenta]Neo Meridian[/bright_magenta]")
    print_status(character)
    console.print()

    locations = Table(
        title="[bold bright_magenta]Locations[/bold bright_magenta]",
        border_style="bright_cyan",
        show_header=False,
    )
    locations.add_column("#", justify="right", style="bright_magenta")
    locations.add_column("Location", style="bold white")
    locations.add_column("Description", style="dim")
    for i, name in enumerate(location_names, start=1):
        locations.add_row(str(i), name, LOCATIONS[name])
    console.print(locations)

    actions = Table(
        title="[bold bright_magenta]Actions[/bold bright_magenta]",
        border_style="bright_cyan",
        show_header=False,
    )
    actions.add_column("#", justify="right", style="bright_magenta")
    actions.add_column("Action", style="bold white")
    actions.add_column("Description", style="dim")
    actions.add_row("i", "Character Info", "View your full stats, gear, contracts, and kills.")
    actions.add_row("?", "Help", "Open the player guide.")
    actions.add_row("0", "Leave", "Head home and save your progress.")
    console.print(actions)


def print_arrival(location: str) -> None:
    console.print()
    console.print(
        Panel(
            LOCATION_DESCRIPTIONS[location],
            title=f"[bold bright_magenta]{location}[/bold bright_magenta]",
            border_style="bright_cyan",
            padding=(0, 2),
        )
    )


def print_menu_divider(label: str) -> None:
    """Visually separate in-character scene/dialogue above from the
    out-of-character menu/mechanics below."""
    console.print()
    console.rule(f"[dim]{label}[/dim]", style="dim")


def visit_undercity(character: Character) -> None:
    print_arrival("Undercity")
    encounter = roll_encounter()
    console.print(f"[dim]{encounter['intro']}[/dim]")

    if encounter["type"] == "combat":
        run_combat(character, encounter["enemy"])
    elif encounter["type"] == "loot":
        low, high = encounter["credits"]
        amount = random.randint(low, high)
        character.credits += amount
        console.print(f"[bold yellow]+{amount} credits.[/bold yellow]")
    # "nothing" encounters just print their flavor line above.


def _deposit(character: Character) -> None:
    if character.credits <= 0:
        console.print("[dim]Nothing on hand to deposit.[/dim]")
        return
    amount = IntPrompt.ask(f"Deposit how much? (0 to cancel, up to {character.credits})")
    if amount <= 0:
        return
    if amount > character.credits:
        console.print("[red]You don't have that much on hand.[/red]")
        return
    character.credits -= amount
    character.banked_credits += amount
    console.print(f"[bold yellow]{amount} credits deposited.[/bold yellow] Banked: {character.banked_credits}")


def _withdraw(character: Character) -> None:
    if character.banked_credits <= 0:
        console.print("[dim]Nothing banked to withdraw.[/dim]")
        return
    amount = IntPrompt.ask(f"Withdraw how much? (0 to cancel, up to {character.banked_credits})")
    if amount <= 0:
        return
    if amount > character.banked_credits:
        console.print("[red]You don't have that much banked.[/red]")
        return
    character.banked_credits -= amount
    character.credits += amount
    console.print(f"[bold yellow]{amount} credits withdrawn.[/bold yellow] On hand: {character.credits}")


def visit_netvault(character: Character) -> None:
    print_arrival("NetVault")

    npc = npc_at("NetVault")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Banking")
    for result in notify_step(character, "talk", "NetVault"):
        print_quest_result(console, character, result)

    console.print(
        f"On hand: [bold yellow]{character.credits}[/bold yellow]   "
        f"Banked: [bold yellow]{character.banked_credits}[/bold yellow] [dim](safe from death-loss)[/dim]"
    )

    action = Prompt.ask(
        "[bright_magenta]1[/bright_magenta] Deposit  [bright_magenta]2[/bright_magenta] Withdraw  "
        "[bright_magenta]0[/bright_magenta] Leave",
        choices=["0", "1", "2"],
        show_choices=False,
    )
    if action == "1":
        _deposit(character)
    elif action == "2":
        _withdraw(character)


HEAL_COST_PER_HP = 2


CURE_COST = 15


def _offer_cure(character: Character) -> None:
    if not character.status_effects:
        return

    labels = ", ".join(EFFECT_LABELS.get(e, e) for e in character.status_effects)
    console.print(f"\n[yellow]Active effects:[/yellow] {labels}")

    action = Prompt.ask(
        f"Clear those for {CURE_COST} credits? [bright_magenta]1[/bright_magenta] Yes  "
        f"[bright_magenta]0[/bright_magenta] No",
        choices=["0", "1"],
        show_choices=False,
    )
    if action != "1":
        return
    if character.credits < CURE_COST:
        console.print("[red]Not enough credits for that.[/red]")
        return

    character.credits -= CURE_COST
    cured = cure_all(character)
    console.print(f"[bold bright_magenta]Cleared {cured} status effect(s).[/bold bright_magenta] -{CURE_COST} credits.")


def visit_doc_wires_clinic(character: Character) -> None:
    print_arrival("Doc Wire's Clinic")

    npc = npc_at("Doc Wire's Clinic")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Clinic Menu")
    for result in notify_step(character, "talk", "Doc Wire's Clinic"):
        print_quest_result(console, character, result)

    _offer_cure(character)

    missing = character.max_hp - character.hp
    if missing <= 0:
        console.print("\n[dim]You're already at full health. Doc Wire waves you off.[/dim]")
        return

    console.print(
        f"\nHP: [bold]{character.hp}/{character.max_hp}[/bold]   "
        f"Patch-up rate: {HEAL_COST_PER_HP} credits/HP"
    )

    max_affordable = min(missing, character.credits // HEAL_COST_PER_HP)
    if max_affordable <= 0:
        console.print("[red]You can't afford so much as a bandage right now.[/red]")
        return

    amount = IntPrompt.ask(f"Heal how much HP? (0 to cancel, up to {max_affordable})")
    if amount <= 0:
        return
    if amount > max_affordable:
        console.print("[red]You can't afford that much healing.[/red]")
        return

    cost = amount * HEAL_COST_PER_HP
    character.hp += amount
    character.credits -= cost
    console.print(
        f"[bold bright_magenta]Patched up.[/bold bright_magenta] "
        f"HP {character.hp}/{character.max_hp}. -{cost} credits."
    )


TRAIN_COST_PER_POINT = 40

TRAINABLE_STATS: dict[str, tuple[str, str]] = {
    "1": ("attack", "Attack"),
    "2": ("defense", "Defense"),
    "3": ("tech", "Tech"),
    "4": ("charisma", "Charisma"),
}


def visit_the_dojo(character: Character) -> None:
    print_arrival("The Dojo")
    console.print("[dim]No trainer in sight — just a chalkboard bolted to the wall with a price list.[/dim]")

    print_menu_divider("Training")
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Stat", style="bold white")
    table.add_column("Current", justify="right")
    for key, (attr, label) in TRAINABLE_STATS.items():
        table.add_row(key, label, str(getattr(character, attr)))
    console.print(table)
    console.print(f"[dim]{TRAIN_COST_PER_POINT} credits per +1.[/dim]")

    choice = Prompt.ask(
        "Train which stat? (0 to leave)",
        choices=["0", *TRAINABLE_STATS.keys()],
        show_choices=False,
    )
    if choice == "0":
        return
    if character.credits < TRAIN_COST_PER_POINT:
        console.print("[red]Not enough credits to train right now.[/red]")
        return

    attr, label = TRAINABLE_STATS[choice]
    character.credits -= TRAIN_COST_PER_POINT
    setattr(character, attr, getattr(character, attr) + 1)
    console.print(
        f"[bold bright_magenta]{label} increased to {getattr(character, attr)}.[/bold bright_magenta] "
        f"-{TRAIN_COST_PER_POINT} credits."
    )


def visit_the_pit(character: Character) -> None:
    print_arrival("The Pit")
    console.print("[dim]The crowd wants blood. Pick your match.[/dim]")

    print_menu_divider("The Ring")
    gladiators = load_gladiators()
    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Gladiator", style="bold white")
    table.add_column("HP", justify="right")
    table.add_column("Reward", justify="right")
    for i, g in enumerate(gladiators, start=1):
        table.add_row(str(i), g["name"], str(g["hp"]), f"{g['credits_reward']}cr / {g['reputation_reward']}rep")
    console.print(table)

    choice = Prompt.ask(
        "Step into the ring? (0 to back out)",
        choices=[str(i) for i in range(len(gladiators) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    gladiator = gladiators[int(choice) - 1]
    console.print(f"\n[dim]{gladiator['intro']}[/dim]")
    enemy_data = {k: v for k, v in gladiator.items() if k not in ("id", "intro")}
    run_combat(character, enemy_data)


REST_THRESHOLD = 0.5  # free rest tops you up to this fraction of max HP, no further


def visit_chrome_noodle_bar(character: Character) -> None:
    print_arrival("Chrome Noodle Bar")

    npc = npc_at("Chrome Noodle Bar")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    rest_floor = int(character.max_hp * REST_THRESHOLD)
    if character.hp >= rest_floor:
        console.print("\n[dim]You're rested enough already. No need to linger.[/dim]")
    else:
        healed = rest_floor - character.hp
        character.hp = rest_floor
        console.print(
            f"\n[bold bright_magenta]You crash in a booth for a while, noodles going cold.[/bold bright_magenta] "
            f"+{healed} HP, on the house."
        )

    console.print(
        "\n[dim]Rin leans in, voice low — she's got side work for the right kind of "
        "smile, if you're charming enough to earn it.[/dim]"
    )

    print_menu_divider("Contract Board")
    for result in notify_step(character, "talk", "Chrome Noodle Bar"):
        print_quest_result(console, character, result)
    _browse_contract_board(character, "Chrome Noodle Bar")


def _browse_contract_board(character: Character, board: str) -> None:
    active_ids = [
        quest_id for quest_id in character.active_quests if get_quest(quest_id).get("board", "Fixer Board") == board
    ]
    if active_ids:
        console.print("\n[bright_magenta]Active contracts:[/bright_magenta]")
        for quest_id in active_ids:
            quest = get_quest(quest_id)
            step = current_step(character, quest_id)
            console.print(f"  [bold]{quest['title']}[/bold] — {step['description']}")

    locked = locked_quests(character, board)
    if locked:
        console.print(
            f"\n[dim]{len(locked)} more contract(s) here need more reputation or charisma "
            f"before they'll be offered.[/dim]"
        )

    open_quests = available_quests(character, board)
    if not open_quests:
        console.print("\n[dim]No new contracts posted right now.[/dim]")
        return

    console.print("\n[bright_magenta]Open contracts:[/bright_magenta]")
    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Title", style="bold white")
    table.add_column("Hook", style="dim")
    for i, quest in enumerate(open_quests, start=1):
        table.add_row(str(i), quest["title"], quest["hook"])
    console.print(table)

    choice = Prompt.ask(
        "Take a contract? (0 to skip)",
        choices=[str(i) for i in range(len(open_quests) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    chosen_quest = open_quests[int(choice) - 1]
    accept_quest(character, chosen_quest["id"])
    console.print(f"\n[bold bright_magenta]Contract accepted:[/bold bright_magenta] {chosen_quest['title']}")
    console.print(f"  {chosen_quest['steps'][0]['description']}")


def visit_fixer_board(character: Character) -> None:
    print_arrival("Fixer Board")

    npc = npc_at("Fixer Board")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Contract Board")
    for result in notify_step(character, "talk", "Fixer Board"):
        print_quest_result(console, character, result)
    _browse_contract_board(character, "Fixer Board")


def build_loadout_table(character: Character, title: str | None = None) -> Table:
    table = Table(title=title, border_style="bright_cyan", show_header=False)
    table.add_column("Slot", style="cyan")
    table.add_column("Installed", style="bold white")
    for slot in CYBERWARE_SLOTS:
        item_id = character.cyberware[slot]
        installed = get_item(item_id)["name"] if item_id else "empty"
        table.add_row(slot.capitalize(), installed)
    return table


def print_loadout(character: Character) -> None:
    console.print("\n[bright_magenta]Your chrome:[/bright_magenta]")
    console.print(build_loadout_table(character))


def print_catalog(catalog: list[dict]) -> None:
    console.print("\n[bright_magenta]For sale:[/bright_magenta]")
    table = Table(border_style="bright_cyan")
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Item", style="bold white")
    table.add_column("Slot")
    table.add_column("Bonus")
    table.add_column("Cost", justify="right")
    table.add_column("Flavor", style="dim")
    for i, item in enumerate(catalog, start=1):
        table.add_row(
            str(i),
            item["name"],
            item["slot"].capitalize(),
            f"+{item['bonus']} {item['stat']}",
            str(item["cost"]),
            item["flavor"],
        )
    console.print(table)


def _buy_cyberware(character: Character) -> None:
    catalog = load_cyberware()
    print_catalog(catalog)

    choice = Prompt.ask(
        "Buy which item? (0 to cancel)",
        choices=[str(i) for i in range(len(catalog) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    item = catalog[int(choice) - 1]
    old_id = character.cyberware[item["slot"]]
    trade_in = sell_back_value(get_item(old_id)) if old_id else 0
    if character.credits + trade_in < item["cost"]:
        console.print("[red]Not enough credits for that, even with a trade-in.[/red]")
        return

    buy_and_equip(character, item["id"])
    if old_id:
        console.print(f"[dim]{get_item(old_id)['name']} pulled and sold back for parts.[/dim]")
    console.print(
        f"[bold bright_magenta]Installed:[/bold bright_magenta] {item['name']} "
        f"(+{item['bonus']} {item['stat']})"
    )


def _sell_cyberware(character: Character) -> None:
    equipped_slots = [slot for slot in CYBERWARE_SLOTS if character.cyberware[slot]]
    if not equipped_slots:
        console.print("[dim]Nothing installed to sell.[/dim]")
        return

    table = Table(border_style="bright_cyan", show_header=False)
    table.add_column("#", justify="right", style="bright_magenta")
    table.add_column("Slot", style="bold white")
    table.add_column("Installed", style="dim")
    for i, slot in enumerate(equipped_slots, start=1):
        item = get_item(character.cyberware[slot])
        table.add_row(str(i), slot.capitalize(), f"{item['name']} (sells for {sell_back_value(item)})")
    console.print(table)

    choice = Prompt.ask(
        "Sell which item? (0 to cancel)",
        choices=[str(i) for i in range(len(equipped_slots) + 1)],
        show_choices=False,
    )
    if choice == "0":
        return

    slot = equipped_slots[int(choice) - 1]
    item = unequip(character, slot)
    console.print(f"[bold yellow]{item['name']} sold for {sell_back_value(item)} credits.[/bold yellow]")


def visit_chop_shop(character: Character) -> None:
    print_arrival("Chop Shop")

    npc = npc_at("Chop Shop")
    console.print(f"[bold cyan]{npc['name']}[/bold cyan] [dim]— {npc['bio']}[/dim]")
    console.print(f"  {random_line(npc)}")

    print_menu_divider("Chop Shop Menu")
    for result in notify_step(character, "talk", "Chop Shop"):
        print_quest_result(console, character, result)

    print_loadout(character)

    action = Prompt.ask(
        "[bright_magenta]1[/bright_magenta] Buy  [bright_magenta]2[/bright_magenta] Sell  "
        "[bright_magenta]0[/bright_magenta] Leave",
        choices=["0", "1", "2"],
        show_choices=False,
    )
    if action == "1":
        _buy_cyberware(character)
    elif action == "2":
        _sell_cyberware(character)


def _themed_table(title: str) -> Table:
    table = Table(title=f"[bold bright_magenta]{title}[/bold bright_magenta]", border_style="bright_cyan", show_header=False)
    table.add_column("Label", style="cyan")
    table.add_column("Value", style="bold white")
    return table


def show_character_info(character: Character) -> None:
    console.print()
    console.rule(f"[bold bright_magenta]{character.name}[/bold bright_magenta] [dim]— {character.char_class}[/dim]")
    console.print()

    attributes = _themed_table("Attributes")
    attributes.add_row("Level", str(character.level))
    attributes.add_row("XP", f"{character.xp}/{xp_for_next_level(character)}")
    attributes.add_row("HP", f"{character.hp}/{character.max_hp}")
    attributes.add_row("Attack", str(character.attack))
    attributes.add_row("Defense", str(character.defense))
    attributes.add_row("Tech", str(character.tech))
    attributes.add_row("Charisma", str(character.charisma))

    economy = _themed_table("Economy")
    economy.add_row("Credits", str(character.credits))
    economy.add_row("Banked", str(character.banked_credits))

    contracts = _themed_table("Reputation & Contracts")
    contracts.add_row("Reputation", str(character.reputation))
    contracts.add_row("Contracts active", str(len(character.active_quests)))
    contracts.add_row("Contracts completed", str(len(character.completed_quests)))

    loadout = build_loadout_table(character, title="[bold bright_magenta]Chrome[/bold bright_magenta]")

    effects = _themed_table("Status Effects")
    if character.status_effects:
        for effect, remaining in character.status_effects.items():
            effects.add_row(EFFECT_LABELS.get(effect, effect), f"{remaining} round(s)")
    else:
        effects.add_row("No active effects", "")

    grid = Table.grid(padding=(0, 2))
    grid.add_column()
    grid.add_column()
    grid.add_row(attributes, economy)
    grid.add_row(contracts, loadout)
    console.print(grid)
    console.print(effects)

    kills = _themed_table("Kills by Faction")
    if character.kills:
        by_faction: dict[str, list[tuple[str, int]]] = {}
        for name, count in character.kills.items():
            by_faction.setdefault(enemy_faction(name), []).append((name, count))
        for faction in sorted(by_faction):
            entries = sorted(by_faction[faction])
            total = sum(count for _, count in entries)
            kills.add_row(f"[bold]{faction}[/bold]", f"[bold]{total}[/bold]")
            for name, count in entries:
                kills.add_row(f"  {name}", str(count))
    else:
        kills.add_row("No kills yet", "")
    console.print(kills)


def enter_hub(character: Character) -> None:
    location_names = list(LOCATIONS.keys())
    while True:
        console.print()
        print_hub_menu(character, location_names)
        choice = Prompt.ask(
            "Where to?",
            choices=[str(i) for i in range(len(location_names) + 1)] + ["?", "i"],
            show_choices=False,
        )
        if choice == "0":
            console.print("[dim]You head back, credits and gear safe... for now.[/dim]")
            return
        if choice == "?":
            show_help(console)
            continue
        if choice == "i":
            show_character_info(character)
            continue

        chosen = location_names[int(choice) - 1]

        if chosen == "Undercity":
            visit_undercity(character)
        elif chosen == "Chrome Noodle Bar":
            visit_chrome_noodle_bar(character)
        elif chosen == "Fixer Board":
            visit_fixer_board(character)
        elif chosen == "Chop Shop":
            visit_chop_shop(character)
        elif chosen == "NetVault":
            visit_netvault(character)
        elif chosen == "Doc Wire's Clinic":
            visit_doc_wires_clinic(character)
        elif chosen == "The Dojo":
            visit_the_dojo(character)
        elif chosen == "The Pit":
            visit_the_pit(character)
        else:
            raise ValueError(f"No hub handler wired up for location: {chosen!r}")
