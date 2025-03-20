import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.outliers_influence import variance_inflation_factor
from fpdf import FPDF

class RegressionAnalysis:
    def __init__(self, data_path):
        """Initialize with dataset path."""
        self.data_path = data_path
        self.df = None
        self.results = None
    
    def load_data(self):
        """Loads data from CSV."""
        self.df = pd.read_csv(self.data_path)
        self.df.dropna(inplace=True)
    
    def fit_regression(self):
        """Fits multiple linear regression."""
        X = self.df[['Turns Survived', 'Initiative', 'Damage Dealt']]
        y = self.df['Win Percentage']
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
        sns.histplot(residuals, kde=True, bins=30)
        plt.title("Residuals Distribution")
        plt.xlabel("Residuals")
        plt.ylabel("Frequency")
        plt.savefig("residuals_plot.png")
    
    def generate_pdf_report(self, output_path="Regression_Report.pdf"):
        """Generates a PDF report with results."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_font("Arial", style='', size=12)
        pdf.cell(200, 10, "Regression Analysis Report", ln=True, align='C')
        pdf.ln(10)
        
        pdf.multi_cell(0, 10, str(self.results.summary()))
        pdf.ln(10)
        
        pdf.cell(200, 10, "VIF Scores", ln=True, align='C')
        pdf.ln(5)
        vif_data = self.calculate_vif()
        for _, row in vif_data.iterrows():
            pdf.cell(0, 10, f"{row['Feature']}: {row['VIF']:.2f}", ln=True)
        
        pdf.ln(10)
        pdf.image("residuals_plot.png", x=10, w=180)
        pdf.output(output_path)
    
    def run_analysis(self):
        """Executes full regression analysis pipeline."""
        self.load_data()
        self.fit_regression()
        self.plot_residuals()
        self.generate_pdf_report()

# Example Usage
# analysis = RegressionAnalysis("data.csv")
# analysis.run_analysis()
