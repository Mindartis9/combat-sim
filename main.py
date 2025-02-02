from characters.party_member import PartyMember
from characters.enemy import Enemy
from mechanics.combat import assign_default_actions
from mechanics.position import Position
from simulation.bulk_runner import analyze_combat_results, run_bulk_simulations
import random
import pandas as pd
from utils.visualization import generate_combat_report
# Define weapons as a dictionary for easy access
WEAPONS = {
    "longsword": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "slashing", "range": 5},
    "battleaxe": {"damage_dice": "1d10", "modifier": "STR", "damage_type": "slashing", "range": 5},
    "dagger": {"damage_dice": "1d4", "modifier": "DEX", "damage_type": "piercing", "range": 20},
    "bow": {"damage_dice": "1d8", "modifier": "DEX", "damage_type": "piercing", "range": 80},
    "claws": {"damage_dice": "1d6", "modifier": "STR", "damage_type": "slashing", "range": 5},
}


def assign_random_positions(entities, team, grid_size=5000, min_distance=50):
    """Assigns random 3D positions ensuring proper spacing."""
    if not entities:
        return

    base_x = random.randint(1000, grid_size - 1000)
    base_y = random.randint(1000, grid_size - 1000)
    base_z = 0

    if team == "enemy":
        base_x += random.randint(min_distance, min_distance + 50)
        base_y += random.randint(min_distance, min_distance + 50)

    entities[0].position = Position(base_x, base_y, base_z)

    for i in range(1, len(entities)):
        while True:
            new_x = entities[i - 1].position.x + random.randint(25, 50) * random.choice([-1, 1])
            new_y = entities[i - 1].position.y + random.randint(25, 50) * random.choice([-1, 1])
            new_z = 0 if entities[i].flying_speed == 0 else random.randint(10, 30)

            if 0 <= new_x <= grid_size and 0 <= new_y <= grid_size:
                entities[i].position = Position(new_x, new_y, new_z)
                break


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

# Assign actions & resistances
for entity in party + enemies:
    assign_default_actions(entity)

enemies[0].resistances = ["slashing"]  # Orc resists slashing
enemies[1].resistances = ["piercing"]  # Wyvern resists arrows

# Assign positions
assign_random_positions(party, "party")
assign_random_positions(enemies, "enemy")

# Run Simulation
combat_results = run_bulk_simulations(party + enemies, num_simulations=10)

# Ensure combat_results is valid
def validate_results(results):
    if not isinstance(results, pd.DataFrame) or results.empty:
        raise ValueError("Simulation returned invalid or empty results.")
    return results

combat_results = validate_results(combat_results)

# Run statistical analysis
analysis_results = analyze_combat_results(combat_results)

generate_combat_report(analysis_results, "combat_simulation_report.pdf")
