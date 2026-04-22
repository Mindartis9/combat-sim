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
import tkinter as tk
from tkinter import ttk, messagebox

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

# ---------- UI + entity creation ----------

ABILITY_KEYS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
SIZE_OPTIONS = ["Tiny", "Small", "Medium", "Large", "Huge", "Gargantuan"]
STYLE_OPTIONS = ["melee", "ranged"]


def parse_csv_list(text):
    if not text.strip():
        return []
    return [item.strip().upper() for item in text.split(",") if item.strip()]


def build_party_member(data):
    ability_scores = {key: int(data[f"ability_{key}"].get()) for key in ABILITY_KEYS}

    member = PartyMember(
        data["name"].get().strip(),
        data["char_class"].get().strip(),
        data["subclass"].get().strip(),
        int(data["level"].get()),
        ability_scores,
        int(data["ac"].get()),
        int(data["initiative"].get()),
        int(data["speed"].get()),
        int(data["hp"].get()),
        parse_csv_list(data["saving_throws"].get()),
        int(data["proficiency_bonus"].get()),
        [],
        [],
        data["size"].get(),
        WEAPONS[data["weapon"].get()],
        data["combat_style"].get(),
        int(data["flying_speed"].get()),
    )

    member.resistances = set(parse_csv_list(data["resistances"].get()))
    member.immunities = set(parse_csv_list(data["immunities"].get()))
    return member


def build_enemy(data):
    ability_scores = {key: int(data[f"ability_{key}"].get()) for key in ABILITY_KEYS}

    enemy = Enemy(
        data["name"].get().strip(),
        ability_scores,
        int(data["ac"].get()),
        int(data["initiative"].get()),
        int(data["speed"].get()),
        int(data["hp"].get()),
        parse_csv_list(data["saving_throws"].get()),
        int(data["proficiency_bonus"].get()),
        [],
        [],
        data["size"].get(),
        WEAPONS[data["weapon"].get()],
        data["combat_style"].get(),
        bool(data["multiattack"].get()),
        int(data["attack_count"].get()),
        int(data["flying_speed"].get()),
    )

    enemy.resistances = set(parse_csv_list(data["resistances"].get()))
    enemy.immunities = set(parse_csv_list(data["immunities"].get()))
    return enemy


def run_pipeline(party, enemies, num_simulations):
    for entity in party + enemies:
        assign_default_actions(entity)

    initialize_positions(party, enemies)

    csv_file = "combat_stats.csv"
    combat_results = run_bulk_simulations(party + enemies, num_simulations=num_simulations)

    if combat_results is not None and not combat_results.empty:
        combat_results = combat_results.dropna(axis=1, how='all')

        if "combat_nbr" not in combat_results.columns:
            combat_results.insert(0, "combat_nbr", range(1, len(combat_results) + 1))

        def _load_clean(path):
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                return pd.DataFrame()
            df = pd.read_csv(path)
            if 'winner' in df.columns:
                df = df[df['winner'].isin(['party', 'enemies'])]
            return df

        existing = _load_clean(csv_file)
        if existing.empty:
            combat_results.to_csv(csv_file, index=False)
        else:
            combined = pd.concat([existing, combat_results], ignore_index=True)
            combined = combined.dropna(axis=1, how='all')
            combined.to_csv(csv_file, index=False)

    analysism = MonteCarloSimulation(csv_file)
    mc_summary = analysism.run_analysis()

    analysis = RegressionAnalysis(csv_file)
    reg_summary = analysis.run_analysis()

    analysis_results1 = analyze_combat_results_per_entity(combat_results)
    analysis_results = analyze_combat_results_global(combat_results)

    spell_effectiveness_report = {}
    from simulation.bulk_runner import get_spell_effectiveness_data, compute_spell_effectiveness
    spell_effectiveness_data = get_spell_effectiveness_data()
    if spell_effectiveness_data:
        spell_effectiveness_report = compute_spell_effectiveness(spell_effectiveness_data)

    combined_results = {}
    if isinstance(analysis_results1, dict):
        combined_results.update(analysis_results1)
    if isinstance(analysis_results, dict):
        combined_results.update(analysis_results)
    if mc_summary:
        combined_results["Monte Carlo Analysis"] = mc_summary
    if reg_summary:
        combined_results["Regression Analysis"] = reg_summary
    if spell_effectiveness_report:
        combined_results["Spell Effectiveness Analysis"] = spell_effectiveness_report

    generate_combat_report(combined_results, "combat_simulation_report.pdf")


def make_labeled_entry(parent, row, label, default=""):
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
    var = tk.StringVar(value=str(default))
    ttk.Entry(parent, textvariable=var, width=18).grid(row=row, column=1, sticky="w", padx=5, pady=2)
    return var


def make_labeled_combo(parent, row, label, values, default=None):
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=5, pady=2)
    var = tk.StringVar(value=default if default is not None else values[0])
    ttk.Combobox(parent, textvariable=var, values=values, state="readonly", width=16).grid(
        row=row, column=1, sticky="w", padx=5, pady=2
    )
    return var


def add_party_form(parent, idx):
    frame = ttk.LabelFrame(parent, text=f"Party member {idx + 1}")
    frame.pack(fill="x", padx=8, pady=6)

    fields = {}
    row = 0
    fields["name"] = make_labeled_entry(frame, row, "Name", f"Hero{idx + 1}"); row += 1
    fields["char_class"] = make_labeled_entry(frame, row, "Class", "Fighter"); row += 1
    fields["subclass"] = make_labeled_entry(frame, row, "Subclass", "Champion"); row += 1
    fields["level"] = make_labeled_entry(frame, row, "Level", 1); row += 1
    fields["ac"] = make_labeled_entry(frame, row, "AC", 15); row += 1
    fields["initiative"] = make_labeled_entry(frame, row, "Initiative", 2); row += 1
    fields["speed"] = make_labeled_entry(frame, row, "Speed", 30); row += 1
    fields["hp"] = make_labeled_entry(frame, row, "HP", 20); row += 1
    fields["proficiency_bonus"] = make_labeled_entry(frame, row, "Proficiency bonus", 2); row += 1
    fields["saving_throws"] = make_labeled_entry(frame, row, "Saving throws", "STR,CON"); row += 1
    fields["size"] = make_labeled_combo(frame, row, "Size", SIZE_OPTIONS, "Medium"); row += 1
    fields["weapon"] = make_labeled_combo(frame, row, "Weapon", list(WEAPONS.keys()), "Longsword"); row += 1
    fields["combat_style"] = make_labeled_combo(frame, row, "Combat style", STYLE_OPTIONS, "melee"); row += 1
    fields["flying_speed"] = make_labeled_entry(frame, row, "Flying speed", 0); row += 1
    fields["resistances"] = make_labeled_entry(frame, row, "Resistances", ""); row += 1
    fields["immunities"] = make_labeled_entry(frame, row, "Immunities", ""); row += 1

    for ability in ABILITY_KEYS:
        fields[f"ability_{ability}"] = make_labeled_entry(frame, row, ability, 10)
        row += 1

    return fields


def add_enemy_form(parent, idx):
    frame = ttk.LabelFrame(parent, text=f"Enemy {idx + 1}")
    frame.pack(fill="x", padx=8, pady=6)

    fields = {}
    row = 0
    fields["name"] = make_labeled_entry(frame, row, "Name", f"Monster{idx + 1}"); row += 1
    fields["ac"] = make_labeled_entry(frame, row, "AC", 13); row += 1
    fields["initiative"] = make_labeled_entry(frame, row, "Initiative", 1); row += 1
    fields["speed"] = make_labeled_entry(frame, row, "Speed", 30); row += 1
    fields["hp"] = make_labeled_entry(frame, row, "HP", 20); row += 1
    fields["proficiency_bonus"] = make_labeled_entry(frame, row, "Proficiency bonus", 2); row += 1
    fields["saving_throws"] = make_labeled_entry(frame, row, "Saving throws", "STR,CON"); row += 1
    fields["size"] = make_labeled_combo(frame, row, "Size", SIZE_OPTIONS, "Medium"); row += 1
    fields["weapon"] = make_labeled_combo(frame, row, "Weapon", list(WEAPONS.keys()), "Greataxe"); row += 1
    fields["combat_style"] = make_labeled_combo(frame, row, "Combat style", STYLE_OPTIONS, "melee"); row += 1
    fields["flying_speed"] = make_labeled_entry(frame, row, "Flying speed", 0); row += 1
    fields["attack_count"] = make_labeled_entry(frame, row, "Attack count", 1); row += 1
    fields["resistances"] = make_labeled_entry(frame, row, "Resistances", ""); row += 1
    fields["immunities"] = make_labeled_entry(frame, row, "Immunities", ""); row += 1

    fields["multiattack"] = tk.BooleanVar(value=False)
    ttk.Label(frame, text="Multiattack").grid(row=row, column=0, sticky="w", padx=5, pady=2)
    ttk.Checkbutton(frame, variable=fields["multiattack"]).grid(row=row, column=1, sticky="w", padx=5, pady=2)
    row += 1

    for ability in ABILITY_KEYS:
        fields[f"ability_{ability}"] = make_labeled_entry(frame, row, ability, 10)
        row += 1

    return fields


class CombatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Combat Simulation Setup")
        self.party_forms = []
        self.enemy_forms = []

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Party members").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.party_count = tk.StringVar(value="3")
        ttk.Entry(top, textvariable=self.party_count, width=8).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(top, text="Enemies").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.enemy_count = tk.StringVar(value="2")
        ttk.Entry(top, textvariable=self.enemy_count, width=8).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(top, text="Simulations").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.num_simulations = tk.StringVar(value="100")
        ttk.Entry(top, textvariable=self.num_simulations, width=8).grid(row=0, column=5, padx=5, pady=5)

        ttk.Button(top, text="Generate forms", command=self.generate_forms).grid(row=0, column=6, padx=10, pady=5)
        ttk.Button(top, text="Run simulation", command=self.run_simulation).grid(row=0, column=7, padx=10, pady=5)

        self.canvas = tk.Canvas(root, height=700)
        self.scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.generate_forms()

    def generate_forms(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.party_forms.clear()
        self.enemy_forms.clear()

        try:
            party_n = int(self.party_count.get())
            enemy_n = int(self.enemy_count.get())
        except ValueError:
            messagebox.showerror("Invalid input", "Party and enemy counts must be integers.")
            return

        if party_n < 1 or enemy_n < 1:
            messagebox.showerror("Invalid input", "You need at least 1 party member and 1 enemy.")
            return

        ttk.Label(self.scrollable_frame, text="Party setup", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=5)
        for i in range(party_n):
            self.party_forms.append(add_party_form(self.scrollable_frame, i))

        ttk.Label(self.scrollable_frame, text="Enemy setup", font=("Arial", 12, "bold")).pack(anchor="w", padx=8, pady=5)
        for i in range(enemy_n):
            self.enemy_forms.append(add_enemy_form(self.scrollable_frame, i))

    def run_simulation(self):
        try:
            num_simulations = int(self.num_simulations.get())
            if num_simulations < 1:
                raise ValueError

            party = [build_party_member(form) for form in self.party_forms]
            enemies = [build_enemy(form) for form in self.enemy_forms]

            run_pipeline(party, enemies, num_simulations)

            messagebox.showinfo(
                "Done",
                "Simulation completed.\nGenerated: combat_simulation_report.pdf"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = CombatApp(root)
    root.mainloop()