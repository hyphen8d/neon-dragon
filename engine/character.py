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
        "flavor": "Jacked into the net more than the street. Fights with code and drones.",
        "hp": 22,
        "attack": 3,
        "defense": 3,
        "tech": 9,
        "charisma": 4,
    },
    "Fixer": {
        "flavor": "Knows everyone, owes everyone, works every angle for a cut.",
        "hp": 24,
        "attack": 4,
        "defense": 4,
        "tech": 4,
        "charisma": 8,
    },
}


@dataclass
class Character:
    name: str
    char_class: str
    level: int = 1
    xp: int = 0
    max_hp: int = 20
    hp: int = 20
    attack: int = 5
    defense: int = 5
    tech: int = 5
    charisma: int = 5
    credits: int = 50
    cyberware: dict = field(default_factory=lambda: {slot: None for slot in CYBERWARE_SLOTS})

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
