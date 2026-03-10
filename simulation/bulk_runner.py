from copy import deepcopy
import numpy as np
import pandas as pd
import scipy.stats as stats
from mechanics.combat import simulate_combat
import matplotlib.pyplot as plt
import statsmodels.api as sm


def _initialize_stats(entities):
    """Create a fresh statistics dictionary for a new combat.

    The structure mirrors what simulate_combat expects and what the
    analysis functions later flatten.
    """
    return {
        "damage_dealt": {},
        "attack_count": {},              # number of attack rolls made by each entity
        "crit_count": {},                # number of critical hits per entity
        "total_crits": 0,                # overall crits in this combat
        "turns_survived": {e.name: 0 for e in entities},
        "actions_used": {},
        "reactions_used": {},
        "initiative_order": {},
        "rounds": 0,
        "turns_no_damage": 0,           # rounds where no damage was dealt
        "hp_end": {},                    # hit points remaining after combat ends
        # auxiliary field used during a round
        "damage_this_round": 0,
    }


def run_bulk_simulations(entities, num_simulations):
    """Runs multiple combat simulations and aggregates statistics."""
    simulation_results = []
    
    for _ in range(num_simulations):
        stats = _initialize_stats(entities)
        result = simulate_combat(deepcopy(entities), stats)
        # simulate_combat returns the final stats dictionary
        simulation_results.append(flatten_dict(result))
    
    df = pd.DataFrame(simulation_results)
    
    return df if not df.empty else None

def flatten_dict(d, parent_key='', sep='_'):
    """Flattens a nested dictionary for easier DataFrame conversion."""
    items = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def compute_win_loss_distribution(df):
    """Computes win rate and confidence interval."""
    if "winner" not in df:
        return None
    
    win_rate = df["winner"].value_counts(normalize=True) * 100
    party_win_rate = win_rate.get("party", 0)
    
    n = len(df)
    se = stats.sem(df["winner"] == "party") if n > 0 else 0
    if n > 1 and se > 0:
        confidence_interval = stats.t.interval(0.95, n - 1, loc=party_win_rate, scale=se)
    else:
        # either not enough samples or zero variance
        confidence_interval = (party_win_rate, party_win_rate)
    
    return party_win_rate, confidence_interval

def compute_damage_statistics(df):
    """Aggregates damage statistics per entity based on column prefixes.

    Returns a dict mapping entity name to average damage dealt across simulations.
    """
    damage_cols = [c for c in df.columns if c.startswith("damage_dealt_")]
    stats = {}
    for col in damage_cols:
        name = col.split("damage_dealt_")[-1]
        stats[name] = df[col].mean() if not df[col].isna().all() else 0
    return stats

def compute_survivability_statistics(df):
    """Computes survivability-related statistics."""
    turn_cols = [c for c in df.columns if c.startswith("turns_survived_")]
    if not turn_cols:
        return None
    stats = {}
    for col in turn_cols:
        name = col.split("turns_survived_")[-1]
        stats[name] = df[col].mean()
    return stats

def compute_action_statistics(df):
    """Computes action and reaction usage statistics."""
    action_columns = [col for col in df.columns if "actions_used_" in col]
    reaction_columns = [col for col in df.columns if "reactions_used_" in col]
    stats_dict = {}
    # per-entity actions as averages
    actions = {}
    for col in action_columns:
        parts = col.split("_")
        # actions_used_<Entity>_<Action>
        if len(parts) >= 4:
            _, _, entity, action = parts[:4]
            actions.setdefault(entity, {})[action] = df[col].mean()
    if actions:
        stats_dict["Action Usage Frequency"] = actions

    # crit statistics
    crit_cols = [c for c in df.columns if c.startswith("crit_count_")]
    attack_cols = [c for c in df.columns if c.startswith("attack_count_")]
    if crit_cols and attack_cols:
        crit_stats = {}
        for col in crit_cols:
            name = col.split("crit_count_")[-1]
            total_crits = df[col].sum()
            attempts_col = f"attack_count_{name}"
            attempts = df[attempts_col].sum() if attempts_col in df else np.nan
            crit_stats[name] = {
                "Average Crits": df[col].mean(),
                "Total Crits": total_crits,
                "Crit Rate": total_crits / attempts if attempts and attempts>0 else np.nan,
            }
        stats_dict["Crit Statistics"] = crit_stats
    
    if reaction_columns:
        stats_dict["Reaction Usage Rate"] = df[reaction_columns].mean()
    
    return stats_dict

def compute_movement_statistics(df):
    """Computes movement-related statistics."""
    movement_data = {
        "Average Distance Moved Per Turn": df.get("distance_moved_per_turn", pd.Series(dtype=float)).apply(np.mean).mean(),
        "Percentage of Turns with Movement": df.get("percentage_turns_moved", pd.Series(dtype=float)).mean(),
        "Average Distance Between Entities": df.get("average_distance_between_entities", pd.Series(dtype=float)).apply(np.mean).mean(),
    }
    return {k: v for k, v in movement_data.items() if pd.notna(v)}

def analyze_combat_results_per_entity(df):
    """Produce per-entity metrics from combat simulation results.

    The returned dictionary is structured to match the visualization module's
    expectations (keys like "damage_dealt", "actions_used", etc.).
    """
    if df is None or df.empty:
        print("DEBUG: No valid data available.")
        return "No valid data available."

    results = {}
    # damage dealt averages
    results["damage_dealt"] = compute_damage_statistics(df)

    # average damage per attack, if attack_count present
    attack_cols = [c for c in df.columns if c.startswith("attack_count_")]
    if attack_cols:
        avg_per_attack = {}
        for col in attack_cols:
            name = col.split("attack_count_")[-1]
            dmg_col = f"damage_dealt_{name}"
            if dmg_col in df.columns:
                total_dmg = df[dmg_col].sum()
                total_atk = df[col].sum()
                avg_per_attack[name] = total_dmg / total_atk if total_atk>0 else 0
        results["avg_damage_per_attack"] = avg_per_attack

    # crit statistics
    crit_cols = [c for c in df.columns if c.startswith("crit_count_")]
    if crit_cols:
        crits = {col.split("crit_count_")[-1]: df[col].mean() for col in crit_cols}
        results["crit_average"] = crits
    if "total_crits" in df:
        results["total_crits_mean"] = df["total_crits"].mean()

    # turns no damage
    if "turns_no_damage" in df:
        results["turns_no_damage"] = df["turns_no_damage"].mean()

    # hp end statistics
    hp_cols = [c for c in df.columns if c.startswith("hp_end_")]
    if hp_cols:
        stats = {}
        for col in hp_cols:
            name = col.split("hp_end_")[-1]
            stats[name] = df[col].mean()
        results["hp_end"] = stats

    # survivability (average turns)
    surv = {}
    turns_cols = [c for c in df.columns if c.startswith("turns_survived_")]
    for col in turns_cols:
        name = col.split("turns_survived_")[-1]
        surv[name] = df[col].mean()
    if surv:
        results["turns_survived"] = surv

    # rounds distribution and other global metrics
    results["rounds"] = df["rounds"].mean() if "rounds" in df else None

    results["Movement Analysis"] = compute_movement_statistics(df)
    results["Probability Distributions"] = compute_probability_distributions(df)

    return results

def analyze_combat_results_global(df):
    """Runs all statistical analysis on combat simulation results."""
    if df is None or df.empty:
        print("DEBUG: No valid data available.")
        return "No valid data available."
    results = {}
    results["Win Rate (%)"] = compute_win_loss_distribution(df)
    if "rounds" in df:
        # global average rounds and distribution saved via histogram
        results["avg_rounds"] = df["rounds"].mean()
    return results

def plot_and_save_histogram(data, title, xlabel, output_path):
    """Generates a histogram and saves it as an image file."""
    if data is None or len(data) == 0:
        return
    plt.figure(figsize=(6,4))
    plt.hist(data, bins=20, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()


def compute_survival_curve(df):
    """Calculates survival probabilities over rounds and plots a curve.

    Returns a dictionary {entity: [percent_alive_by_round]} or None if no data.
    """
    seq_cols = [c for c in df.columns if c.startswith("survival_sequence_")]
    if not seq_cols:
        return None
    curves = {}
    for col in seq_cols:
        name = col.split("survival_sequence_")[-1]
        sequences = df[col].dropna().tolist()
        if not sequences:
            continue
        max_len = max(len(seq) for seq in sequences)
        counts = [0] * max_len
        total = len(sequences)
        for seq in sequences:
            for i in range(max_len):
                if i < len(seq) and seq[i]:
                    counts[i] += 1
        curves[name] = [(counts[i] / total) * 100 for i in range(max_len)]
    # plot if we have at least one curve
    if curves:
        plt.figure(figsize=(8, 6))
        for name, probs in curves.items():
            plt.plot(range(1, len(probs) + 1), probs, label=name)
        plt.xlabel("Round")
        plt.ylabel("Percent Alive")
        plt.title("Survivability Curve")
        plt.legend()
        plt.grid(True)
        plt.savefig("survival_curve.png", bbox_inches="tight")
        plt.close()
    return curves


def compute_probability_distributions(df):
    """Computes probability distributions and generates histograms."""
    stats_dict = {}

    if "damage_dealt_Aaragocra Ranger" in df.columns or any(c.startswith("damage_dealt_") for c in df.columns):
        # combine all damage values into one series for overall distribution
        dmg_cols = [c for c in df.columns if c.startswith("damage_dealt_")]
        damage_values = df[dmg_cols].sum(axis=1).dropna()
        mean_damage = damage_values.mean()
        std_damage = damage_values.std()
        stats_dict["Damage Distribution"] = {
            "Mean": mean_damage,
            "Standard Deviation": std_damage,
        }
        plot_and_save_histogram(damage_values, "Total Damage Distribution", "Damage", "damage_distribution.png")

    if "rounds" in df.columns:
        rounds = df["rounds"].dropna()
        plot_and_save_histogram(rounds, "Rounds Per Combat", "Rounds", "rounds_distribution.png")

    # create survival curve based on recorded sequences
    curves = compute_survival_curve(df)
    if curves is not None:
        stats_dict["Survival Curve"] = curves

    return stats_dict