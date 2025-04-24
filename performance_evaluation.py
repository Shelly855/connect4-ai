"""
performance_evaluation.py - Simulates AI matchups and collects performance metrics for Connect 4 agents.

This script runs automated matchups between different AI agent types (Random, Smart, Minimax, Basic ML,
and Minimax-Trained ML) using the Connect4 class. It records key performance metrics across multiple games, including:
- Win/loss/draw outcomes
- Average move time per agent
- Memory usage
- Minimax-specific stats (nodes expanded, depth reached, heuristic delta, branching factor)

The results from each matchup are saved to `game_results.csv`, which was used for visualisation in Jupyter Notebook.

Run this script with `python performance_evaluation.py` to regenerate 'game_results.csv'.
"""

from game import Connect4
import joblib
import csv
import time
import psutil  # for evaluating memory usage


# Load ML models
basic_ml_model = joblib.load("ml_agent.pkl")
minimax_ml_model = joblib.load("ml_agent_minimax.pkl")


def simulate_match(
    agent1_type, agent2_type, agent1_model=None, agent2_model=None, games=500
):
    all_game_data = []

    # Simulate multiple games between the two agents
    for _ in range(games):
        game = Connect4(agent1_type, agent2_type, agent1_model, agent2_model)

        # Track turn order and outcome
        current_symbol = game.PLAYER_1
        turns = 0
        winner = "draw"
        win_type = None

        # Timing and move count metrics
        total_time_agent1 = 0
        total_time_agent2 = 0
        move_count_agent1 = 0
        move_count_agent2 = 0

        while True:
            if current_symbol == game.PLAYER_1:
                agent_type = agent1_type
                model = agent1_model
            else:
                agent_type = agent2_type
                model = agent2_model

            # Reset metrics for minimax-specific tracking
            if agent_type == "minimax":
                game.nodes_expanded = 0
                game.search_depth_used = 0
                game.branching_factors = []
                game.heuristic_deltas = []

            # Time the agent's move
            start_time = time.perf_counter()

            if agent_type == "random":
                move = game.random_agent()
            elif agent_type == "smart":
                move = game.smart_agent()
            elif agent_type == "minimax":
                move = game.minimax_agent_move(current_symbol)
            elif agent_type in ("ml", "minimax_ml"):
                move = game.ml_agent_predict(model)
            else:
                raise ValueError("Agent type must be AI.")

            end_time = time.perf_counter()
            move_duration = end_time - start_time

            if current_symbol == game.PLAYER_1:
                total_time_agent1 += move_duration
                move_count_agent1 += 1
            else:
                total_time_agent2 += move_duration
                move_count_agent2 += 1

            if move is None or not game.drop_disc(move, current_symbol):
                break

            turns += 1

            win_type = game.check_winner(current_symbol)
            if win_type:
                winner = "agent1" if current_symbol == game.PLAYER_1 else "agent2"
                break

            if game.is_full():
                winner = "draw"
                break

            current_symbol = (
                game.PLAYER_2 if current_symbol == game.PLAYER_1 else game.PLAYER_1
            )

        # Post-game metrics
        # After game ends - calculate metrics
        avg_time_agent1 = (
            total_time_agent1 / move_count_agent1 if move_count_agent1 > 0 else 0
        )
        avg_time_agent2 = (
            total_time_agent2 / move_count_agent2 if move_count_agent2 > 0 else 0
        )

        # Track memory usage
        process = psutil.Process()
        memory_usage_mb = process.memory_info().rss / 1024**2  # convert to MB

        # Calculate average branching factor
        avg_branching = (
            sum(game.branching_factors) / len(game.branching_factors)
            if game.branching_factors
            else 0
        )

        avg_heuristic_delta = (
            sum(game.heuristic_deltas) / len(game.heuristic_deltas)
            if game.heuristic_deltas
            else 0
        )

        # Save game data
        all_game_data.append(
            {
                "matchup": f"{agent1_type}_vs_{agent2_type}",
                "winner": winner,
                "moves": turns,
                "minimax_nodes": (
                    game.nodes_expanded
                    if "minimax" in [agent1_type, agent2_type]
                    else ""
                ),
                "minimax_depth": (
                    game.search_depth_used
                    if "minimax" in [agent1_type, agent2_type]
                    else ""
                ),
                "avg_time_agent1": round(avg_time_agent1, 5),
                "avg_time_agent2": round(avg_time_agent2, 5),
                "win_type": win_type if winner != "draw" else "draw",
                "memory_mb": round(memory_usage_mb, 2),
                "avg_branching_factor": (
                    round(avg_branching, 2)
                    if "minimax" in [agent1_type, agent2_type]
                    else ""
                ),
                "avg_heuristic_delta": (
                    round(avg_heuristic_delta, 2)
                    if "minimax" in [agent1_type, agent2_type]
                    else ""
                ),
            }
        )

    return all_game_data


# Run matchups
results = []
results += simulate_match("random", "smart")
results += simulate_match("smart", "minimax")
results += simulate_match("minimax", "ml", agent2_model=basic_ml_model)

# Save to CSV
with open("game_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
