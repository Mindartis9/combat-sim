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
        """Loads data from CSV and removes rows missing win information."""
        self.df = pd.read_csv(self.data_path)
        # only drop rows where winner or win percentage is missing
        if 'Win Percentage' in self.df.columns:
            self.df.dropna(subset=['Win Percentage'], inplace=True)
        elif 'winner' in self.df.columns:
            self.df.dropna(subset=['winner'], inplace=True)
        # otherwise keep all rows (other NaNs are allowed)
    
    def run_simulation(self):
        """Runs the Monte Carlo simulation.

        The simulation models the **party win percentage**; results are clipped to
        [0,100] and the complementary enemy win percentage is implicit.
        """
        if 'Win Percentage' not in self.df.columns:
            # derive win percentage from winner field if available
            if 'winner' in self.df.columns:
                win_pct = (self.df['winner'] == 'party').astype(int) * 100
                win_percentage_mean = win_pct.mean()
                win_percentage_std = win_pct.std()
            else:
                raise ValueError("Data does not contain 'Win Percentage' or 'winner' columns")
        else:
            win_percentage_mean = self.df['Win Percentage'].mean()
            win_percentage_std = self.df['Win Percentage'].std()

        simulated_results = np.random.normal(win_percentage_mean, win_percentage_std, self.num_simulations)
        # clip to valid percentage range
        simulated_results = np.clip(simulated_results, 0, 100)
        self.results = simulated_results
    
    def plot_simulation_results(self):
        """Plots the Monte Carlo simulation results."""
        plt.figure(figsize=(8, 6))
        plt.hist(self.results, bins=50, alpha=0.75, density=True)
        plt.title("Monte Carlo Simulation Results")
        plt.xlabel("Simulated Win Percentage")
        plt.ylabel("Frequency")
        plt.grid(True)
        # use a file name that matches what the visualization module expects
        plt.savefig("monte_carlo_plot.png")
    
    def generate_pdf_report(self, output_path="MonteCarlo_Report.pdf"):
        """Generates a PDF report with the simulation results."""
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Monte Carlo Simulation Report", ln=True, align='C')
        pdf.ln(10)

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

        add_section("Simulation Statistics")
        # compute confidence interval using percentiles in case of extreme values
        ci_lower = np.percentile(self.results, 2.5)
        ci_upper = np.percentile(self.results, 97.5)
        add_table({
            "Party Win % Mean": f"{np.mean(self.results):.2f}%",
            "Std Dev": f"{np.std(self.results):.2f}%",
            "Min Party Win %": f"{np.min(self.results):.2f}%",
            "Max Party Win %": f"{np.max(self.results):.2f}%",
            "Average Enemy Win %": f"{100 - np.mean(self.results):.2f}%",
            "95% Confidence Interval": f"{ci_lower:.2f}% - {ci_upper:.2f}%"
        })
        pdf.image("monte_carlo_plot.png", x=10, w=180)
        pdf.output(output_path)
    
    def run_analysis(self, df=None):
        """Executes the full Monte Carlo simulation pipeline.

        If a DataFrame is passed directly, use it instead of reading the CSV file.
        """
        if df is not None:
            self.df = df
        else:
            self.load_data()

        if self.df is None or self.df.empty:
            print("Monte Carlo Analysis: data file is empty, skipping simulation.")
            return
        self.run_simulation()
        # results may be nan if std or mean could not be calculated
        if self.results is None or len(self.results) == 0 or np.all(np.isnan(self.results)):
            print("Monte Carlo Analysis: insufficient data for simulation results, skipping plots/reports.")
            return None
        self.plot_simulation_results()
        self.generate_pdf_report()
        # return a summary dict suitable for inclusion in the master report
        ci_lower = np.percentile(self.results, 2.5)
        ci_upper = np.percentile(self.results, 97.5)
        return {
            "Party Win % Mean": np.mean(self.results),
            "Std Dev": np.std(self.results),
            "Min Party Win %": np.min(self.results),
            "Max Party Win %": np.max(self.results),
            "Average Enemy Win %": 100 - np.mean(self.results),
            "95% Confidence Interval": (ci_lower, ci_upper)
        }

