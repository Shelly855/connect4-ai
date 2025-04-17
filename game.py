# === General References ===
# - Keith Galli’s Connect 4 AI (GitHub):
#   https://github.com/KeithGalli/Connect4-Python/blob/master/connect4_with_ai.py
#   Used as a reference for structuring minimax, alpha-beta pruning, and evaluation heuristics.

import random
import math
import tkinter as tk
from config import ROW_COUNT, COLUMN_COUNT, PLAYER_1_COLOUR, PLAYER_2_COLOUR

class Connect4:
    PLAYER_1 = "●"
    PLAYER_2 = "○"

    # Initialise a 6-row by 7-column empty board as a nested list:
    # - Inner loop (for _ in range(7)) creates a row of 7 spaces
    # - Outer loop (for _ in range(6)) repeats this process for 6 rows
    # 'self' = instance of the class, allowing access to its attributes & methods
    def __init__(self, agent1_type="human", agent2_type="ml", agent1_model=None, agent2_model=None):
        self.board = [[" " for _ in range(COLUMN_COUNT)] for _ in range(ROW_COUNT)]
        self.agent1_type = agent1_type
        self.agent2_type = agent2_type
        self.agent1_model = agent1_model # model used by Player 1 if agent1 is ML
        self.agent2_model = agent2_model # model used by Player 2 if agent2 is ML

    def drop_disc(self, column, player_symbol):
        row = self.get_lowest_empty_row(column)
        if row is not None:
            self.board[row][column] = player_symbol
            return True
        return False

    # Check if column is full - returns Boolean
    def is_valid_move(self, column):
        return self.board[0][column] == " " # checks top row (row index 0)
    
    def check_winner(self, player_symbol):

        # Check for horizontal win -
        for row in range(ROW_COUNT): # iterate through all 6 rows
            for col in range(COLUMN_COUNT - 3): # only check up to col index 3, otherwise it'll be out of bounds

                # Check if this position & the next 3 to the right match the player's symbol
                # - col + 0: 1st symbol in sequence, col + 1: 2nd symbol, & so on
                if all(self.board[row][col + i] == player_symbol for i in range(4)):
                    return True # found 4 in a row - win
                
        # Check for vertical win |
        for col in range(COLUMN_COUNT):
            for row in range(ROW_COUNT - 3): # only check up to row index 2
                if all (self.board[row + i][col] == player_symbol for i in range(4)):
                    return True
                
        # Check for diagonal win /
        for row in range(3, ROW_COUNT): # check from rows 3-5 to ensure enough space above for win
            for col in range(COLUMN_COUNT - 3):

                # Check if 4 pieces match diagonally (bottom-left -> top-right)
                # - row - i moves up (decrease row index)
                # - col + i moves right (increase column index)
                if all(self.board[row - i][col + i] == player_symbol for i in range(4)):
                    return True
                
        # Check for diagonal win \
        for row in range(3, ROW_COUNT):
            for col in range(3, COLUMN_COUNT):

                # Check if 4 pieces match diagonally (bottom-right -> top-left)
                # - row - i moves up
                # - col - i moves left
                if all(self.board[row - i][col - i] == player_symbol for i in range(4)):
                    return True
        
        return False # no winner
    
    # Check if draw
    def is_full(self):
        return all(self.board[0][col] != " " for col in range(COLUMN_COUNT))
    
    # Returns score showing how good the position is for the player
    def evaluate_board(self, player_symbol):
        opponent_symbol = self.PLAYER_1 if player_symbol == self.PLAYER_2 else self.PLAYER_2
        score = 0

        # Extract every possible horizontal set of 4 pieces
        for row in range(ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):
                window = [self.board[row][col + i] for i in range(4)] # get 4 in a row sequence
                score += self.assess_pattern(player_symbol, opponent_symbol, window) # call function to analyse how strong pattern is

        # Extract every possible vertical set
        for col in range(COLUMN_COUNT):
            for row in range(ROW_COUNT - 3):
                window = [self.board[row + i][col] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Extract every possible diagonal / set
        for row in range(3, ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):
                window = [self.board[row - i][col + i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Extract every possible diagonal \ set
        for row in range(3, ROW_COUNT):
            for col in range(3, COLUMN_COUNT):
                window = [self.board[row - i][col - i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        return score
    
    # window = list of 4 consecutive cells
    # Returns score showing how good/bad this sequence of 4 is
    def assess_pattern(self, player_symbol, opponent_symbol, window):
        score = 0
        opponent_count = window.count(opponent_symbol)
        player_count = window.count(player_symbol)
        empty_count = window.count(" ") # empty spaces in board

        # Penalises positions that are strong for opponent
        if opponent_count == 4: # opponent wins - bad position
            score -= 100
        elif opponent_count == 3 and empty_count == 1: # opponent nearly winning - needs blocking
            score -= 10
        elif opponent_count == 2 and empty_count == 2: # opponent potentially winning
            score -= 1

        # Rewards positions that help player win
        if player_count == 4: # player wins
            score += 100
        elif player_count == 3 and empty_count == 1: # player nearly winning - good position
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 1

        # High score = strong position for player
        # Low/negative score = strong position for opponent
        # Will choose move that maximises this
        return score
    
    # maximising_player - True if AI's turn, False if opponent's turn
    # Depth - controls how many moves ahead the AI looks
    # alpha = -∞ (worst possible start for maximising)
    # beta = ∞ (worst possible start for minimising)

    # === Reference for alpha beta pruning: Science Buddies YouTube tutorial on minimax with alpha-beta pruning ===
    #   https://www.youtube.com/watch?v=rbmk1qtVEmg
    def minimax_agent(self, alpha, beta, maximising_player, depth):

        valid_moves = [col for col in range(COLUMN_COUNT) if self.is_valid_move(col)] #fFind all columns where move is possible (not full)

        # Move-ordering - sort moves (centre first)
        priority_order = [3, 2, 4, 1, 5, 0, 6] # 3 = index 0 (best)

        # Sort valid moves based on position in priority_order list
        # lambda col: priority_order.index(col) gives priority ranking for each column
        # sorted() rearranges valid_moves so centre columns come first
        valid_moves = sorted(valid_moves, key=lambda col: priority_order.index(col))

        # Stop search if AI searched deep enough or board full
        if depth == 0 or self.is_full():
            return None, self.evaluate_board(self.PLAYER_2) # none because it's an evaluation, not selecting a move
        
        if maximising_player:
            best_score = float('-inf') # start off as negative infinity because AI wants highest possible score
            best_move = None
            for col in valid_moves:
                row = self.get_lowest_empty_row(col)
                self.board[row][col] = self.PLAYER_2 # AI makes move (place disc in lowest available row)
                _, score = self.minimax_agent(alpha, beta, False, depth - 1) # simulate to see how opponent would respond
                self.board[row][col] = " " # undo move so to not change the real

                # If this move gives higher score than best score
                if score > best_score:
                    best_score = score # store new best score
                    best_move = col # best column to play
                alpha = max(alpha, best_score)

                # Prune search if alpha value is greater than or equal to beta
                if alpha >= beta:
                    break

            return best_move, best_score
        
        else:
            best_score = float('inf') # positive infinity because opponent tries to minimise AI's score
            best_move = None

            # Tries every possible move for opponent (PLAYER_1)
            for col in valid_moves:
                row = self.get_lowest_empty_row(col)
                self.board[row][col] = self.PLAYER_1 # opponent makes move
                _, score = self.minimax_agent(alpha, beta, True, depth - 1) # simulate AI's response
                self.board[row][col] = " "

                # Opponent chooses move that lowest AI's score the most
                if score < best_score:
                    best_score = score
                    best_move = col

                beta = min(beta, best_score)
                if alpha >= beta:
                    break

            return best_move, best_score
        
    # AI chooses best move using minimax
    def minimax_agent_move(self):
        best_move, _ = self.minimax_agent(-math.inf, math.inf, True, 3)
        return best_move if best_move is not None else self.random_agent()
            
    # AI chooses random move
    def random_agent(self):
        valid_moves = [col for col in range(COLUMN_COUNT) if self.is_valid_move(col)]

        if valid_moves:
            chosen_move = random.choice(valid_moves)
            return chosen_move
        return None
    
    # For smart agent method
    def find_winning_move(self, player_symbol):
        for col in range(COLUMN_COUNT):
            if self.is_valid_move(col):
                row = self.get_lowest_empty_row(col)
                if row is not None:
                    self.board[row][col] = player_symbol # place disc temporarily
                    if self.check_winner(player_symbol):
                        self.board[row][col] = " " # Uudo move
                        return col # winning column
                    self.board[row][col] = " "
        return None # no winning move

    def smart_agent(self):

        # Check if AI can win this turn
        winning_move = self.find_winning_move(self.PLAYER_2)
        if winning_move is not None:
            return winning_move # play winning move
        
        # Check if opponent is about to win and block them
        blocking_move = self.find_winning_move(self.PLAYER_1)
        if blocking_move is not None:
            return blocking_move # block opponent from winning
        
        # Pick random move
        return self.random_agent()

    def ml_agent_predict(self, model):
        flat_board = [self.convert_symbol(cell) for row in self.board for cell in row]

        # Predict best column using trained ML model (can be original ML or minimax ML agent)
        prediction = model.predict([flat_board])[0]

        # Convert from str to int
        column = int(prediction)

        # Make sure the predicted move is valid
        if self.is_valid_move(column):
            return column
        else:
            return self.random_agent() # if column is full

    def convert_symbol(self, symbol):
        if symbol == self.PLAYER_1:
            return 1
        elif symbol == self.PLAYER_2:
            return -1
        else:
            return 0

    def get_lowest_empty_row(self, column):

        # range (start, stop, step):
        # - Start from bottom row (5)
        # - Run until row 0, stop before -1 (makes sure all 6 rows are checked (5-0))
        # - Moves backward (from bottom to top)
        for row in range(ROW_COUNT - 1, -1, -1):
            if self.board[row][column] == " ": # check if slot is empty
                return row
        return None # column is full

    def _print_tree_recursive(self, board_state, depth, maximising_player, indent, alpha, beta, player_symbol, output_widget):
        indent_str = "|   " * indent
        valid_moves = [col for col in range(COLUMN_COUNT) if board_state[0][col] == " "]

        if depth == 0 or not valid_moves:
            score = self.evaluate_board(player_symbol)
            output_widget.insert(tk.END, f"{indent_str}└── Score: {score}\n")
            return score

        best_score = -math.inf if maximising_player else math.inf
        best_move = None

        for col in valid_moves:
            current_symbol = player_symbol if maximising_player else (
            self.PLAYER_1 if player_symbol == self.PLAYER_2 else self.PLAYER_2
            )
            row = self._simulate_drop(board_state, col, current_symbol)
            if row is None:
                continue # skip full column

            move_label = "Max" if maximising_player else "Min"
            output_widget.insert(tk.END, f"{indent_str}├── Column {col} ({move_label}, {current_symbol})\n")

            score = self._print_tree_recursive(board_state, depth - 1, not maximising_player, indent + 1, alpha, beta, player_symbol, output_widget)
            board_state[row][col] = " " # undo move

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

            if alpha >= beta:
                output_widget.insert(tk.END, f"{indent_str}│   └── Pruned (α ≥ β)\n")
                break

        if indent == 0:
            output_widget.insert(tk.END, f"\nBest opening move: Column {best_move} with score {best_score}\n")
        return best_score

    def _simulate_drop(self, board, column, symbol):
        for row in range(ROW_COUNT - 1, -1, -1):
            if board[row][column] == " ":
                board[row][column] = symbol
                return row
        return None
    
# Start game
if __name__ == "__main__":
    import joblib
    from connect4_gui import StartScreen, Connect4GUI
    from config import *

    AGENT_MAP = {
        "Human": "human",
        "Random Agent": "random",
        "Smart Agent": "smart",
        "Minimax Agent": "minimax",
        "Basic ML Agent": "ml",
        "Minimax-Trained ML Agent": "minimax_ml"
    }

    # Load ML models
    basic_ml_model = joblib.load("ml_agent.pkl") # uses dataset from https://archive.ics.uci.edu/dataset/26/connect+4
    minimax_ml_model = joblib.load("ml_agent_minimax.pkl") # uses generated minimax dataset

    def start_game(agent1_name, agent2_name):
        agent1_type = AGENT_MAP.get(agent1_name, "human")
        agent2_type = AGENT_MAP.get(agent2_name, "human")

        agent1_model = (
            basic_ml_model if agent1_type == "ml"
            else minimax_ml_model if agent1_type == "minimax_ml"
            else None
        )

        agent2_model = (
            basic_ml_model if agent2_type == "ml"
            else minimax_ml_model if agent2_type == "minimax_ml"
            else None
        )

        Connect4GUI(agent1_type, agent2_type, agent1_model, agent2_model)

    root = tk.Tk()
    root.title("Connect 4 Setup")
    StartScreen(root, start_game)
    root.mainloop()


# TO DO:
# Consistent comment capitals
# More comments
# Add citations used