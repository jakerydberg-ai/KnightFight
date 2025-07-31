import random
import copy
import os
import sys

# Add the parent directory to the Python path to allow imports from the main folder
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

# Import the main game module and activate silent mode
import knight_battle_game

knight_battle_game.SILENT_MODE = True

from gamedata import ALL_KNIGHTS, ALL_MOVES, ALL_ABILITIES
from knight_battle_game import Knight, Player, Battle


class HeadlessBattle(Battle):
    """A version of the Battle class that runs without user input and logging."""

    def display_battlefield(self):
        """Override to do nothing."""
        pass

    def run_simulation(self):
        self.initial_setup()
        round_num = 1
        while (
            self.p1.has_living_knights()
            and self.p2.has_living_knights()
            and round_num < 50
        ):
            self.prepare_round()

            actions = self.get_all_actions()
            actions.sort(key=lambda x: (x[1].priority, x[0].speed), reverse=True)

            for knight, move, targets in actions:
                if knight.is_fainted:
                    continue
                self.execute_action(knight, move, targets)
                self.process_fainted()
                if not (self.p1.has_living_knights() and self.p2.has_living_knights()):
                    break

            if not (self.p1.has_living_knights() and self.p2.has_living_knights()):
                break

            self.end_of_round_effects()
            self.process_fainted()
            round_num += 1

        return self.generate_battle_log(round_num)

    def generate_battle_log(self, turns):
        winner = None
        if self.p1.has_living_knights() and not self.p2.has_living_knights():
            winner = self.p1.name
        elif self.p2.has_living_knights() and not self.p1.has_living_knights():
            winner = self.p2.name

        return {
            "winner": winner,
            "p1_survivors": len([k for k in self.p1.team if not k.is_fainted]),
            "p2_survivors": len([k for k in self.p2.team if not k.is_fainted]),
            "turns": turns,
        }

    def get_all_actions(self):
        actions = []
        all_knights = [
            k
            for k in self.p1.active_knights + self.p2.active_knights
            if k and not k.is_fainted
        ]
        all_knights.sort(key=lambda k: k.speed, reverse=True)

        for knight in all_knights:
            if "dazed" in knight.status_effects:
                continue

            if knight.charge_state:
                move, targets = knight.charge_state
                actions.append((knight, move, targets))
                knight.charge_state = None
                continue

            owner = self.p1 if knight in self.p1.active_knights else self.p2
            opponent_player = self.p2 if owner == self.p1 else self.p1

            move, targets = owner.ai_logic.get_action(
                self, owner, opponent_player, knight
            )
            if move:
                actions.append((knight, move, targets))
            else:
                benched = owner.get_living_bench()
                if benched:
                    slot = owner.active_knights.index(knight)
                    owner.active_knights[slot] = benched[0]

        return actions

    def initial_setup(self):
        for player in [self.p1, self.p2]:
            benched = player.get_living_bench()
            if len(benched) >= 2:
                player.active_knights = [benched[0], benched[1]]
            elif len(benched) == 1:
                player.active_knights = [benched[0], None]

    def process_fainted(self):
        for player in [self.p1, self.p2]:
            for i, knight in enumerate(player.active_knights):
                if knight and knight.is_fainted:
                    benched = player.get_living_bench()
                    player.active_knights[i] = benched[0] if benched else None
