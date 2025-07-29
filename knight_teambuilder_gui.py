import tkinter as tk
from tkinter import ttk, messagebox, font, filedialog
import base64
import os
import json
import copy
from gamedata import ALL_KNIGHTS, ALL_MOVES, ALL_ABILITIES

# --- Themed Tooltip Class ---
class Tooltip:
    """Create a themed tooltip for a given widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                         background="#2E2E2E", foreground="#E0E0E0", relief='solid', borderwidth=1,
                         wraplength=200, font=("Garamond", 10))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

# --- Main Application ---
class TeamBuilderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Knightfall: Team Builder")
        self.root.geometry("850x650")
        self.root.minsize(800, 600)
        self.root.configure(bg="#1E1E1E")

        self.setup_styles()
        
        self.team = []
        self.available_templates = list(ALL_KNIGHTS.keys())
        self.stat_change_job = None # For hold-to-increment
        self.create_main_layout()

    def setup_styles(self):
        self.title_font = font.Font(family="Garamond", size=18, weight="bold")
        self.label_font = font.Font(family="Garamond", size=12)
        self.button_font = font.Font(family="Garamond", size=11, weight="bold")

        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background="#1E1E1E")
        style.configure("TLabel", background="#1E1E1E", foreground="#E0E0E0", font=self.label_font)
        style.configure("TButton", background="#4A4A4A", foreground="#E0E0E0", font=self.button_font, borderwidth=1, focusthickness=3, focuscolor='none')
        style.map("TButton", background=[('active', '#6E6E6E'), ('disabled', '#3A3A3A')])
        
        style.configure("Title.TLabel", font=self.title_font, foreground="#D4AF37")
        style.configure("Gold.TButton", foreground="#D4AF37")
        style.configure("TLabelframe", background="#2E2E2E", bordercolor="#4A4A4A")
        style.configure("TLabelframe.Label", background="#2E2E2E", foreground="#D4AF37", font=("Garamond", 12, "bold"))
        style.configure("TCombobox", fieldbackground="#4A4A4A", background="#4A4A4A", foreground="#E0E0E0", arrowcolor="#D4AF37")
        style.configure("TCheckbutton", background="#2E2E2E", foreground="#E0E0E0", font=("Garamond", 11))
        style.map("TCheckbutton", background=[('active', '#4A4A4A')], indicatorcolor=[('selected', '#D4AF37')])

    def create_main_layout(self):
        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(self.main_pane, width=250)
        self.main_pane.add(left_frame, weight=1)

        ttk.Label(left_frame, text="Your Warband", style="Title.TLabel").pack(pady=10)
        self.team_display = tk.Listbox(left_frame, height=10, width=40, bg="#2E2E2E", fg="#E0E0E0", selectbackground="#D4AF37", font=("Garamond", 11), borderwidth=0, highlightthickness=1, highlightbackground="#4A4A4A")
        self.team_display.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(pady=10)

        self.save_button = ttk.Button(button_frame, text="Save Warband", command=self.save_team, state=tk.DISABLED, style="Gold.TButton")
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.load_button = ttk.Button(button_frame, text="Load Warband", command=self.load_team)
        self.load_button.pack(side=tk.LEFT, padx=5)

        self.right_frame = ttk.Frame(self.main_pane)
        self.main_pane.add(self.right_frame, weight=3)
        
        self.show_initial_message()

    def show_initial_message(self):
        for widget in self.right_frame.winfo_children():
            widget.destroy()
        
        ttk.Label(self.right_frame, text="Your Warband is empty.", style="Title.TLabel").pack(pady=20)
        self.add_knight_button = ttk.Button(self.right_frame, text="Recruit a Knight", command=self.show_knight_builder)
        self.add_knight_button.pack(pady=10)

    def show_knight_builder(self):
        if len(self.team) >= 6:
            messagebox.showinfo("Team Full", "You already have 6 knights in your team.")
            return

        for widget in self.right_frame.winfo_children():
            widget.destroy()

        ttk.Label(self.right_frame, text="Recruit a New Knight", style="Title.TLabel").pack(pady=10)

        template_frame = ttk.LabelFrame(self.right_frame, text="Choose Template")
        template_frame.pack(padx=10, pady=10, fill="x")
        
        self.template_var = tk.StringVar()
        template_menu = ttk.Combobox(template_frame, textvariable=self.template_var, values=self.available_templates, state="readonly", width=30)
        template_menu.pack(pady=5, padx=5)
        template_menu.bind("<<ComboboxSelected>>", self.update_builder_ui)
        
        self.builder_content_frame = ttk.Frame(self.right_frame)
        self.builder_content_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
    def update_builder_ui(self, event=None):
        template_name = self.template_var.get()
        if not template_name: return

        for widget in self.builder_content_frame.winfo_children():
            widget.destroy()

        template = ALL_KNIGHTS[template_name]
        
        custom_grid = ttk.Frame(self.builder_content_frame)
        custom_grid.pack(fill="both", expand=True)
        custom_grid.columnconfigure(1, weight=1)

        left_custom_frame = ttk.Frame(custom_grid)
        left_custom_frame.grid(row=0, column=0, padx=5, sticky="new")

        name_frame = ttk.LabelFrame(left_custom_frame, text="Name")
        name_frame.pack(pady=5, fill="x")
        self.custom_name_var = tk.StringVar(value=template.name)
        ttk.Entry(name_frame, textvariable=self.custom_name_var, width=25, font=("Garamond", 11)).pack(pady=5, padx=5)

        stats_frame = ttk.LabelFrame(left_custom_frame, text="Stats (50 Bonus Points)")
        stats_frame.pack(pady=5, fill="x")
        self.stat_vars = {}
        self.base_stats = copy.deepcopy(template.base_stats)
        self.points_remaining = 50
        self.points_label = ttk.Label(stats_frame, text=f"Points Remaining: {self.points_remaining}")
        self.points_label.pack()

        for stat, value in self.base_stats.items():
            frame = ttk.Frame(stats_frame)
            frame.pack(fill='x', expand=True, padx=5, pady=2)
            ttk.Label(frame, text=f"{stat.upper()}:", width=5).pack(side=tk.LEFT)
            var = tk.IntVar(value=value)
            self.stat_vars[stat] = var
            
            entry = ttk.Entry(frame, textvariable=var, width=5, state="readonly", font=("Garamond", 11))
            entry.pack(side=tk.LEFT, padx=5)
            
            plus_button = ttk.Button(frame, text="+", width=2)
            plus_button.pack(side=tk.LEFT)
            plus_button.bind('<ButtonPress-1>', lambda e, s=stat, d=1: self.start_stat_change(s, d))
            plus_button.bind('<ButtonRelease-1>', self.stop_stat_change)

            minus_button = ttk.Button(frame, text="-", width=2)
            minus_button.pack(side=tk.LEFT)
            minus_button.bind('<ButtonPress-1>', lambda e, s=stat, d=-1: self.start_stat_change(s, d))
            minus_button.bind('<ButtonRelease-1>', self.stop_stat_change)


        ability_frame = ttk.LabelFrame(left_custom_frame, text="Ability")
        ability_frame.pack(pady=5, fill="x", expand=True)
        faction_abilities = [a for a in ALL_ABILITIES.values() if a.faction == template.faction]
        generic_abilities = [a for a in ALL_ABILITIES.values() if a.faction == "Generic"]
        self.available_abilities = sorted(faction_abilities, key=lambda a: a.name) + sorted(generic_abilities, key=lambda a: a.name)
        
        self.ability_var = tk.StringVar()
        ability_menu = ttk.Combobox(ability_frame, textvariable=self.ability_var, values=[a.name for a in self.available_abilities], state="readonly")
        ability_menu.pack(pady=5)
        ability_menu.bind("<<ComboboxSelected>>", self.update_ability_description)
        self.ability_desc_label = ttk.Label(ability_frame, text="", wraplength=200, justify=tk.LEFT)
        self.ability_desc_label.pack(pady=5, padx=5, fill='x')

        moves_frame = ttk.LabelFrame(custom_grid, text="Moves (Select 5)")
        moves_frame.grid(row=0, column=1, padx=5, sticky="nsew")
        
        learnset = [ALL_MOVES[m] for m in template.learnset]
        generic_moves = [m for m in ALL_MOVES.values() if m.faction == "Generic"]
        all_possible_moves = list(set(learnset + generic_moves))
        
        available_moves = sorted(all_possible_moves, key=lambda m: (m.faction == 'Generic', m.name))
        
        self.move_vars = {}
        self.move_checkboxes = []
        for move in available_moves:
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(moves_frame, text=f"{move.name} ({move.faction})", variable=var, command=self.check_move_count, style="TCheckbutton")
            cb.pack(anchor=tk.W, padx=10, pady=2)
            self.move_vars[move.name] = var
            self.move_checkboxes.append(cb)
            Tooltip(cb, move.description)

        self.finalize_button = ttk.Button(self.builder_content_frame, text="Add Knight to Warband", command=self.finalize_knight, style="Gold.TButton")
        self.finalize_button.pack(pady=20)

    def start_stat_change(self, stat, delta):
        self.change_stat(stat, delta)
        self.stat_change_job = self.root.after(400, lambda: self.continuous_stat_change(stat, delta))

    def continuous_stat_change(self, stat, delta):
        self.change_stat(stat, delta)
        self.stat_change_job = self.root.after(75, lambda: self.continuous_stat_change(stat, delta))

    def stop_stat_change(self, event):
        if self.stat_change_job:
            self.root.after_cancel(self.stat_change_job)
            self.stat_change_job = None

    def update_ability_description(self, event=None):
        selected_ability_name = self.ability_var.get()
        for ability in self.available_abilities:
            if ability.name == selected_ability_name:
                self.ability_desc_label.config(text=ability.description)
                break

    def change_stat(self, stat, delta):
        current_val = self.stat_vars[stat].get()
        base_val = self.base_stats[stat]

        if delta > 0 and self.points_remaining > 0:
            self.stat_vars[stat].set(current_val + delta)
            self.points_remaining -= delta
        elif delta < 0 and current_val > base_val:
            self.stat_vars[stat].set(current_val + delta)
            self.points_remaining += abs(delta)
        
        self.points_label.config(text=f"Points Remaining: {self.points_remaining}")

    def check_move_count(self):
        selected_count = sum(1 for var in self.move_vars.values() if var.get())
        if selected_count >= 5:
            for cb, (name, var) in zip(self.move_checkboxes, self.move_vars.items()):
                if not var.get():
                    cb.config(state=tk.DISABLED)
        else:
            for cb in self.move_checkboxes:
                cb.config(state=tk.NORMAL)

    def finalize_knight(self):
        selected_moves = [name for name, var in self.move_vars.items() if var.get()]
        if len(selected_moves) != 5:
            messagebox.showerror("Error", "You must select exactly 5 moves.")
            return
        
        if not self.ability_var.get():
            messagebox.showerror("Error", "You must select an ability.")
            return

        knight_data = {
            "template": self.template_var.get(),
            "custom_name": self.custom_name_var.get(),
            "stats": {stat: var.get() for stat, var in self.stat_vars.items()},
            "ability": self.ability_var.get(),
            "moves": selected_moves
        }
        
        self.team.append(knight_data)
        self.update_team_display()
        self.show_initial_message()

        if len(self.team) == 6:
            self.add_knight_button.config(state=tk.DISABLED)
            self.save_button.config(state=tk.NORMAL)
            messagebox.showinfo("Warband Complete", "Your warband is full. You can now save your team.")

    def update_team_display(self):
        self.team_display.delete(0, tk.END)
        for knight in self.team:
            self.team_display.insert(tk.END, f" {knight['custom_name']} ({knight['template']})")

    def save_team(self):
        if len(self.team) < 6:
            messagebox.showwarning("Incomplete Team", "You must have 6 knights in your warband to save.")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Knightfall Team", "*.json"), ("All Files", "*.*")],
            title="Save Warband As..."
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'w') as f:
                json.dump(self.team, f, indent=4)
            messagebox.showinfo("Success", f"Team saved to {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Error Saving File", f"An error occurred: {e}")

    def load_team(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Knightfall Team", "*.json"), ("All Files", "*.*")],
            title="Load Warband From..."
        )
        if not filepath:
            return
        
        try:
            with open(filepath, 'r') as f:
                loaded_team = json.load(f)
            
            # Basic validation
            if isinstance(loaded_team, list) and len(loaded_team) == 6:
                self.team = loaded_team
                self.update_team_display()
                self.save_button.config(state=tk.NORMAL)
                self.add_knight_button.config(state=tk.DISABLED)
                messagebox.showinfo("Success", "Team loaded successfully.")
            else:
                raise ValueError("Invalid team file format.")
        except Exception as e:
            messagebox.showerror("Error Loading File", f"Could not load or parse the team file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TeamBuilderApp(root)
    root.mainloop()
