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
            "Win Rate": f"{win_rate:.2f}%",
            "Confidence Interval": f"{confidence_interval[0]:.2f}% - {confidence_interval[1]:.2f}%"
        })
        
    # Damage Statistics
    # Damage Statistics
    if "damage_dealt" in results and results["damage_dealt"]:
        add_section("Damage Statistics")

        formatted_damage = {name: round(value, 2) for name, value in results["damage_dealt"].items()}
        add_table(formatted_damage)
    else:
        add_text("No damage recorded.")

    # Action & Reaction Analysis
    if "actions_used" in results and results["actions_used"]:
        add_section("Action & Reaction Analysis")

        for entity, actions in results["actions_used"].items():
            add_section(f"Entity: {entity}")
            formatted_actions = {action: count for action, count in actions.items()}
            add_table(formatted_actions)
    else:
        add_text("No action data recorded.")

        # Monte Carlo Analysis
        if "Monte Carlo Analysis" in results and results["Monte Carlo Analysis"]:
            add_section("Monte Carlo Analysis")
            
            monte_carlo_fixed = {}
            for k, v in results["Monte Carlo Analysis"].items():
                if isinstance(v, tuple):  # Handle tuple confidence intervals
                    monte_carlo_fixed[str(k)] = f"({round(float(v[0]), 2)}, {round(float(v[1]), 2)})"
                else:
                    monte_carlo_fixed[str(k)] = round(float(v), 2)

            add_table(monte_carlo_fixed)
            add_image("monte_carlo_simulation.png")

    
    # Regression Analysis
    if "Regression Analysis" in results and results["Regression Analysis"]:
        add_section("Regression Analysis")
    
        for entity, coeffs in results["Regression Analysis"].items():
            if isinstance(coeffs, dict):  # Ensure coefficients are formatted properly
                add_section(f"{entity} Coefficients")
                formatted_coeffs = {str(k): round(float(v), 4) for k, v in coeffs.items()}
                add_table(formatted_coeffs)
            else:
                add_table({entity: round(float(coeffs), 4)})
                
   # Save PDF
    pdf.output(output_path)
