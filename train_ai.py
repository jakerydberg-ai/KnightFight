import json
import random
import copy
import os
import sys

# Add the script's directory and parent directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(script_dir)
sys.path.append(parent_dir)

from headless_battle import HeadlessBattle
from knight_battle_game import Knight, Player
from gamedata import ALL_MOVES
from knight_ai_training import AIBrain, AIPlayer

# --- Training Configuration ---
GENERATIONS = 1000
POPULATION_SIZE = 80


def print_progress_bar(iteration, total, prefix="", suffix="", length=50, fill="█"):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + "-" * (length - filled_length)
    sys.stdout.write(f"\r{prefix} |{bar}| {percent}% {suffix}")
    sys.stdout.flush()


def calculate_fitness(battle_log, player_name):
    fitness = 0
    if battle_log["winner"] == player_name:
        fitness += 1000
        survivors = battle_log[
            "p1_survivors" if player_name == "AI 1" else "p2_survivors"
        ]
        fitness += survivors * 100

    defeated = 6 - (
        battle_log["p2_survivors" if player_name == "AI 1" else "p1_survivors"]
    )
    fitness += defeated * 50
    fitness -= battle_log["turns"] * 10

    return fitness


def crossover(parent1, parent2):
    child_knowledge = {}
    all_keys = set(parent1.knowledge.keys()) | set(parent2.knowledge.keys())
    for key in all_keys:
        if random.random() < 0.5:
            child_knowledge[key] = parent1.knowledge.get(key)
        else:
            child_knowledge[key] = parent2.knowledge.get(key)

    child = AIBrain()
    child.knowledge = child_knowledge
    return child


def mutate(brain, all_moves):
    if random.random() < 0.1:  # 10% mutation chance
        if brain.knowledge:
            key_to_mutate = random.choice(list(brain.knowledge.keys()))
            brain.knowledge[key_to_mutate] = random.choice(all_moves)
    return brain


def run_training_session(generations, population_size):
    print("Initializing AI populations for training...")

    team_file_path = os.path.join(script_dir, "ai_opponent_team.json")
    all_moves = list(ALL_MOVES.keys())

    population1 = [AIPlayer("AI 1", team_file_path) for _ in range(population_size)]
    population2 = [AIPlayer("AI 2", team_file_path) for _ in range(population_size)]

    total_battles = generations * population_size * 2
    battles_completed = 0

    print_progress_bar(0, total_battles, prefix="Training Progress:", suffix="Complete")

    for gen in range(generations):
        # --- Train Population 1 vs Population 2 ---
        for ai_p1 in population1:
            ai_p2 = random.choice(population2)

            p1 = Player("AI 1", [Knight(kd) for kd in json.load(open(team_file_path))])
            p1.ai_logic = ai_p1
            p2 = Player("AI 2", [Knight(kd) for kd in json.load(open(team_file_path))])
            p2.ai_logic = ai_p2

            battle = HeadlessBattle(p1, p2)
            log = battle.run_simulation()
            ai_p1.brain.fitness = calculate_fitness(log, "AI 1")
            battles_completed += 1
            print_progress_bar(
                battles_completed,
                total_battles,
                prefix="Training Progress:",
                suffix="Complete",
            )

        # --- Train Population 2 vs Population 1 ---
        for ai_p2 in population2:
            ai_p1 = random.choice(population1)

            p1 = Player("AI 1", [Knight(kd) for kd in json.load(open(team_file_path))])
            p1.ai_logic = ai_p1
            p2 = Player("AI 2", [Knight(kd) for kd in json.load(open(team_file_path))])
            p2.ai_logic = ai_p2

            battle = HeadlessBattle(p1, p2)
            log = battle.run_simulation()
            ai_p2.brain.fitness = calculate_fitness(log, "AI 2")
            battles_completed += 1
            print_progress_bar(
                battles_completed,
                total_battles,
                prefix="Training Progress:",
                suffix="Complete",
            )

        # Evolve Population 1
        population1.sort(key=lambda p: p.brain.fitness, reverse=True)
        new_pop1 = population1[:2]
        while len(new_pop1) < population_size:
            parent1, parent2 = random.choices(population1[:5], k=2)
            child_brain = crossover(parent1.brain, parent2.brain)
            child_brain = mutate(child_brain, all_moves)

            new_ai_player = AIPlayer("AI 1", team_file_path)
            new_ai_player.brain = child_brain
            new_pop1.append(new_ai_player)
        population1 = new_pop1

        # Evolve Population 2
        population2.sort(key=lambda p: p.brain.fitness, reverse=True)
        new_pop2 = population2[:2]
        while len(new_pop2) < population_size:
            parent1, parent2 = random.choices(population2[:5], k=2)
            child_brain = crossover(parent1.brain, parent2.brain)
            child_brain = mutate(child_brain, all_moves)

            new_ai_player = AIPlayer("AI 2", team_file_path)
            new_ai_player.brain = child_brain
            new_pop2.append(new_ai_player)
        population2 = new_pop2

    print("\n")

    # --- Final Selection ---
    best_ai_player1 = population1[0]
    best_ai_player2 = population2[0]

    if best_ai_player1.brain.fitness > best_ai_player2.brain.fitness:
        champion_brain = best_ai_player1.brain
        print(
            f"Champion AI is from Population 1 with Fitness: {champion_brain.fitness}"
        )
    else:
        champion_brain = best_ai_player2.brain
        print(
            f"Champion AI is from Population 2 with Fitness: {champion_brain.fitness}"
        )

    champion_brain.brain_file = os.path.join(script_dir, "ai_brain.json")
    champion_brain.save_knowledge()
    print(f"Saved champion brain to ai_brain.json")


if __name__ == "__main__":
    run_training_session(GENERATIONS, POPULATION_SIZE)
