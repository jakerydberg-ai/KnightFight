import random
import json
import copy
import os
import sys

# Add the parent directory to the Python path to allow imports from the main folder
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from gamedata import ALL_MOVES
from knight_battle_game import Knight, Player, Battle


class AIPlayer:
    def __init__(self, name, team_file_path):
        self.player = Player(name, self.load_team(team_file_path))
        self.brain = AIBrain()

    def load_team(self, file_path):
        with open(file_path, "r") as f:
            team_data = json.load(f)
        return [Knight(knight_data) for knight_data in team_data]

    def get_action(self, battle_state, owner, opponent_player, acting_knight):
        return self.brain.get_best_move(
            battle_state, owner, opponent_player, acting_knight
        )


class AIBrain:
    def __init__(self, brain_file=None):
        self.brain_file = brain_file
        self.knowledge = self.load_knowledge() if brain_file else {}
        self.fitness = 0

    def load_knowledge(self):
        try:
            with open(self.brain_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_knowledge(self):
        if self.brain_file:
            with open(self.brain_file, "w") as f:
                json.dump(self.knowledge, f, indent=4)

    def get_best_move(self, battle_state, ai_player, opponent_player, active_knight):
        state_key = self.get_state_key(ai_player, opponent_player)

        if not active_knight or active_knight.is_fainted:
            return None, None

        if state_key in self.knowledge:
            move_name = self.knowledge.get(state_key)
            move = next((m for m in active_knight.moves if m.name == move_name), None)
            if move is None:
                move = random.choice(active_knight.moves)
        else:
            move = random.choice(active_knight.moves)
            self.knowledge[state_key] = move.name

        targets = []
        if move.target_type == "self":
            targets = [active_knight]
        elif move.target_type == "single_ally":
            ally = next(
                (
                    k
                    for k in ai_player.active_knights
                    if k and k != active_knight and not k.is_fainted
                ),
                None,
            )
            targets = [ally] if ally else [active_knight]
        elif move.target_type == "team_synergy":
            ally = next(
                (
                    k
                    for k in ai_player.active_knights
                    if k and k != active_knight and not k.is_fainted
                ),
                None,
            )
            targets = [active_knight, ally] if ally else [active_knight]
        elif move.target_type == "all_enemies":
            targets = [
                k for k in opponent_player.active_knights if k and not k.is_fainted
            ]
        elif move.target_type == "all_adjacent":
            ally = next(
                (
                    k
                    for k in ai_player.active_knights
                    if k and k != active_knight and not k.is_fainted
                ),
                None,
            )
            opponents = [
                k for k in opponent_player.active_knights if k and not k.is_fainted
            ]
            targets = opponents + ([ally] if ally else [])
        elif move.target_type == "single_enemy":
            possible_targets = [
                k
                for k in opponent_player.active_knights
                if k and not k.is_fainted and not k.is_invisible
            ]
            if possible_targets:
                targets = [random.choice(possible_targets)]

        return move, targets

    def get_state_key(self, ai_player, opponent_player):
        def get_knight_details(knight):
            if not knight:
                return "empty"

            details = [
                knight.name,
                f"hp:{int(knight.hp/knight.max_hp*100)}",
            ]
            if knight.status_effects:
                details.append(
                    f"status:{','.join(sorted(knight.status_effects.keys()))}"
                )
            if any(v != 0 for v in knight.stat_stages.values()):
                stats = []
                for stat, val in knight.stat_stages.items():
                    if val != 0:
                        stats.append(f"{stat}:{val:+}")
                details.append(f"stats:{','.join(sorted(stats))}")
            if knight.active_effects:
                details.append(f"fx:{','.join(sorted(knight.active_effects.keys()))}")

            return "|".join(details)

        my_knights_str = [get_knight_details(k) for k in ai_player.active_knights]
        opponent_knights_str = [
            get_knight_details(k) for k in opponent_player.active_knights
        ]

        weather = Battle.current_weather["type"]

        return f"MyTeam:{';'.join(my_knights_str)}_vs_TheirTeam:{';'.join(opponent_knights_str)}_Weather:{weather}"
