from fpdf import FPDF
import pandas as pd
import os
import numpy as np

def generate_combat_report(results, output_path):
    """Generates a structured PDF report from combat simulation results."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title Page
    pdf.set_font("Arial", "B", 20)
    pdf.cell(200, 10, "D&D Combat Simulation Report", ln=True, align="C")
    pdf.ln(10)
    
    # Function to add sections
    def add_section(title):
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, title, ln=True)
        pdf.ln(5)
    
    def add_text(content):
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, content)
        pdf.ln(5)
    
    def add_image(image_path, width=180):
        if os.path.exists(image_path):
            pdf.image(image_path, x=(210 - width) / 2, w=width)
            pdf.ln(10)
    
    def add_table(data):
        pdf.set_font("Arial", "B", 12)
        col_width = 90  # Adjusted for better readability

        if isinstance(data, pd.Series) or isinstance(data, dict):
            pdf.cell(col_width, 10, "Metric", border=1)
            pdf.cell(col_width, 10, "Value", border=1)
            pdf.ln()
            pdf.set_font("Arial", "", 10)
            for key, value in data.items():
                # Ensure proper number formatting
                if isinstance(value, (pd.Series, pd.DataFrame)):
                    clean_value = str(value.to_dict())  # Ensures all values are converted properly
                elif isinstance(value, (int, float, np.float64)):
                    clean_value = round(float(value), 4)
                else:
                    clean_value = str(value)
                pdf.cell(col_width, 10, str(key), border=1)
                pdf.cell(col_width, 10, str(clean_value), border=1)
                pdf.ln()
        elif isinstance(data, pd.DataFrame):
            # Convert DataFrame into separate dictionaries per entity
            for entity in data.columns:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, entity, ln=True)  # Entity header
                pdf.set_font("Arial", "", 10)
                for index, value in data[entity].items():
                    clean_value = round(float(value), 4) if isinstance(value, (int, float, np.float64)) else str(value)
                    pdf.cell(col_width, 10, str(index), border=1)
                    pdf.cell(col_width, 10, str(clean_value), border=1)
                    pdf.ln()
                pdf.ln(5)  # Space between entities
        pdf.ln(5)
    
    # Win Rate Analysis
    if "Win Rate (%)" in results:
        win_rate, confidence_interval = results["Win Rate (%)"]
        add_section("Win Rate Analysis")
        add_table({
            "Party Win Rate": f"{win_rate:.2f}%",
            "95% Confidence Interval": f"{confidence_interval[0]:.2f}% - {confidence_interval[1]:.2f}%"
        })
    # average rounds if provided
    if "avg_rounds" in results:
        add_section("Average Rounds per Combat")
        add_text(str(round(results["avg_rounds"], 2)))

    # Per-entity Metrics
    if "damage_dealt" in results and results["damage_dealt"]:
        add_section("Damage Statistics (average per simulation)")
        sorted_damage = {name: round(results["damage_dealt"][name], 2)
                         for name in sorted(results["damage_dealt"])}
        add_table(sorted_damage)

    if "avg_damage_per_attack" in results:
        add_section("Average Damage per Attack")
        formatted = {name: round(v, 2) for name, v in results["avg_damage_per_attack"].items()}
        add_table(formatted)

    if "crit_average" in results:
        add_section("Crits per Entity (avg per sim)")
        formatted = {name: round(v, 2) for name, v in results["crit_average"].items()}
        add_table(formatted)
    if "total_crits_mean" in results:
        add_text(f"Average total crits per combat: {results['total_crits_mean']:.2f}")

    if "turns_no_damage" in results:
        add_section("Rounds with No Damage (average)")
        add_text(str(round(results["turns_no_damage"], 2)))

    if "hp_end" in results:
        add_section("Average HP Remaining at End")
        sorted_hp = {name: round(results["hp_end"][name], 2) for name in sorted(results["hp_end"])}
        add_table(sorted_hp)

    if "turns_survived" in results:
        add_section("Survivability (average turns survived)")
        sorted_surv = {name: round(results["turns_survived"][name], 2)
                       for name in sorted(results["turns_survived"])}
        add_table(sorted_surv)

    if "actions_used" in results and results["actions_used"]:
        add_section("Action Usage (average per simulation)")
        for entity in sorted(results["actions_used"]):
            add_section(f"Entity: {entity}")
            formatted_actions = {action: round(count, 2)
                                 for action, count in results["actions_used"][entity].items()}
            add_table(formatted_actions)

    if "Movement Analysis" in results and results["Movement Analysis"]:
        add_section("Movement Analysis")
        add_table(results["Movement Analysis"])

    if "Probability Distributions" in results and results["Probability Distributions"]:
        add_section("Probability Distributions")
        for key, val in results["Probability Distributions"].items():
            add_section(key)
            # survival curve doesn't print raw data long-form
            if key == "Survival Curve":
                add_text("See survival curve plot below for entity life percentages over rounds.")
            elif isinstance(val, dict):
                add_table(val)
        # include histogram images if generated
        for img in ["damage_distribution.png", "turns_survived_distribution.png", "rounds_distribution.png", "survival_curve.png"]:
            add_image(img)

    # Monte Carlo Analysis
    if "Monte Carlo Analysis" in results and results["Monte Carlo Analysis"]:
        add_section("Monte Carlo Simulation Summary")
        monte_carlo_fixed = {}
        for k, v in results["Monte Carlo Analysis"].items():
            # identify metrics that represent percentages so we can append a '%' sign
            is_pct = "%" in str(k) or "Win" in str(k)
            if isinstance(v, tuple):  # Handle tuple confidence intervals
                formatted = f"({round(float(v[0]), 2)}, {round(float(v[1]), 2)})"
                if is_pct:
                    # apply % to both endpoints
                    formatted = f"({round(float(v[0]), 2)}%, {round(float(v[1]), 2)}%)"
                monte_carlo_fixed[str(k)] = formatted
            else:
                val = round(float(v), 2)
                monte_carlo_fixed[str(k)] = f"{val}%" if is_pct else val
        add_table(monte_carlo_fixed)
        add_image("monte_carlo_plot.png")

    # Regression Analysis
    if "Regression Analysis" in results and results["Regression Analysis"]:
        add_section("Regression Analysis Results")
        for entity in sorted(results["Regression Analysis"]):
            coeffs = results["Regression Analysis"][entity]
            if isinstance(coeffs, dict):  # Ensure coefficients are formatted properly
                add_section(f"{entity} Coefficients")
                formatted_coeffs = {str(k): round(float(v), 4) for k, v in coeffs.items()}
                add_table(formatted_coeffs)
            else:
                add_table({entity: round(float(coeffs), 4)})

   # Save PDF
    pdf.output(output_path)
