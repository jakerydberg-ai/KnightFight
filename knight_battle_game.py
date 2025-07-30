import time
import random
import os
import base64
import json
import copy
from gamedata import ALL_KNIGHTS, ALL_MOVES, ALL_ABILITIES, Move


# --- Utility Functions ---
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def type_text(text, delay=0.03):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


# --- Core Game Classes ---
class Knight:
    def __init__(self, custom_data):
        self.name = custom_data["custom_name"]
        template = ALL_KNIGHTS[custom_data["template"]]
        self.faction = template.faction
        self.base_stats = custom_data["stats"]
        self.ability = ALL_ABILITIES[custom_data["ability"]]
        self.moves = [copy.deepcopy(ALL_MOVES[m]) for m in custom_data["moves"]]

        self.hp = self.base_stats["hp"]
        self.max_hp = self.base_stats["hp"]
        self.guard = 0
        self.status_effects = {}
        self.active_effects = {}
        self.is_fainted = False
        self.charge_state = None
        self.rampage_state = None
        self.is_parrying = False
        self.is_aegis_protected = False
        self.is_invisible = False
        self.consecutive_protects = 0
        self.disabled_moves = {}
        self.stat_stages = {"atk": 0, "def": 0, "spd": 0}

    @property
    def attack(self):
        val = self.base_stats["atk"]
        stage_mod = 1.0 + (self.stat_stages["atk"] * 0.50)
        val *= stage_mod
        if "weaken" in self.status_effects:
            val *= 0.7
        if self.ability.name == "Adrenaline" and self.status_effects:
            val *= 1.5
        if self.ability.name == "Last Stand" and self.hp <= self.max_hp / 3:
            val *= 1.5
        if (
            self.ability.name == "Divine Power"
            and Battle.current_weather["type"] == "Blazing Sun"
        ):
            val *= 1.5
        return int(val)

    @property
    def defense(self):
        val = self.base_stats["def"]
        stage_mod = 1.0 + (self.stat_stages["def"] * 0.50)
        val *= stage_mod
        if "vulnerable" in self.status_effects:
            val *= 0.7
        if Battle.current_weather["type"] == "Metalstorm" and self.faction == "Steel":
            val *= 1.5
        if Battle.current_weather["type"] == "Hailstorm" and self.faction == "Cryo":
            val *= 1.5
        return int(val)

    @property
    def speed(self):
        val = self.base_stats["spd"]
        stage_mod = 1.0 + (self.stat_stages["spd"] * 0.50)
        val *= stage_mod
        if "slowed" in self.status_effects and self.ability.name != "Grounded":
            val *= 0.5
        if (
            self.ability.name == "Chilling Finesse"
            and Battle.current_weather["type"] == "Hailstorm"
        ):
            val *= 2
        return int(val)

    def apply_status(self, status, duration, attacker=None):
        if status == "slowed" and self.ability.name == "Grounded":
            return f"{self.name}'s Grounded ability prevents it from being slowed!"
        if status not in self.status_effects:
            if attacker and attacker.ability.name == "Witch Doctor":
                duration += 2
            self.status_effects[status] = duration

            status_map = {
                "burn": "was set ablaze",
                "slowed": "felt a chill slow their pace",
                "cursed": "felt dread creep around their mind",
                "dazed": "clutched their helm in a daze",
                "vulnerable": "felt their armor splinter",
                "weaken": "felt their sword arm get sore",
            }
            display_status = status_map.get(status, status)
            return f"{self.name} {display_status}."
        return ""

    def take_damage(self, unmod_damage, move=None, ignore_defense=False):
        if (
            "eye_of_the_storm" in self.active_effects
            and random.random() < 0.3
            and not ignore_defense
        ):
            type_text(f"{self.name} avoided the attack with Eye of the Storm!")
            return 0
        damage = unmod_damage
        if not ignore_defense:
            if "mists_of_borealis" in self.active_effects:
                damage = int(damage * 0.5)
            if self.ability.name == "Reinforced":
                damage = int(damage * 0.9)
            if self.ability.name == "Permafrost" and move and move.rampage_turns > 0:
                damage = int(damage * 0.5)

            if self.guard > 0:
                max_reduction_from_cap = int(damage * 0.5)
                actual_reduction = min(self.guard, max_reduction_from_cap)
                damage -= actual_reduction
                guard_depletion = actual_reduction
                if move and move.guard_multiplier > 1.0:
                    guard_depletion = int(
                        actual_reduction * move.guard_multiplier * 0.25
                    )
                self.guard -= guard_depletion
                type_text(
                    f"{self.name}'s Guard reduced the damage by {actual_reduction}!"
                )
                if self.guard <= 0:
                    self.guard = 0
                    type_text(f"{self.name}'s Guard was broken!")

        final_damage = max(1, damage)
        self.hp -= final_damage

        if self.ability.name == "Ice Shield" and final_damage > 0:
            guard_gain = int(final_damage * 0.15)
            self.guard += guard_gain
            type_text(f"{self.name}'s Ice Shield created {guard_gain} Guard!")

        if self.hp <= 0:
            self.hp = 0
            self.is_fainted = True

        return final_damage

    def apply_self_effect(self, effect, damage_dealt=0):
        simple_effects = ["slowed", "weaken", "vulnerable", "dazed"]
        if effect in simple_effects:
            self.apply_status(effect, 2, attacker=self)
            return
        if "recoil" in effect:
            parts = effect.split("_")
            recoil_percent = int(parts[1])
            recoil_dmg = max(1, int(damage_dealt * (recoil_percent / 100)))
            type_text(f"{self.name} took {recoil_dmg} in recoil damage!")
            self.take_damage(recoil_dmg, ignore_defense=True)
            return

        parts = effect.split("_")
        i = 0
        while i < len(parts):
            stat_name = parts[i]
            if (i + 2) < len(parts):
                direction = parts[i + 1]
                try:
                    amount = int(parts[i + 2])
                    stat_key = stat_name[:3]
                    if direction == "up":
                        self.stat_stages[stat_key] = min(
                            6, self.stat_stages[stat_key] + amount
                        )
                        type_text(f"{self.name}'s {stat_name.capitalize()} rose!")
                    elif direction == "down":
                        self.stat_stages[stat_key] = max(
                            -6, self.stat_stages[stat_key] - amount
                        )
                        type_text(f"{self.name}'s {stat_name.capitalize()} fell!")
                    i += 3
                except (ValueError, KeyError):
                    i += 1
            else:
                i += 1

    def tick_statuses(self):
        for status in list(self.status_effects.keys()):
            self.status_effects[status] -= 1
            if self.status_effects[status] <= 0:
                del self.status_effects[status]
                type_text(f"{self.name} is no longer {status}.")
        for effect in list(self.active_effects.keys()):
            self.active_effects[effect] -= 1
            if self.active_effects[effect] <= 0:
                del self.active_effects[effect]
                if effect == "invisible":
                    self.is_invisible = False
                type_text(f"{self.name}'s {effect.replace('_', ' ')} wore off.")
        for move_name in list(self.disabled_moves.keys()):
            self.disabled_moves[move_name] -= 1
            if self.disabled_moves[move_name] <= 0:
                del self.disabled_moves[move_name]
                type_text(f"{self.name} can use {move_name} again.")

    def display_status(self):
        bar_length = 15
        filled_length = (
            int(bar_length * self.hp / self.max_hp) if self.max_hp > 0 else 0
        )
        bar = "█" * filled_length + "-" * (bar_length - filled_length)
        hp_str = f"HP: {self.hp}/{self.max_hp} [{bar}]"
        guard_str = f"| Guard: {self.guard}" if self.guard > 0 else ""

        stat_changes = []
        if self.stat_stages["atk"] != 0:
            stat_changes.append(f"Atk: {self.stat_stages['atk']:+}")
        if self.stat_stages["def"] != 0:
            stat_changes.append(f"Def: {self.stat_stages['def']:+}")
        if self.stat_stages["spd"] != 0:
            stat_changes.append(f"Spd: {self.stat_stages['spd']:+}")
        stat_str = "| " + ", ".join(stat_changes) if stat_changes else ""

        status_str = (
            "| " + ", ".join([k.capitalize() for k in self.status_effects.keys()])
            if self.status_effects
            else ""
        )
        return f"{hp_str} {guard_str} {stat_str} {status_str}"


class Player:
    def __init__(self, name, team):
        self.name = name
        self.team = team
        self.active_knights = [None, None]
        self.is_aoe_protected = False

    def has_living_knights(self):
        return any(not k.is_fainted for k in self.team)

    def get_living_bench(self):
        return [
            k for k in self.team if not k.is_fainted and k not in self.active_knights
        ]


class Battle:
    current_weather = {"type": "Clear", "turns_left": 0}

    def __init__(self, player1, player2):
        self.p1 = player1
        self.p2 = player2
        self.log = []

    def display_battlefield(self):
        clear_screen()
        print("=" * 70)
        weather = (
            f"Weather: {self.current_weather['type']} ({self.current_weather['turns_left']} turns left)"
            if self.current_weather["type"] != "Clear"
            else "Weather: Clear Skies"
        )
        print(f"  {weather.center(68)}")
        print("=" * 70)

        print(f"  {self.p2.name}'s Field:")
        for i, knight in enumerate(self.p2.active_knights):
            if knight:
                print(
                    f"    {i+1}: {knight.name:<15} ({knight.faction} | {knight.ability.name})"
                )
                print(f"       {knight.display_status()}")
        print("-" * 70)
        print(f"  {self.p1.name}'s Field:")
        for i, knight in enumerate(self.p1.active_knights):
            if knight:
                print(
                    f"    {i+1}: {knight.name:<15} ({knight.faction} | {knight.ability.name})"
                )
                print(f"       {knight.display_status()}")
        print("=" * 70)

        for entry in self.log:
            type_text(entry, delay=0.02)
        self.log = []
        print()

    def run(self):
        self.initial_setup()
        round_num = 1
        while self.p1.has_living_knights() and self.p2.has_living_knights():
            self.prepare_round()
            self.display_battlefield()
            self.log.append(f"--- Round {round_num} ---")

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
            input("\nPress Enter to continue...")

        self.announce_winner()

    def prepare_round(self):
        self.p1.is_aoe_protected = False
        self.p2.is_aoe_protected = False
        all_knights = [k for k in self.p1.active_knights + self.p2.active_knights if k]
        for knight in all_knights:
            knight.is_parrying = False
            knight.is_aegis_protected = False

    def initial_setup(self):
        for player in [self.p1, self.p2]:
            for i in range(2):
                self.choose_knight_for_slot(player, i)

    def choose_knight_for_slot(self, player, slot_index):
        clear_screen()
        type_text(f"{player.name}, choose a Knight for slot {slot_index + 1}:")
        benched = player.get_living_bench()
        for i, knight in enumerate(benched):
            print(f"  {i+1}. {knight.name} ({knight.faction})")

        while True:
            try:
                choice = int(input("Enter number: ")) - 1
                if 0 <= choice < len(benched):
                    player.active_knights[slot_index] = benched[choice]
                    type_text(f"{player.name} sends out {benched[choice].name}!")
                    time.sleep(1)
                    return
            except ValueError:
                print("Invalid input.")

    def get_all_actions(self):
        actions = []
        all_knights = [
            k
            for k in self.p1.active_knights + self.p2.active_knights
            if k and not k.is_fainted
        ]
        for knight in all_knights:
            owner = self.p1 if knight in self.p1.active_knights else self.p2
            opponent_player = self.p2 if owner == self.p1 else self.p1

            self.display_battlefield()
            type_text(f"--- {owner.name}'s Turn: {knight.name} ---")

            action, details = self.get_action_for_knight(knight, owner, opponent_player)

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

    def get_action_for_knight(self, knight, owner, opponent_player):
        while True:
            print(f"What will {knight.name} do?")
            print("1. Fight")
            print("2. Switch")
            try:
                choice = int(input("Choice: "))
                if choice == 1:
                    while True:
                        self.display_battlefield()
                        type_text(f"--- {owner.name}'s Turn: {knight.name} ---")
                        move = self.get_move_choice(knight)
                        if not move:
                            break

                        self.display_battlefield()
                        type_text(f"--- {owner.name}'s Turn: {knight.name} ---")
                        print(f"Move: {move.name}")
                        print(f"Description: {move.description}")

                        needs_target = move.target_type in [
                            "single_enemy",
                            "single_ally",
                        ]
                        prompt = "1. Select Target" if needs_target else "1. Confirm"
                        print(f"\n{prompt}")
                        print("2. Back")

                        confirm_choice = input("Choice: ")
                        if confirm_choice == "1":
                            target = self.get_target(
                                knight, move, owner, opponent_player
                            )
                            return "move", (move, target)
                        else:
                            continue
                elif choice == 2:
                    benched_knight = self.get_switch_choice(owner)
                    if benched_knight:
                        return "switch", benched_knight
            except ValueError:
                print("Invalid input.")

    def get_move_choice(self, knight):
        print("Choose a move:")
        valid_moves = [m for m in knight.moves if m.name not in knight.disabled_moves]
        for i, move in enumerate(valid_moves):
            print(f"  {i+1}. {move.name}")
        print(f"  {len(valid_moves)+1}. Back")

        while True:
            try:
                choice = int(input("Move choice: ")) - 1
                if 0 <= choice < len(valid_moves):
                    return valid_moves[choice]
                elif choice == len(valid_moves):
                    return None
            except ValueError:
                print("Invalid input.")

    def get_switch_choice(self, owner):
        benched = owner.get_living_bench()
        if not benched:
            print("No knights to switch to!")
            time.sleep(1)
            return None
        print("Switch to which knight?")
        for i, knight in enumerate(benched):
            print(f"  {i+1}. {knight.name}")
        print(f"  {len(benched)+1}. Back")
        while True:
            try:
                choice = int(input("Switch choice: ")) - 1
                if 0 <= choice < len(benched):
                    return benched[choice]
                elif choice == len(benched):
                    return None
            except ValueError:
                print("Invalid input.")

    def get_target(self, attacker, move, owner, opponent_player):
        if move.target_type == "team_synergy":
            ally = next(
                (k for k in owner.active_knights if k != attacker and not k.is_fainted),
                None,
            )
            return [attacker, ally] if ally else [attacker]
        if move.target_type == "self":
            return [attacker]

        if move.target_type == "single_ally":
            possible_targets = [
                k for k in owner.active_knights if k and not k.is_fainted
            ]
            if len(possible_targets) == 1:
                return possible_targets
            else:
                print("Choose a target:")
                for i, t in enumerate(possible_targets):
                    print(f"  {i+1}. {t.name}")
                while True:
                    try:
                        choice = int(input("Target: ")) - 1
                        if 0 <= choice < len(possible_targets):
                            return [possible_targets[choice]]
                    except ValueError:
                        print("Invalid input.")

        if move.target_type == "all_adjacent":
            ally = next(
                (k for k in owner.active_knights if k != attacker and not k.is_fainted),
                None,
            )
            opponents = [
                k for k in opponent_player.active_knights if k and not k.is_fainted
            ]
            return opponents + ([ally] if ally else [])

        possible_targets = [
            k
            for k in opponent_player.active_knights
            if k and not k.is_fainted and not k.is_invisible
        ]
        if not possible_targets:
            return []

        if len(possible_targets) == 1 or move.target_type == "all_enemies":
            return opponent_player.active_knights  # Target all, even invisible ones
        else:
            print("Choose a target:")
            for i, t in enumerate(possible_targets):
                print(f"  {i+1}. {t.name}")
            while True:
                try:
                    choice = int(input("Target: ")) - 1
                    if 0 <= choice < len(possible_targets):
                        return [possible_targets[choice]]
                except ValueError:
                    print("Invalid input.")

    def execute_action(self, knight: Knight, move: Move, targets):
        if knight.is_invisible and move.power > 0:
            knight.is_invisible = False
            knight.active_effects.pop("invisible", None)
            self.log.append(f"{knight.name} reappeared!")

        if move.is_protection_move:
            if move.name != "Mists of Borealis":
                fail_chance = 1 - (0.5**knight.consecutive_protects)
                if random.random() < fail_chance:
                    self.log.append(f"{knight.name}'s {move.name}... but it failed!")
                    knight.consecutive_protects = 0
                    return
                knight.consecutive_protects += 1
        else:
            knight.consecutive_protects = 0

        if move.name == "Parry":
            knight.is_parrying = True
            knight.apply_self_effect(move.self_effect)
            self.log.append(f"{knight.name} takes a stance, ready to parry!")
            return

        if move.name == "Royal Aegis":
            knight.is_aegis_protected = True
            self.log.append(f"{knight.name} raises its shield!")
            return

        owner = self.p1 if knight in self.p1.active_knights else self.p2
        if move.name == "Shield Wall":
            owner.is_aoe_protected = True
            self.log.append(f"{knight.name} creates a protective wall for the team!")
            return

        if not isinstance(targets, list):
            targets = [targets]

        if move.target_type == "team_synergy":
            ally = next((k for k in targets if k != knight), None)
            if ally and ally.faction == knight.faction:
                self.log.append(f"{knight.name} and {ally.name} resonate with synergy!")
                for member in targets:
                    if member:
                        self.apply_move_effect(knight, move, member)
            else:
                self.apply_move_effect(knight, move, knight)
            return

        for target in targets:
            if not target or target.is_fainted:
                continue
            self.apply_move_effect(knight, move, target)

    def apply_move_effect(self, attacker: Knight, move: Move, target: Knight):
        owner_of_target = self.p1 if target in self.p1.active_knights else self.p2
        if (
            move.target_type in ["all_enemies", "all_adjacent"]
            and owner_of_target.is_aoe_protected
            and target in owner_of_target.active_knights
        ):
            self.log.append(
                f"The attack on {target.name} was blocked by a Shield Wall!"
            )
            return

        if target.is_parrying:
            self.log.append(
                f"{attacker.name}'s attack hit {target.name}... but struck their guard!"
            )
            attacker.disabled_moves[move.name] = 2
            self.log.append(f"{attacker.name}'s {move.name} is disabled!")
            return

        if target.is_aegis_protected:
            self.log.append(
                f"{attacker.name}'s attack was blocked by {target.name}'s Royal Aegis!"
            )
            if move.power > 0:
                attacker.apply_status("weaken", 2, attacker=target)
            return

        self.log.append(f"{attacker.name} uses {move.name} on {target.name}!")
        time.sleep(1)

        if move.power > 0:
            damage = (attacker.attack * move.power) // target.defense
            dealt = target.take_damage(damage, move)
            if dealt > 0:
                self.log.append(f"It dealt {dealt} damage to {target.name}!")
                if (
                    "consecration" in target.active_effects
                    and move.target_type == "single_enemy"
                ):
                    status_msg = attacker.apply_status("burn", 3, attacker=target)
                    if status_msg:
                        self.log.append(status_msg)
                if target.ability.name == "Soul Ablaze" and random.random() < 0.3:
                    status_msg = attacker.apply_status("burn", 3, attacker=target)
                    if status_msg:
                        self.log.append(
                            f"{attacker.name} was burned by {target.name}'s Soul Ablaze!"
                        )

        if move.effect:
            if random.random() <= (move.effect_chance / 100):
                status_msg = target.apply_status(
                    move.effect, move.effect_duration, attacker=attacker
                )
                if status_msg:
                    self.log.append(status_msg)

        if move.sets_weather:
            self.current_weather["type"] = move.sets_weather
            self.current_weather["turns_left"] = 5
            self.log.append(f"The weather changed to {move.sets_weather}!")

        if move.self_effect:
            target.apply_self_effect(move.self_effect)

        if move.synergy_effect:
            target.active_effects[move.synergy_effect] = move.effect_duration
            if move.synergy_effect == "invisible":
                target.is_invisible = True
            self.log.append(
                f"{target.name} is now affected by {move.synergy_effect.replace('_', ' ')}!"
            )

    def process_fainted(self):
        for player in [self.p1, self.p2]:
            for i, knight in enumerate(player.active_knights):
                if knight and knight.is_fainted:
                    self.display_battlefield()
                    self.log.append(f"{knight.name} has fainted!")
                    time.sleep(1)
                    player.active_knights[i] = None
                    if player.has_living_knights():
                        self.choose_knight_for_slot(player, i)
                    else:
                        self.log.append(f"{player.name} has no more knights!")

    def end_of_round_effects(self):
        self.log.append("--- End of Round ---")
        if self.current_weather["turns_left"] > 0:
            self.current_weather["turns_left"] -= 1
            if self.current_weather["turns_left"] == 0:
                self.log.append(f"The {self.current_weather['type']} subsided.")
                self.current_weather["type"] = "Clear"
            else:
                self.log.append(f"The {self.current_weather['type']} continues...")

        all_knights = [
            k
            for k in self.p1.active_knights + self.p2.active_knights
            if k and not k.is_fainted
        ]
        for knight in all_knights:
            if "burn" in knight.status_effects:
                burn_damage = int(knight.max_hp * 0.08)
                knight.hp -= burn_damage
                self.log.append(f"{knight.name} is seared with scorching flames.")

            knight.tick_statuses()

    def announce_winner(self):
        clear_screen()
        winner = self.p1.name if self.p1.has_living_knights() else self.p2.name
        type_text(f"{winner} is the winner!", delay=0.05)
        print("\n--- Battle Over ---")


def decode_team_from_json(team_data):
    try:
        return [Knight(knight_info) for knight_info in team_data]
    except Exception as e:
        print(f"Error decoding team data: {e}")
        return None


def load_team_from_file(player_name):
    team = None
    while not team:
        filepath = input(
            f"{player_name}, enter the path to your Warband file (e.g., team1.json):\n"
        )
        if not filepath:
            print("No file entered. Exiting.")
            return None

        try:
            with open(filepath, "r") as f:
                team_data = json.load(f)
            team = decode_team_from_json(team_data)
            if not team:
                print("Invalid team file format. Please try again.")
        except FileNotFoundError:
            print(
                f"Error: File not found at '{filepath}'. Please check the name and try again."
            )
            team = None
        except Exception as e:
            print(f"Could not load or parse the team file: {e}. Please try again.")
            team = None

    return team


if __name__ == "__main__":
    clear_screen()
    print("--- Knight Battle Simulator v5 (File Loading Update) ---")

    p1_name = input("Enter Player 1's name: ")
    p1_team = load_team_from_file(p1_name)
    if not p1_team:
        exit()
    player1 = Player(p1_name, p1_team)
    print("Player 1's team loaded successfully!")

    p2_name = input("\nEnter Player 2's name: ")
    p2_team = load_team_from_file(p2_name)
    if not p2_team:
        exit()
    player2 = Player(p2_name, p2_team)
    print("Player 2's team loaded successfully!")

    input("\nBoth teams loaded. Press Enter to begin the battle...")

    battle = Battle(player1, player2)
    battle.run()
