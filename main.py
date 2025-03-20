from characters.party_member import PartyMember
from characters.enemy import Enemy
from mechanics.combat import assign_default_actions
from simulation.bulk_runner import analyze_combat_results, run_bulk_simulations
import pandas as pd
from utils.visualization import generate_combat_report
from mechanics.position import initialize_positions
import os
from utils.regressionanalysis import RegressionAnalysis
from utils.montecarlo import MonteCarloSimulation

# Define weapons as a dictionary for easy access
WEAPONS = {
    "Club": {"damage_dice": "1d4", "modifier": "STR", "damage_type": "bludgeoning", "range": 5},
    "Dagger": {"damage_dice": "1d4", "modifier": "DEX", "damage_type": "piercing", "range": 5},
    "Greatclub": {"damage_dice": "1d8", "modifier": "DEX", "damage_type": "bludgeoning", "range": 5},
    "Handaxe": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "slashing", "range": 5},
    "Javelin": {"damage_dice": "1d6", "modifier": "STR", "damage_type": "piercing", "range": 5},
    "Light hammer": {"damage_dice": "1d4", "modifier": "STR", "damage_type": "bludgeoning", "range": 5},
    "Mace": {"damage_dice": "1d6", "modifier": "STR", "damage_type": "bludgeoning", "range": 5},
    "Quarterstaff": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "bludgeoning", "range": 5},
    "Sickle": {"damage_dice": "1d4", "modifier": "DEX", "damage_type": "slashing", "range": 5},
    "Spear": {"damage_dice": "1d6", "modifier": "STR", "damage_type": "piercing", "range": 5},
    "Crossbow, light": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "piercing", "range": 80},
    "Dart": {"damage_dice": "1d14", "modifier": "DEX", "damage_type": "piercing", "range": 20},
    "Shortbow": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "piercing", "range": 80},
    "Sling": {"damage_dice": "1d4", "modifier": "DEX", "damage_type": "bludgeoning", "range": 30},
    "Battleaxe": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "slashing", "range": 5},
    "Flail": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "bludgeoning", "range": 5},
    "Glaive": {"damage_dice": "1d10", "modifier": "STR", "damage_type": "slashing", "range": 10},
    "Greataxe": {"damage_dice": "1d12", "modifier": "DEX", "damage_type": "slashing", "range": 5},
    "Greatsword": {"damage_dice": "2d6", "modifier": "DEX", "damage_type": "slashing", "range": 5},
    "Halberd": {"damage_dice": "1d10", "modifier": "STR", "damage_type": "slashing", "range": 10},
    "Lance": {"damage_dice": "1d12", "modifier": "STR", "damage_type": "piercing", "range": 10},
    "Longsword": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "slashing", "range": 5},
    "Maul": {"damage_dice": "2d6", "modifier": "DEX", "damage_type": "bludgeoning", "range": 5},
    "Morningstar": {"damage_dice": "1d8", "modifier": "DEX", "damage_type": "piercing", "range": 5},
    "Pike": {"damage_dice": "1d10", "modifier": "STR", "damage_type": "piercing", "range": 10},
    "Rapier": {"damage_dice": "1d8", "modifier": "DEX", "damage_type": "piercing", "range": 5},
    "Scimitar": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "slashing", "range": 5},
    "Shortsword": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "piercing", "range": 5},
    "Trident": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "piercing", "range": 5},
    "War pick": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "piercing", "range": 5},
    "Warhammer": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "bludgeoning", "range": 5},
    "Whip": {"damage_dice": "1d4", "modifier": "DEX", "damage_type": "slashing", "range": 10},
    "Blowgun": {"damage_dice": "1d1", "modifier": "DEX", "damage_type": "piercing", "range": 25},
    "Crossbow, hand": {"damage_dice": "1d6", "modifier": "DEX", "damage_type": "piercing", "range": 30},
    "Crossbow, heavy": {"damage_dice": "1d10", "modifier": "STR", "damage_type": "piercing", "range": 100},
    "Longbow": {"damage_dice": "1d8", "modifier": "STR", "damage_type": "piercing", "range": 150},
    "ClawsWyvern": {"damage_dice": "2d6", "modifier": "STR", "damage_type": "slashing", "range": 5},
}

# Party Members
party = [
    PartyMember("Aragorn", "Fighter", "Champion", 5, {"STR": 18, "DEX": 14, "CON": 16, "INT": 10, "WIS": 12, "CHA": 13},
                18, 2, 30, 50, ["STR", "CON"], 3, [], [], "Medium", WEAPONS["Longsword"], "melee"),
    PartyMember("Aarakocra Ranger", "Ranger", "Beastmaster", 5, {"STR": 12, "DEX": 18, "CON": 14, "INT": 10, "WIS": 14, "CHA": 10},
                16, 4, 25, 40, ["DEX", "WIS"], 3, [], [], "Medium", WEAPONS["Longbow"], "ranged", 50)
]

# Enemies
enemies = [
    Enemy("Orc", {"STR": 16, "DEX": 12, "CON": 14, "INT": 8, "WIS": 11, "CHA": 10}, 13, 1, 30, 30, ["STR", "CON"],
          2, [], [], "Medium", WEAPONS["Greataxe"], "melee", True, 2),
    Enemy("Wyvern", {"STR": 19, "DEX": 10, "CON": 17, "INT": 5, "WIS": 12, "CHA": 6}, 15, 1, 20, 70, ["STR", "CON"],
          3, [], [], "Large", WEAPONS["ClawsWyvern"], "melee", False, 1, 60)
]

# Assign actions & resistances
for entity in party + enemies:
    assign_default_actions(entity)

enemies[0].resistances = ["slashing"]  # Orc resists slashing
enemies[1].resistances = ["piercing"]  # Wyvern resists piercing

# Assign positions
initialize_positions(party, enemies)

entities = party + enemies

# Initialize an empty CSV with the correct parameters

csv_file = "combat_stats.csv"

# Define the structure of the CSV
columns = [
    "combat_nbr",
    "winner",
    "damage_dealt",
    "turns_survived",
    "actions_used",
    "reactions_used",
    "initiative_order",
    "rounds"
]

# Create the CSV file if it doesn't exist
if not os.path.exists(csv_file):
    empty_data = pd.DataFrame(columns=columns)
    empty_data.to_csv(csv_file, index=False)

# Load the CSV into a dictionary for later use
stats = pd.read_csv(csv_file).to_dict(orient="list")

# Run Simulation
combat_results = run_bulk_simulations(party + enemies, num_simulations=10)

analysism = MonteCarloSimulation("data.csv")
analysism.run_analysis()

analysis = RegressionAnalysis("combat_stats.csv")
analysis.run_analysis()

# Run statistical analysis
analysis_results = analyze_combat_results(combat_results)

generate_combat_report(analysis_results, "combat_simulation_report.pdf")
