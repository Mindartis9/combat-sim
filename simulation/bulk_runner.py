from copy import deepcopy
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.linear_model import LinearRegression, LogisticRegression
from mechanics.combat import simulate_combat
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

def run_bulk_simulations(entities, num_simulations, debug=False):
    """Runs multiple combat simulations and aggregates statistics."""
    simulation_results = []
    
    for _ in range(num_simulations):
        stats = simulate_combat(deepcopy(entities))
        simulation_results.append(flatten_dict(stats))
    
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
    
    if len(df) > 1:
        confidence_interval = stats.t.interval(0.95, len(df) - 1, loc=party_win_rate, scale=stats.sem(df["winner"] == "party"))
    else:
        confidence_interval = (party_win_rate, party_win_rate)
    
    return party_win_rate, confidence_interval

def compute_damage_statistics(df):
    """Computes damage-related statistics."""
    damage_columns = [col for col in df.columns if "damage_dealt" in col]
    if not damage_columns:
        return None
    
    damage_data = df[damage_columns]
    return {
        "Average Damage Per Round": damage_data.mean(),
        "Total Damage Dealt": damage_data.sum(),
        "Damage Variance": damage_data.var(),
        "Damage Standard Deviation": damage_data.std(),
        "Expected Value of Damage": damage_data.mean(),
    }

def compute_survivability_statistics(df):
    """Computes survivability-related statistics."""
    if "turns_survived" not in df:
        return None
    
    return {
        "Average Turns Before Death": df["turns_survived"].mean(),
        "Survival Rate Per Round": df.get("survival_per_round", pd.Series(dtype=float)).apply(np.mean).mean(),
        "Death Turn Variance": df["turns_survived"].var(),
    }

def compute_action_statistics(df):
    """Computes action and reaction usage statistics."""
    action_columns = [col for col in df.columns if "actions_used" in col]
    reaction_columns = [col for col in df.columns if "reactions_used" in col]
    
    stats_dict = {
        "Action Usage Frequency": df[action_columns].mean() if action_columns else None,
        "Reaction Usage Rate": df[reaction_columns].mean() if reaction_columns else None,
    }
    
    if "hit_miss_counts" in df:
        hit_totals = df.filter(like="_hits").sum(axis=1)
        miss_totals = df.filter(like="_misses").sum(axis=1)
        total_attempts = hit_totals + miss_totals.replace(0, np.nan)
        df["Hit Rate"] = hit_totals / total_attempts
        df["Miss Rate"] = 1 - df["Hit Rate"]
        stats_dict.update({
            "Average Hit Rate": df["Hit Rate"].mean(),
            "Average Miss Rate": df["Miss Rate"].mean(),
        })
    
    return stats_dict

def compute_movement_statistics(df):
    """Computes movement-related statistics."""
    movement_data = {
        "Average Distance Moved Per Turn": df.get("distance_moved_per_turn", pd.Series(dtype=float)).apply(np.mean).mean(),
        "Percentage of Turns with Movement": df.get("percentage_turns_moved", pd.Series(dtype=float)).mean(),
        "Average Distance Between Entities": df.get("average_distance_between_entities", pd.Series(dtype=float)).apply(np.mean).mean(),
    }
    return {k: v for k, v in movement_data.items() if pd.notna(v)}

def analyze_combat_results(df):
    """Runs all statistical analysis on combat simulation results."""
    if df is None or df.empty:
        print("DEBUG: No valid data available.")
        return "No valid data available."
    
    return {
        "Win Rate (%)": compute_win_loss_distribution(df),
        "Damage Statistics": compute_damage_statistics(df),
        "Survivability Statistics": compute_survivability_statistics(df),
        "Action Analysis": compute_action_statistics(df),
        "Movement Analysis": compute_movement_statistics(df),
        "Probability Distributions": compute_probability_distributions(df),
        "Monte Carlo Analysis": monte_carlo_analysis(df),
        "Regression Analysis": regression_analysis(df),
    }

def plot_and_save_histogram(data, title, xlabel, output_path):
    """Generates a histogram and saves it as an image file."""
    plt.figure(figsize=(6,4))
    plt.hist(data, bins=20, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Frequency")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()


def compute_probability_distributions(df):
    """Computes probability distributions and generates histograms."""
    stats_dict = {}

    if "damage_dealt" in df.columns:
        damage_values = df["damage_dealt"].dropna()
        mean_damage = damage_values.mean()
        std_damage = damage_values.std()
        
        stats_dict["Damage Distribution"] = {
            "Mean": mean_damage,
            "Standard Deviation": std_damage,
        }
        
        # Save histogram for damage dealt
        plot_and_save_histogram(damage_values, "Damage Dealt Distribution", "Damage", "damage_distribution.png")

    if "turns_survived" in df.columns:
        survival_values = df["turns_survived"].dropna()
        
        # Save histogram for turns survived
        plot_and_save_histogram(survival_values, "Turns Survived Distribution", "Turns Survived", "turns_survived_distribution.png")

    return stats_dict

def monte_carlo_analysis(df, num_simulations=10):
    """Performs Monte Carlo analysis on win rates."""
    if "winner" not in df.columns:
        return None

    win_rate = (df["winner"] == "party").mean()
    
    simulated_win_rates = np.random.binomial(n=num_simulations, p=win_rate, size=num_simulations) / num_simulations
    ci_lower, ci_upper = np.percentile(simulated_win_rates, [2.5, 97.5])

    # Save histogram for Monte Carlo simulation
    plot_and_save_histogram(simulated_win_rates * 100, "Monte Carlo Simulated Win Rates", "Win Rate (%)", "monte_carlo_simulation.png")


    return {
        "Estimated Win Rate": round(win_rate * 100, 2),
        "95% Confidence Interval": (round(ci_lower * 100, 2), round(ci_upper * 100, 2)),
    }

def regression_analysis(df):
    """Performs logistic regression analysis to predict combat success."""
    
    if "winner" not in df.columns:
        return {"Error": "Missing required column: 'winner'."}

    df = df.copy()
    df["win_binary"] = (df["winner"] == "party").astype(int)

    # Define predictors explicitly
    predictors = ["turns_survived", "damage_dealt", "initiative"]
    predictors = [p for p in predictors if p in df.columns]  # Only keep existing columns

    if not predictors:
        return {"Error": f"No valid predictors found. Available columns: {df.columns.tolist()}"}

    # Prepare data
    X = df[predictors].dropna()
    y = df.loc[X.index, "win_binary"]

    # Check for multicollinearity
    X_with_const = sm.add_constant(X)
    vif_data = pd.DataFrame({
        "Variable": X_with_const.columns,
        "VIF": [variance_inflation_factor(X_with_const.values, i) for i in range(X_with_const.shape[1])]
    })
    
    # Fit logistic regression
    logit_model = sm.Logit(y, X_with_const).fit(disp=0)  # Suppress output
    results_summary = logit_model.summary2().tables[1]  # Extract coefficients and p-values
    
    # Extract key results
    coefficients = results_summary["Coef."]
    p_values = results_summary["P>|z|"]
    
    # Compute McFadden's Pseudo R²
    null_model = sm.Logit(y, np.ones_like(y)).fit(disp=0)  # Null model with only intercept
    pseudo_r2 = 1 - (logit_model.llf / null_model.llf)
    
    return {
        "Regression Coefficients": coefficients.to_dict(),
        "P-values": p_values.to_dict(),
        "Intercept": logit_model.params["const"],
        "Pseudo R²": pseudo_r2,
        "VIF Scores": vif_data.set_index("Variable")["VIF"].to_dict(),
        "Model Summary": str(logit_model.summary())  # Optional: Full summary
    }
