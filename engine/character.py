"""Character data model: stats, class templates, and (de)serialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

CYBERWARE_SLOTS = ("arm", "eyes", "spine", "skin")

# Starting stats per class. Numbers are a first pass — rebalance in playtesting.
CLASSES: dict[str, dict] = {
    "Street Samurai": {
        "flavor": "Chrome-plated muscle. Lives by the blade, augmented to the bone.",
        "hp": 30,
        "attack": 8,
        "defense": 6,
        "tech": 2,
        "charisma": 3,
    },
    "Netrunner": {
        # Kept short enough to fit the class-select table's Flavor column
        # on one line at the game's fixed 120-column width — see main.py's
        # choose_class(), which is the only place CLASSES[...]['flavor'] renders.
        "flavor": "More wired into the net than the street. Fights with code.",
        "hp": 22,
        "attack": 3,
        "defense": 3,
        "tech": 9,
        "charisma": 4,
    },
    # Grifter (charisma-focused) is pulled for now, pending a redesigned
    # third class. Charisma itself stays a live stat — it still gates
    # Endr3am's contracts, discounts Hyphen8d's Hut, and softens the
    # trauma bill — it's just not any class's headline stat right now.
}


@dataclass
class Character:
    name: str
    char_class: str
    level: int = 1
    day: int = 1
    xp: int = 0
    max_hp: int = 20
    hp: int = 20
    attack: int = 5
    defense: int = 5
    tech: int = 5
    charisma: int = 5
    credits: int = 50
    banked_credits: int = 0
    reputation: int = 0
    quantum_cores: int = 0  # rare secondary currency — see engine/shop.py's Black Market
    cyberware: dict = field(default_factory=lambda: {slot: None for slot in CYBERWARE_SLOTS})
    active_quests: dict = field(default_factory=dict)  # quest_id -> current step index
    completed_quests: list = field(default_factory=list)
    status_effects: dict = field(default_factory=dict)  # effect name -> rounds remaining
    kills: dict = field(default_factory=dict)  # enemy name -> times defeated
    inventory: list = field(default_factory=list)  # usable_item ids, one entry per copy carried
    daily_kills: dict = field(default_factory=dict)  # faction -> kills today, resets on sleep (see engine/heat.py)
    market_modifier: dict = field(default_factory=dict)  # today's price event, see engine/shop.py
    market_stock: list = field(default_factory=list)  # item ids Hyphen8d's Hut carries today
    bought_round_today: bool = False  # Chrome Noodle Bar's Buy a round, once per day, resets on sleep
    learned_abilities: list = field(default_factory=list)  # RoboDOJO ability ids, permanent, independent of class
    rested_today: bool = False  # Chrome Noodle Bar's free rest, once per day, resets on sleep
    training_attempts_today: int = 0  # RoboDOJO sparring bouts used today, resets on sleep

    @classmethod
    def new(cls, name: str, char_class: str) -> "Character":
        base = CLASSES[char_class]
        return cls(
            name=name,
            char_class=char_class,
            max_hp=base["hp"],
            hp=base["hp"],
            attack=base["attack"],
            defense=base["defense"],
            tech=base["tech"],
            charisma=base["charisma"],
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        return cls(**data)


def hp_style(hp: int, max_hp: int) -> str:
    """Rich style name for displaying HP, colored by danger level."""
    if max_hp <= 0:
        return "bold white"
    ratio = hp / max_hp
    if ratio <= 0.25:
        return "bold red"
    if ratio <= 0.5:
        return "bold yellow"
    return "bold white"
