"""
game.py - Core Connect 4 logic, agents, and gameplay mechanics.

This module implements the Connect4 class, which handles board setup, move logic,
win/draw checking, and AI agent behaviour. It supports multiple agent types:
- Random
- Smart (1-ply rule-based)
- Minimax with alpha-beta pruning
- ML-based agents (trained on UCI data or minimax-generated decisions)

It also includes board evaluation functions and a minimax tree visualiser.
This logic is reused in both the GUI and performance evaluation scripts.
Running this file directly will launch the full graphical interface.
Run this script with `python game.py` to start the game.

General Reference:
- Keith Galli - Connect 4 AI (GitHub)
    https://github.com/KeithGalli/Connect4-Python/blob/master/connect4_with_ai.py
    Used as a reference for structuring minimax, alpha-beta pruning, and evaluation heuristics.
"""

import random
import math
import tkinter as tk
from config import ROW_COUNT, COLUMN_COUNT, SEARCH_DEPTH


class Connect4:
    PLAYER_1 = "●"
    PLAYER_2 = "○"

    # Create empty 6x7 board
    def __init__(
        self,
        agent1_type="human",
        agent2_type="ml",
        agent1_model=None,
        agent2_model=None,
    ):
        self.board = [[" " for _ in range(COLUMN_COUNT)] for _ in range(ROW_COUNT)]
        self.agent1_type = agent1_type
        self.agent2_type = agent2_type
        self.agent1_model = agent1_model  # model for Player 1 (if ML)
        self.agent2_model = agent2_model  # model for Player 2 (if ML)

        # Stats for minimax performance
        self.nodes_expanded = 0
        self.search_depth_used = 0
        self.branching_factors = []  # valid moves per turn
        self.heuristic_deltas = []  # score changes per move

    def drop_disc(self, column, player_symbol):
        """Places the player's disc in the chosen column if possible. Returns True if successful."""
        row = self.get_lowest_empty_row(column)
        if row is not None:
            self.board[row][column] = player_symbol
            return True
        return False

    def is_valid_move(self, column):
        """Returns True if the selected column has at least one empty slot."""
        return self.board[0][column] == " "

    def check_winner(self, player_symbol):
        """Checks the board for a winning condition (horizontal, vertical, or diagonal) for the given player."""
        # Check horizontal win -
        for row in range(ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):  # avoid out of bounds
                if all(self.board[row][col + i] == player_symbol for i in range(4)):
                    return "horizontal"

        # Check vertical win |
        for col in range(COLUMN_COUNT):
            for row in range(ROW_COUNT - 3):  # avoid out of bounds
                if all(self.board[row + i][col] == player_symbol for i in range(4)):
                    return "vertical"

        # Check diagonal win /
        for row in range(3, ROW_COUNT):  # start from row 3 to stay in bounds
            for col in range(COLUMN_COUNT - 3):
                # Bottom left -> top right
                if all(self.board[row - i][col + i] == player_symbol for i in range(4)):
                    return "diagonal"

        # Check diagonal win \
        for row in range(3, ROW_COUNT):
            for col in range(3, COLUMN_COUNT):
                # Bottom-right -> top-left
                if all(self.board[row - i][col - i] == player_symbol for i in range(4)):
                    return "diagonal"

        return None  # no winner

    def is_full(self):
        """Returns True if the board has no empty slots left (i.e., a draw)."""
        return all(self.board[0][col] != " " for col in range(COLUMN_COUNT))

    def evaluate_board(self, player_symbol):
        """Scores the board from the given player's perspective using heuristics. Higher is better for the player."""
        opponent_symbol = (
            self.PLAYER_1 if player_symbol == self.PLAYER_2 else self.PLAYER_2
        )
        score = 0

        # Horizontal patterns
        for row in range(ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):
                window = [self.board[row][col + i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Vertical patterns
        for col in range(COLUMN_COUNT):
            for row in range(ROW_COUNT - 3):
                window = [self.board[row + i][col] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Diagonal / patterns
        for row in range(3, ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):
                window = [self.board[row - i][col + i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Diagonal \ patterns
        for row in range(3, ROW_COUNT):
            for col in range(3, COLUMN_COUNT):
                window = [self.board[row - i][col - i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        return score

    # A window = sequence of 4 connected cells
    def assess_pattern(self, player_symbol, opponent_symbol, window):
        """Evaluates a group of four cells and assigns a score based on potential threats or advantages."""
        score = 0
        opponent_count = window.count(opponent_symbol)
        player_count = window.count(player_symbol)
        empty_count = window.count(" ")

        # Penalise strong opponent patterns
        if opponent_count == 4:  # opponent wins
            score -= 100000
        elif opponent_count == 3 and empty_count == 1:  # needs blocking
            score -= 100
        elif opponent_count == 2 and empty_count == 2:
            score -= 10

        # Reward strong player patterns
        if player_count == 4:
            score += 100000  # win
        elif player_count == 3 and empty_count == 1:
            score += 120  # strong setup
        elif player_count == 2 and empty_count == 2:
            score += 10

        # Higher = better for player. Lower = better for opponent
        # Will choose move that maximises this
        return score

    # Minimax with alpha-beta pruning
    # True = AI's turn, False = opponent's turn
    # Depth = how many moves ahead to evaluate
    # Alpha = best already explored option for maximising player (starts at -inf)
    # Beta = best already explored option for minimising player (starts at +inf)

    # Reference: Science Buddies - Minimax with Alpha-Beta Pruning
    # https://www.youtube.com/watch?v=rbmk1qtVEmg
    def minimax_agent(self, alpha, beta, maximising_player, depth, ai_symbol):
        """Recursive minimax algorithm with alpha-beta pruning to choose the best move for the AI."""
        # Track search stats
        self.search_depth_used = max(self.search_depth_used, depth)
        self.nodes_expanded += 1

        # Find all columns where move is possible (not full)
        valid_moves = [col for col in range(COLUMN_COUNT) if self.is_valid_move(col)]

        opponent_symbol = self.PLAYER_1 if ai_symbol == self.PLAYER_2 else self.PLAYER_2

        if self.check_winner(ai_symbol):
            return None, float("inf")  # player wins
        elif self.check_winner(opponent_symbol):
            return None, float("-inf")  # opponent wins

        # Track branching factor
        self.branching_factors.append(len(valid_moves))

        # Sort moves (centre first)
        priority_order = [3, 2, 4, 1, 5, 0, 6]
        valid_moves = sorted(valid_moves, key=lambda col: priority_order.index(col))

        # Stop search if depth limit reached or board is full
        if depth == 0 or self.is_full():
            return None, self.evaluate_board(ai_symbol)

        if maximising_player:
            best_score = float("-inf")
            best_move = None
            for col in valid_moves:
                row = self.get_lowest_empty_row(col)
                self.board[row][col] = ai_symbol
                _, score = self.minimax_agent(
                    alpha, beta, False, depth - 1, ai_symbol
                )  # simulate to see how opponent would respond
                self.board[row][col] = " "  # undo move

                if score > best_score:
                    best_score = score
                    best_move = col
                alpha = max(alpha, best_score)

                # Prune branch
                if alpha >= beta:
                    break

            return best_move, best_score
        else:
            best_score = float("inf")  # start high since opponent is minimising
            best_move = None

            # Try all valid opponent moves
            for col in valid_moves:
                row = self.get_lowest_empty_row(col)
                self.board[row][col] = opponent_symbol  # opponent makes move
                _, score = self.minimax_agent(alpha, beta, True, depth - 1, ai_symbol)
                self.board[row][col] = " "  # undo move

                # Opponent chooses move that lowest player's score the most
                if score < best_score:
                    best_score = score
                    best_move = col

                beta = min(beta, best_score)
                if alpha >= beta:
                    break

            return best_move, best_score

    def minimax_agent_move(self, ai_symbol):
        """Returns the best move for the AI using minimax, while logging heuristic delta for analysis."""
        best_move, _ = self.minimax_agent(
            -math.inf, math.inf, True, SEARCH_DEPTH, ai_symbol
        )

        if best_move is not None:
            score_before = self.evaluate_board(ai_symbol)

            row = self.get_lowest_empty_row(best_move)
            self.board[row][best_move] = ai_symbol

            # Evaluate board after simulating the move
            score_after = self.evaluate_board(ai_symbol)
            delta = score_after - score_before
            self.heuristic_deltas.append(delta)

            self.board[row][best_move] = " "  # undo move after evaluation

            return best_move
        return self.random_agent()

    def random_agent(self):
        """Returns a random valid column for the next move."""
        valid_moves = [col for col in range(COLUMN_COUNT) if self.is_valid_move(col)]

        if valid_moves:
            chosen_move = random.choice(valid_moves)
            return chosen_move
        return None

    # Check if player can win this turn
    def find_winning_move(self, player_symbol):
        for col in range(COLUMN_COUNT):
            if self.is_valid_move(col):
                row = self.get_lowest_empty_row(col)
                if row is not None:
                    self.board[row][col] = player_symbol  # place disc temporarily
                    if self.check_winner(player_symbol):
                        self.board[row][col] = " "  # undo move
                        return col  # winning column
                    self.board[row][col] = " "
        return None

    def smart_agent(self, ai_symbol):
        """Tries to win in one move or block the opponent if they can win next turn. Falls back to random otherwise."""
        opponent_symbol = self.PLAYER_1 if ai_symbol == self.PLAYER_2 else self.PLAYER_2

        # Try to win
        winning_move = self.find_winning_move(ai_symbol)
        if winning_move is not None:
            return winning_move

        # Try to block opponent
        blocking_move = self.find_winning_move(opponent_symbol)
        if blocking_move is not None:
            return blocking_move

        # Otherwise, pick random move
        return self.random_agent()

    def ml_agent_predict(self, model):
        """Uses a trained ML model to predict the best move. Defaults to a random move if the prediction is invalid."""
        flat_board = [self.convert_symbol(cell) for row in self.board for cell in row]

        # Predict best column using a trained ML model
        prediction = model.predict([flat_board])[0]

        # Ensure column index is an integer
        column = int(prediction)

        # Make sure the predicted move is valid
        if self.is_valid_move(column):
            return column
        else:
            return self.random_agent()  # if column is full

    def convert_symbol(self, symbol):
        """Converts board symbols to numerical values used by ML models."""
        return {self.PLAYER_1: 1, self.PLAYER_2: -1}.get(symbol, 0)

    def get_lowest_empty_row(self, column):
        """Finds the lowest available row in a column. Returns None if the column is full."""
        # Start from bottom row and move upward
        for row in range(ROW_COUNT - 1, -1, -1):
            if self.board[row][column] == " ":
                return row
        return None

    def _print_tree_recursive(
        self,
        board_state,
        depth,
        maximising_player,
        indent,
        alpha,
        beta,
        player_symbol,
        output_widget,
    ):
        """Recursively builds and displays the minimax decision tree in the given output widget."""
        indent_str = "|   " * indent
        valid_moves = [col for col in range(COLUMN_COUNT) if board_state[0][col] == " "]

        # Reached max depth or no valid moves
        if depth == 0 or not valid_moves:
            score = self.evaluate_board(player_symbol)
            output_widget.insert(tk.END, f"{indent_str}└── Score: {score}\n")
            return None, score

        # Initialise best score depending on turn type
        best_score = -math.inf if maximising_player else math.inf
        best_move = None

        pruned_after = 0

        for col in valid_moves:
            pruned_after += 1 # count this move
            # Select symbol for current turn
            current_symbol = (
                player_symbol
                if maximising_player
                else (
                    self.PLAYER_1 if player_symbol == self.PLAYER_2 else self.PLAYER_2
                )
            )

            # Simulate placing a piece in the column
            row = self._simulate_drop(board_state, col, current_symbol)
            if row is None:
                continue  # skip if column is full

            move_label = "Max" if maximising_player else "Min"
            output_widget.insert(
                tk.END,
                f"{indent_str}├── Column {col} ({move_label}, {current_symbol})\n",
            )

            # Switch player for next step
            next_symbol = (
                self.PLAYER_1 if current_symbol == self.PLAYER_2 else self.PLAYER_2
            )

            _, score = self._print_tree_recursive(
                board_state,
                depth - 1,
                not maximising_player,
                indent + 1,
                alpha,
                beta,
                next_symbol,
                output_widget,
            )
            board_state[row][col] = " "  # undo move after simulation

            # Update best score and pruning values
            if maximising_player:
                if score > best_score:
                    best_score = score
                    best_move = col
                alpha = max(alpha, best_score)
            else:
                if score < best_score:
                    best_score = score
                    best_move = col
                beta = min(beta, best_score)

            # Alpha-beta pruning
            if alpha >= beta:
                branch_word = "branch" if pruned_after == 1 else "branches"
                output_widget.insert(tk.END, f"{indent_str}│   └── Pruned (α ≥ β) after {pruned_after} {branch_word}\n")
                break

        # Only print final decision at root
        if indent == 0:
            output_widget.insert(
                tk.END,
                f"\nBest opening move: Column {best_move} with score {best_score}\n",
            )
        return best_move, best_score

    def _simulate_drop(self, board, column, symbol):
        """Simulates a disc drop without altering the actual game state. Returns the row if successful."""
        for row in range(ROW_COUNT - 1, -1, -1):
            if board[row][column] == " ":
                board[row][column] = symbol
                return row
        return None


# Start game
if __name__ == "__main__":
    import joblib
    from connect4_gui import StartScreen, Connect4GUI
    from config import (
        ROW_COUNT,
        COLUMN_COUNT,
        SEARCH_DEPTH,
    )

    # Map user-friendly names to internal agent types
    AGENT_MAP = {
        "Human": "human",
        "Random Agent": "random",
        "Smart Agent": "smart",
        "Minimax Agent": "minimax",
        "Basic ML Agent": "ml",
        "Minimax-Trained ML Agent": "minimax_ml",
    }

    # Load pre-trained ML models
    basic_ml_model = joblib.load(
        "ml_agent.pkl"  # trained on UCI Connect-4 dataset: https://archive.ics.uci.edu/dataset/26/connect+4
    )
    minimax_ml_model = joblib.load(
        "ml_agent_minimax.pkl"  # trained on minimax-generated data
    )

    def start_game(agent1_name, agent2_name, root):
        # Get agent types from UI selection
        agent1_type = AGENT_MAP.get(agent1_name, "human")
        agent2_type = AGENT_MAP.get(agent2_name, "human")

        # Select models if needed
        agent1_model = (
            basic_ml_model
            if agent1_type == "ml"
            else minimax_ml_model if agent1_type == "minimax_ml" else None
        )
        agent2_model = (
            basic_ml_model
            if agent2_type == "ml"
            else minimax_ml_model if agent2_type == "minimax_ml" else None
        )

        # Launch game GUI
        Connect4GUI(agent1_type, agent2_type, agent1_model, agent2_model, root)

    # Set up and start the GUI
    root = tk.Tk()
    root.title("Connect 4 Setup")
    StartScreen(root, lambda a1, a2: start_game(a1, a2, root))
    root.mainloop()
