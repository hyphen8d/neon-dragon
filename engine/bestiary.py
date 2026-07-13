"""Faction lookups across all enemy content sources (Undercity, The Pit,
RoboDOJO)."""

from __future__ import annotations

from engine.encounters import load_encounters
from engine.pit import load_gladiators

# RoboDOJO's sparring partners, keyed by which stat they train (see
# TRAINABLE_STATS in engine/hub.py). Flat, un-scaled stats — RoboDOJO has no
# level gate, so difficulty stays fixed while the player's own stats (and
# _train_cost's rising credit fee) do the real gatekeeping over time. Not in
# HEAT_FACTIONS, so sparring never builds Faction Heat.
TRAINING_DRONES: dict[str, dict] = {
    "attack": {
        "name": "Melee Drone",
        "faction": "Training",
        "hp": 18,
        "attack": 5,
        "defense": 3,
        "credits_reward": 0,
        "xp_reward": 8,
        "is_droid": True,
        "scan_desc": "Chassis: RoboDOJO sparring rig. Padded knuckles, pulls every swing.",
    },
    "defense": {
        "name": "Heavy-Frame Drone",
        "faction": "Training",
        "hp": 20,
        "attack": 6,
        "defense": 3,
        "credits_reward": 0,
        "xp_reward": 8,
        "is_droid": True,
        "scan_desc": "Chassis: Reinforced sparring frame. Leans in slow, telegraphs every hit.",
    },
    "tech": {
        "name": "Sparring ICE",
        "faction": "Training",
        "hp": 16,
        "attack": 5,
        "defense": 4,
        "credits_reward": 0,
        "xp_reward": 8,
        "is_droid": True,
        "scan_desc": "Signature: Simulated firewall routine. Runs the same three attack patterns on loop.",
    },
}


def enemy_faction(name: str) -> str:
    for encounter in load_encounters():
        enemy = encounter.get("enemy")
        if enemy and enemy["name"] == name:
            return enemy.get("faction", "Unknown")
    for gladiator in load_gladiators():
        if gladiator["name"] == name:
            return gladiator.get("faction", "Unknown")
    for drone in TRAINING_DRONES.values():
        if drone["name"] == name:
            return drone.get("faction", "Unknown")
    return "Unknown"
