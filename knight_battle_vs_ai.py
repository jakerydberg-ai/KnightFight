import time
import random
import os
import base64
import json
import copy
import sys

# Add the main project directory to the Python path
# This allows modules in subfolders (like AI_Zone) to import from the root
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from gamedata import ALL_KNIGHTS, ALL_MOVES, ALL_ABILITIES, Move
from knight_battle_game import (
    Battle,
    Knight,
    Player,
    load_team_from_file,
    clear_screen,
    type_text,
)
from AI_Zone.knight_ai_player import AIPlayer  # This import will now work correctly


class BattleVsAI(Battle):
    def initial_setup(self):
        """
        Overrides the base setup to handle both human and AI knight selection.
        """
        # Human Player Setup
        self.choose_knight_for_slot(self.p1, 0)
        self.choose_knight_for_slot(self.p1, 1)

        # AI Player Setup
        type_text(f"{self.p2.name} is choosing its knights...")
        time.sleep(1)
        benched_ai = self.p2.get_living_bench()
        if len(benched_ai) >= 2:
            self.p2.active_knights[0] = benched_ai[0]
            self.p2.active_knights[1] = benched_ai[1]
            type_text(
                f"{self.p2.name} sends out {self.p2.active_knights[0].name} and {self.p2.active_knights[1].name}!"
            )
        elif len(benched_ai) == 1:
            self.p2.active_knights[0] = benched_ai[0]
            type_text(f"{self.p2.name} sends out {self.p2.active_knights[0].name}!")
        time.sleep(1)

    def get_all_actions(self):
        actions = []
        all_knights = [
            k
            for k in self.p1.active_knights + self.p2.active_knights
            if k and not k.is_fainted
        ]
        # Sort by speed to determine turn order for action selection
        all_knights.sort(key=lambda k: k.speed, reverse=True)

        for knight in all_knights:
            owner = self.p1 if knight in self.p1.active_knights else self.p2

            if owner == self.p1:  # Human Player
                opponent_player = self.p2
                self.display_battlefield()
                type_text(f"--- {owner.name}'s Turn: {knight.name} ---")
                action, details = self.get_action_for_knight(
                    knight, owner, opponent_player
                )
            else:  # AI Player
                opponent_player = self.p1
                self.display_battlefield()
                type_text(f"--- {owner.name}'s Turn: {knight.name} ---")

                # AI makes its decision for the specific knight whose turn it is
                move, targets = self.p2.ai_logic.get_action(
                    self, owner, opponent_player, knight
                )

                action, details = "move", (move, targets)
                time.sleep(1)  # Pause to simulate AI thinking

            if action == "move":
                move, target = details
                actions.append((knight, move, target))
            elif action == "switch":
                slot = owner.active_knights.index(knight)
                owner.active_knights[slot] = details
                self.log.append(
                    f"{owner.name} recalls {knight.name} and sends out {details.name}!"
                )
                time.sleep(1)

        return actions

    def process_fainted(self):
        """
        Overrides the base method to handle AI switching automatically and checks if a bench exists.
        """
        for player in [self.p1, self.p2]:
            for i, knight in enumerate(player.active_knights):
                if knight and knight.is_fainted:
                    self.display_battlefield()
                    self.log.append(f"{knight.name} has fainted!")
                    time.sleep(1)
                    player.active_knights[i] = None
                    if player.has_living_knights():
                        benched = player.get_living_bench()
                        if benched:  # Only proceed if there are knights to switch to
                            if player == self.p1:  # Human player
                                self.choose_knight_for_slot(player, i)
                            else:  # AI Player
                                type_text(
                                    f"{player.name} is choosing its next knight..."
                                )
                                time.sleep(1)
                                new_knight = benched[0]
                                player.active_knights[i] = new_knight
                                self.log.append(
                                    f"{player.name} sends out {new_knight.name}!"
                                )
                                time.sleep(1)
                    else:
                        self.log.append(f"{player.name} has no more knights!")


if __name__ == "__main__":
    clear_screen()
    print("--- Knight Battle Simulator vs. AI ---")

    p1_name = input("Enter your name: ")
    p1_team = load_team_from_file(p1_name)
    if not p1_team:
        exit()
    player1 = Player(p1_name, p1_team)
    print("Your team has been loaded!")

    # Setup AI Player
    ai_folder_path = os.path.join(script_dir, "AI_Zone")
    ai_team_path = os.path.join(ai_folder_path, "ai_opponent_team.json")
    ai_brain_path = os.path.join(ai_folder_path, "ai_brain.json")

    ai_player_obj = AIPlayer("Knightfall AI", ai_team_path)
    ai_player_obj.brain.brain_file = ai_brain_path
    ai_player_obj.brain.knowledge = ai_player_obj.brain.load_knowledge()

    player2 = ai_player_obj.player
    player2.ai_logic = ai_player_obj
    print("AI opponent is ready!")

    input("\nPress Enter to begin the battle...")

    battle = BattleVsAI(player1, player2)
    battle.run()
