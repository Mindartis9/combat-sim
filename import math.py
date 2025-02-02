import random
import math
from mechanics.position import Position  # Import Position class from your file
import matplotlib.pyplot as plt
from characters.party_member import PartyMember
from characters.enemy import Enemy
from mechanics.combat import assign_default_actions
from simulation.bulk_runner import analyze_combat_results, run_bulk_simulations
import pandas as pd
from utils.visualization import generate_combat_report
from mechanics.position import initialize_positions, move_entities



# Define weapons as a dictionary for easy access
WEAPONS = {
    "longsword": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "slashing", "range": 5},
    "battleaxe": {"damage_dice": "1d10", "modifier": "STR", "damage_type": "slashing", "range": 5},
    "dagger": {"damage_dice": "1d4", "modifier": "DEX", "damage_type": "piercing", "range": 20},
    "bow": {"damage_dice": "1d8", "modifier": "DEX", "damage_type": "piercing", "range": 80},
    "claws": {"damage_dice": "1d6", "modifier": "STR", "damage_type": "slashing", "range": 5},
}

# Party Members
party = [
    PartyMember("Aragorn", "Fighter", "Champion", 5, {"STR": 18, "DEX": 14, "CON": 16, "INT": 10, "WIS": 12, "CHA": 13},
                18, 2, 30, 50, ["STR", "CON"], 3, [], [], "Medium", WEAPONS["longsword"], "melee"),
    PartyMember("Aarakocra Ranger", "Ranger", "Beastmaster", 5, {"STR": 12, "DEX": 18, "CON": 14, "INT": 10, "WIS": 14, "CHA": 10},
                16, 4, 25, 40, ["DEX", "WIS"], 3, [], [], "Medium", WEAPONS["bow"], "ranged", 50)
]

# Enemies
enemies = [
    Enemy("Orc", {"STR": 16, "DEX": 12, "CON": 14, "INT": 8, "WIS": 11, "CHA": 10}, 13, 1, 30, 30, ["STR", "CON"],
          2, [], [], "Medium", WEAPONS["claws"], "melee", True, 2),
    Enemy("Wyvern", {"STR": 19, "DEX": 10, "CON": 17, "INT": 5, "WIS": 12, "CHA": 6}, 15, 1, 20, 70, ["STR", "CON"],
          3, [], [], "Large", WEAPONS["claws"], "melee", False, 1, 60)
]

# Generate initial positions
initialize_positions(party, enemies)

print("Initial Camp A:", [(p.position.x, p.position.y, p.position.z) for p in party])
print("Initial Camp B:", [(p.position.x, p.position.y, p.position.z) for p in enemies])

# Move entities using their movement methods
move_entities(party, enemies, speed=30)

print("\nAfter Movement:")
print("Updated Camp A:", [(p.position.x, p.position.y, p.position.z) for p in party])
print("Updated Camp B:", [(p.position.x, p.position.y, p.position.z) for p in enemies])


