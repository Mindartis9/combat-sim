import pandas as pd
import numpy as np
import statsmodels.api as sm

import matplotlib.pyplot as plt

from statsmodels.stats.outliers_influence import variance_inflation_factor
from fpdf import FPDF

class RegressionAnalysis:
    def __init__(self, data_path):
        """Initialize with dataset path."""
        self.data_path = data_path
        self.df = None
        self.results = None
    
    def load_data(self):
        """Loads data from CSV and prepares derived fields for regression."""
        self.df = pd.read_csv(self.data_path)
        # compute a numeric win percentage column if missing
        if 'Win Percentage' not in self.df.columns and 'winner' in self.df.columns:
            self.df['Win Percentage'] = (self.df['winner'] == 'party').astype(int) * 100

        # derive aggregate features needed for regression
        # total damage across all entities
        damage_cols = [c for c in self.df.columns if c.startswith('damage_dealt_')]
        if damage_cols:
            self.df['Damage Dealt'] = self.df[damage_cols].sum(axis=1)

        # initiative: minimum initiative order (earliest actor)
        init_cols = [c for c in self.df.columns if c.startswith('initiative_order_')]
        if init_cols:
            self.df['Initiative'] = self.df[init_cols].min(axis=1)

        # turns survived: average of all characters
        turn_cols = [c for c in self.df.columns if c.startswith('turns_survived_')]
        if turn_cols:
            self.df['Turns Survived'] = self.df[turn_cols].mean(axis=1)

        # drop any rows missing the core features or target
        required = ['Turns Survived', 'Initiative', 'Damage Dealt', 'Win Percentage']
        existing = [c for c in required if c in self.df.columns]
        if existing:
            self.df.dropna(subset=existing, inplace=True)
    
    def fit_regression(self):
        """Fits multiple linear regression."""
        X = self.df[['Turns Survived', 'Initiative', 'Damage Dealt']]
        if 'Win Percentage' in self.df.columns:
            y = self.df['Win Percentage']
        elif 'winner' in self.df.columns:
            # encode party win as 1, losses as 0 and convert to percentage
            y = (self.df['winner'] == 'party').astype(int) * 100
        else:
            raise ValueError("Regression requires a 'Win Percentage' or 'winner' column")
        X = sm.add_constant(X)
        
        model = sm.OLS(y, X).fit()
        self.results = model
    
    def calculate_vif(self):
        """Calculates Variance Inflation Factor (VIF)."""
        X = self.df[['Turns Survived', 'Initiative', 'Damage Dealt']]
        X = sm.add_constant(X)
        vif_data = pd.DataFrame()
        vif_data['Feature'] = X.columns
        vif_data['VIF'] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
        return vif_data
    
    def plot_residuals(self):
        """Generates residuals plot."""
        residuals = self.results.resid
        plt.figure(figsize=(8, 6))
        plt.hist(residuals, bins=30, edgecolor='black', alpha=0.7)
        plt.axvline(x=0, color='red', linestyle='--', linewidth=1)
        plt.title("Residuals Distribution")
        plt.xlabel("Residuals")
        plt.ylabel("Frequency")
        plt.savefig("residuals_plot.png")
    
    def generate_pdf_report(self, output_path="Regression_Report.pdf"):
        """Generates a PDF report with results using formatted sections and tables."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        def add_section(title):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, title, ln=True)
            pdf.ln(5)
        def add_text(txt):
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, txt)
            pdf.ln(5)
        def add_table(data):
            pdf.set_font("Arial", "B", 12)
            colw = 90
            pdf.cell(colw, 10, "Metric", border=1)
            pdf.cell(colw, 10, "Value", border=1)
            pdf.ln()
            pdf.set_font("Arial", "", 10)
            for k, v in data.items():
                pdf.cell(colw, 10, str(k), border=1)
                pdf.cell(colw, 10, str(v), border=1)
                pdf.ln()
            pdf.ln(5)

        add_section("Regression Analysis Report")

        # model summary coefficients
        coeffs = self.results.params if self.results is not None else {}
        add_section("Coefficients")
        coeff_dict = {str(k): round(float(v), 4) for k, v in coeffs.items()}
        add_table(coeff_dict)

        # r-squared and other stats
        if self.results is not None:
            stats_data = {
                "R-squared": round(self.results.rsquared, 4),
                "Adj. R-squared": round(self.results.rsquared_adj, 4),
                "F-statistic": round(self.results.fvalue, 4) if hasattr(self.results, 'fvalue') else '',
                "Prob (F-statistic)": round(self.results.f_pvalue, 4) if hasattr(self.results, 'f_pvalue') else ''
            }
            add_section("Model Summary")
            add_table(stats_data)

        # VIF
        add_section("Variance Inflation Factor (VIF)")
        vif_data = self.calculate_vif()
        vif_dict = {row['Feature']: round(row['VIF'], 4) for _, row in vif_data.iterrows()}
        add_table(vif_dict)

        # residuals plot
        add_section("Residuals Distribution")
        pdf.image("residuals_plot.png", x=10, w=180)

        pdf.output(output_path)
    
    def run_analysis(self, df=None):
        """Executes full regression analysis pipeline.

        Can optionally accept a DataFrame directly, bypassing CSV loading.
        """
        if df is not None:
            self.df = df
        else:
            self.load_data()
        if self.df is None or self.df.empty:
            print("Regression Analysis: data file is empty, skipping regression.")
            return
        required = {'Turns Survived', 'Initiative', 'Damage Dealt'}
        if not required.issubset(self.df.columns):
            print(f"Regression Analysis: missing required columns {required - set(self.df.columns)}, skipping.")
            return
        self.fit_regression()
        self.plot_residuals()
        self.generate_pdf_report()
        # prepare a summary that can be merged into other reports
        summary = {}
        if self.results is not None:
            # coefficients
            coeffs = self.results.params.to_dict()
            summary["Coefficients"] = coeffs
            # key statistics
            stats_data = {
                "R-squared": round(self.results.rsquared, 4),
                "Adj. R-squared": round(self.results.rsquared_adj, 4),
                "F-statistic": round(self.results.fvalue, 4) if hasattr(self.results, 'fvalue') else '',
                "Prob (F-statistic)": round(self.results.f_pvalue, 4) if hasattr(self.results, 'f_pvalue') else ''
            }
            summary["Model Summary"] = stats_data
            # VIF
            vif = self.calculate_vif()
            vif_dict = {row['Feature']: round(row['VIF'], 4) for _, row in vif.iterrows()}
            summary["VIF"] = vif_dict
        return summary


