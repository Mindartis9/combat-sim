from characters.party_member import PartyMember
from characters.enemy import Enemy
from mechanics.combat import assign_default_actions
from simulation.bulk_runner import analyze_combat_results_global, run_bulk_simulations, analyze_combat_results_per_entity
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

enemies[0].resistances = {"slashing"}  # Orc resists slashing
enemies[1].resistances = {"piercing"}  # Wyvern resists piercing

# Assign positions
initialize_positions(party, enemies)

entities = party + enemies

# CSV file used for persistent tracking and later statistical modules
csv_file = "combat_stats.csv"

# Run Simulation
combat_results = run_bulk_simulations(party + enemies, num_simulations=100)

# Persist the results so Monte Carlo / regression can operate on them
if combat_results is not None and not combat_results.empty:
    # drop columns that are entirely NaN before saving
    combat_results = combat_results.dropna(axis=1, how='all')

    # add combat number column if absent
    if "combat_nbr" not in combat_results.columns:
        combat_results.insert(0, "combat_nbr", range(1, len(combat_results) + 1))

    # helper to load and clean previous file
    def _load_clean(path):
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return pd.DataFrame()
        df = pd.read_csv(path)
        if 'winner' in df.columns:
            # keep only valid string winners
            df = df[df['winner'].isin(['party', 'enemies'])]
        return df

    existing = _load_clean(csv_file)
    if existing.empty:
        combat_results.to_csv(csv_file, index=False)
    else:
        combined = pd.concat([existing, combat_results], ignore_index=True)
        # again drop any empty columns after combining
        combined = combined.dropna(axis=1, how='all')
        combined.to_csv(csv_file, index=False)

# run statistical analyses using the updated CSV
analysism = MonteCarloSimulation(csv_file)
mc_summary = analysism.run_analysis()

analysis = RegressionAnalysis(csv_file)
reg_summary = analysis.run_analysis()

# Run statistical analysis for this batch of simulations
analysis_results1 = analyze_combat_results_per_entity(combat_results)
analysis_results = analyze_combat_results_global(combat_results)

# combine everything for the master PDF
combined_results = {}
if isinstance(analysis_results1, dict):
    combined_results.update(analysis_results1)
if isinstance(analysis_results, dict):
    combined_results.update(analysis_results)
if mc_summary:
    combined_results["Monte Carlo Analysis"] = mc_summary
if reg_summary:
    combined_results["Regression Analysis"] = reg_summary

generate_combat_report(combined_results, "combat_simulation_report.pdf")
