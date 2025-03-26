import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

class MonteCarloSimulation:
    def __init__(self, data_path, num_simulations=10000):
        """Initialize the Monte Carlo Simulation class."""
        self.data_path = data_path
        self.num_simulations = num_simulations
        self.df = None
        self.results = []
    
    def load_data(self):
        """Loads data from CSV."""
        self.df = pd.read_csv(self.data_path)
        self.df.dropna(inplace=True)
    
    def run_simulation(self):
        """Runs the Monte Carlo simulation."""
        win_percentage_mean = self.df['Win Percentage'].mean()
        win_percentage_std = self.df['Win Percentage'].std()
        
        simulated_results = np.random.normal(win_percentage_mean, win_percentage_std, self.num_simulations)
        self.results = simulated_results
    
    def plot_simulation_results(self):
        """Plots the Monte Carlo simulation results."""
        plt.figure(figsize=(8, 6))
        plt.hist(self.results, bins=50, alpha=0.75, density=True)
        plt.title("Monte Carlo Simulation Results")
        plt.xlabel("Simulated Win Percentage")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.savefig("monte_carlo_plot.png")
    
    def generate_pdf_report(self, output_path="MonteCarlo_Report.pdf"):
        """Generates a PDF report with the simulation results."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.set_font("Arial", style='', size=12)
        pdf.cell(200, 10, "Monte Carlo Simulation Report", ln=True, align='C')
        pdf.ln(10)
        
        pdf.cell(200, 10, "Simulation Statistics", ln=True, align='C')
        pdf.ln(5)
        pdf.cell(0, 10, f"Mean Simulated Win Percentage: {np.mean(self.results):.2f}%", ln=True)
        pdf.cell(0, 10, f"Standard Deviation: {np.std(self.results):.2f}%", ln=True)
        pdf.cell(0, 10, f"Minimum Simulated Win Percentage: {np.min(self.results):.2f}%", ln=True)
        pdf.cell(0, 10, f"Maximum Simulated Win Percentage: {np.max(self.results):.2f}%", ln=True)
        
        pdf.ln(10)
        pdf.image("monte_carlo_plot.png", x=10, w=180)
        pdf.output(output_path)
    
    def run_analysis(self):
        """Executes the full Monte Carlo simulation pipeline."""
        self.load_data()
        self.run_simulation()
        self.plot_simulation_results()
        self.generate_pdf_report()

