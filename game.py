# === General References ===
# - Keith Galli’s Connect 4 AI (GitHub):
#   https://github.com/KeithGalli/Connect4-Python/blob/master/connect4_with_ai.py
#   Used as a reference for structuring minimax, alpha-beta pruning, and evaluation heuristics.

import random
import time
import math
from colorama import Fore, Style, init # For colours
init(autoreset=True) # Reset colour after each print

PLAYER_1_COLOUR = Fore.GREEN
PLAYER_2_COLOUR = Fore.BLUE
ERROR_COLOUR = Fore.RED
AI_COLOUR = Fore.YELLOW
COLUMN_COUNT = 7
ROW_COUNT = 6

class Connect4:
    
    # Constants: Fixed values that do not change during execution
    PLAYER_1 = "●" # Human
    PLAYER_2 = "○" # AI

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

    def display_board(self):
        print("\n  0  1  2  3  4  5  6")
        for row in self.board:
            print("-" * 22) # Print horizontal line
            print("| " + "| ".join(row) + "| ") # Print column lines
        print("-" * 22) # Print bottom horizontal line
        print("\n")

    def drop_disc(self, column, player_symbol):
        row = self.get_lowest_empty_row(column)
        if row is not None:
            self.board[row][column] = player_symbol
            return True
        return False

    # Check if column is full - returns Boolean
    def is_valid_move(self, column):
        return self.board[0][column] == " " # Checks top row (row index 0)
    
    def check_winner(self, player_symbol):

        # Check for horizontal win -
        for row in range(ROW_COUNT): # Iterate through all 6 rows
            for col in range(COLUMN_COUNT - 3): # Only check up to col index 3, otherwise it'll be out of bounds

                # Check if this position & the next 3 to the right match the player's symbol
                # - col + 0: 1st symbol in sequence, col + 1: 2nd symbol, & so on
                if all(self.board[row][col + i] == player_symbol for i in range(4)):
                    return True # Found 4 in a row - win
                
        # Check for vertical win |
        for col in range(COLUMN_COUNT):
            for row in range(ROW_COUNT - 3): # Only check up to row index 2
                if all (self.board[row + i][col] == player_symbol for i in range(4)):
                    return True
                
        # Check for diagonal win /
        for row in range(3, ROW_COUNT): # Check from rows 3-5 to ensure enough space above for win
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
        
        return False # No winner
    
    # Check if board is full = draw
    def is_full(self):
        return all(self.board[0][col] != " " for col in range(COLUMN_COUNT))
    
    # Evaluates board for player_symbol (AI or human)
    # Returns score showing how good the position is for the player
    def evaluate_board(self, player_symbol):
        opponent_symbol = self.PLAYER_1 if player_symbol == self.PLAYER_2 else self.PLAYER_2 # Check which symbol belongs to opponent
        score = 0 # Can increase or decrease

        # Extract every possible horizontal set of 4 pieces
        for row in range(ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):
                window = [self.board[row][col + i] for i in range(4)] # Get 4 in a row sequence
                score += self.assess_pattern(player_symbol, opponent_symbol, window) # Call assess_pattern to analyse how strong pattern is

        # Extract every possible vertical set of 4 pieces
        for col in range(COLUMN_COUNT):
            for row in range(ROW_COUNT - 3):
                window = [self.board[row + i][col] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Extract every possible diagonal / set of 4 pieces
        for row in range(3, ROW_COUNT):
            for col in range(COLUMN_COUNT - 3):
                window = [self.board[row - i][col + i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        # Extract every possible diagonal \ set of 4 pieces
        for row in range(3, ROW_COUNT):
            for col in range(3, COLUMN_COUNT):
                window = [self.board[row - i][col - i] for i in range(4)]
                score += self.assess_pattern(player_symbol, opponent_symbol, window)

        return score
    
    # window = list of 4 consecutive cells
    # Returns score showing how good or bad this sequence of 4 is
    def assess_pattern(self, player_symbol, opponent_symbol, window):
        score = 0
        opponent_count = window.count(opponent_symbol)
        player_count = window.count(player_symbol)
        empty_count = window.count(" ") # empty spaces in board

        # Penalises positions that are strong for opponent
        if opponent_count == 4: # Opponent wins - bad position
            score -= 100
        elif opponent_count == 3 and empty_count == 1: # Opponent nearly winning - needs blocking
            score -= 10
        elif opponent_count == 2 and empty_count == 2: # Opponent potentially winning
            score -= 1

        # Rewards positions that help player win
        if player_count == 4: # Player wins
            score += 100
        elif player_count == 3 and empty_count == 1: # Player nearly winning - good position
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 1

        # High score = strong position for player
        # Low/negative score = strong position for opponent
        # AI will choose move that maximises this
        return score
    
    # maximising_player - True if AI's turn, False if opponent's turn
    # Depth - controls how many moves ahead the AI looks
    # alpha = -∞ (worst possible start for maximising)
    # beta = ∞ (worst possible start for minimising)

    # === Reference for alpha beta pruning: Science Buddies YouTube tutorial on minimax with alpha-beta pruning ===
    #   https://www.youtube.com/watch?v=rbmk1qtVEmg
    def minimax_agent(self, alpha, beta, maximising_player, depth):

        valid_moves = [col for col in range(COLUMN_COUNT) if self.is_valid_move(col)] # Find all columns where move is possible (not full)

        # Move-ordering - sort moves (centre first)
        priority_order = [3, 2, 4, 1, 5, 0, 6] # 3 = index 0 (best)

        # Sort valid moves based on position in priority_order list
        # lambda col: priority_order.index(col) gives priority ranking for each column
        # sorted() rearranges valid_moves so centre columns come first
        valid_moves = sorted(valid_moves, key=lambda col: priority_order.index(col))

        # Stop search if AI searched deep enough or board full
        if depth == 0 or self.is_full():
            return None, self.evaluate_board(self.PLAYER_2) # None because it's an evaluation, not selecting a move
        
        if maximising_player:
            best_score = float('-inf') # Start off as negative infinity because AI wants highest possible score
            best_move = None
            for col in valid_moves:
                row = self.get_lowest_empty_row(col)
                self.board[row][col] = self.PLAYER_2 # AI makes move (place disc in lowest available row)
                _, score = self.minimax_agent(alpha, beta, False, depth - 1) # Simulate to see how opponent would respond
                self.board[row][col] = " " # Undo move so to not change the real

                # If this move gives higher score than best score
                if score > best_score:
                    best_score = score # Store new best score
                    best_move = col # Best column to play
                alpha = max(alpha, best_score)

                # Prune search if alpha value is greater than or equal to beta
                if alpha >= beta:
                    break

            return best_move, best_score
        
        else:
            best_score = float('inf') # Positive infinity because opponent tries to minimise AI's score
            best_move = None

            # Tries every possible move for opponent (PLAYER_1)
            for col in valid_moves:
                row = self.get_lowest_empty_row(col)
                self.board[row][col] = self.PLAYER_1 # Opponent makes move
                _, score = self.minimax_agent(alpha, beta, True, depth - 1) # Simulate AI's response
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
                    self.board[row][col] = player_symbol # Place disc temporarily
                    if self.check_winner(player_symbol):
                        self.board[row][col] = " " # Undo move
                        return col # Winning column
                    self.board[row][col] = " "
        return None # No winning move

    def smart_agent(self):

        # Check if AI can win this turn
        winning_move = self.find_winning_move(self.PLAYER_2)
        if winning_move is not None:
            return winning_move # Play winning move
        
        # Check if human is about to win and block them
        blocking_move = self.find_winning_move(self.PLAYER_1)
        if blocking_move is not None:
            return blocking_move # Block human from winning
        
        # Pick random move
        return self.random_agent()

    def ml_agent_predict(self, model):
        # Flatten board & convert symbols to numeric
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

    def get_human_move(self, player_symbol):
        while True: # Loop until valid

            # Makes sure user enters valid column number
            try:
                column = int(input(f"Player 1 ({self.PLAYER_1}), choose a column (0-6): "))

                # Check if input between 0 & 6
                if 0 <= column <= COLUMN_COUNT - 1:
                    if self.is_valid_move(column):
                        return column
                    else:
                        print(ERROR_COLOUR + "That column is full! Try again.\n")
                else:
                    print(ERROR_COLOUR + "Oops! Please enter a number between 0 and 6.\n")
            except ValueError:
                print(ERROR_COLOUR + "Oops! Please enter a number between 0 and 6.\n")
        
    # Main game loop
    def play(self):
        players = [self.PLAYER_1, self.PLAYER_2] # List stores player symbols
        turn = 0 # Track turn number (even = player 1, odd = player 2)

        # Run until win or board is full
        while True:
            self.announce_turn(turn)
            self.display_board() # Show state of board before each turn

            # Check for draw
            if self.is_full():
                self.display_board()
                print(AI_COLOUR + "\nIt's a draw!\n")
                return # End game

            current_player = self.PLAYER_1 if turn % 2 == 0 else self.PLAYER_2
            agent_type = self.agent1_type if turn % 2 == 0 else self.agent2_type
            
                # print(AI_COLOUR + f"AI ({self.PLAYER_2}) is thinking...\n")
                # time.sleep(1)
                
            # Decide move based on agent type
            if agent_type == "human":
                column = self.get_human_move(current_player)
            elif agent_type == "ml":
                model_to_use = self.agent1_model if turn % 2 == 0 else self.agent2_model
                column = self.ml_agent_predict(model_to_use)
            elif agent_type == "minimax":
                column = self.minimax_agent_move()
            elif agent_type == "random":
                column = self.random_agent()
            elif agent_type == "smart":
                column = self.smart_agent()
            elif agent_type == "minimax_ml":
                model_to_use = self.agent1_model if turn % 2 == 0 else self.agent2_model
                column = self.ml_agent_predict(model_to_use)
            else:
                raise ValueError("Unknown agent type")

            # column = self.minimax_agent_move()
            # column = self.ml_agent_predict()
            # column = self.random_agent()
            # column = self.smart_agent()

            if column is None:
                print(ERROR_COLOUR + "No valid moves! The game is likely a draw.")
                return # End game

            # Make a move
            if self.drop_disc(column, current_player): # If move is valid
                self.announce_move(turn, column) # Announce the move that was made

            if self.check_winner(current_player):
                self.display_board()
                print(PLAYER_1_COLOUR + f"\n{'Player 1' if turn % 2 == 0 else 'Player 2'} ({current_player}) wins!\n")
                break
            turn += 1 # Switch to next player's turn (even is player 1, odd is player 2)

    def get_lowest_empty_row(self, column):

        # range (start, stop, step):
        # - Start from bottom row (5)
        # - Run until row 0, stop before -1 (makes sure all 6 rows are checked (5-0))
        # - Moves backward (from bottom to top)
        for row in range(ROW_COUNT - 1, -1, -1):
            if self.board[row][column] == " ": # Check if slot is empty
                return row
        return None # Column is full
    
    # Print whose turn it is
    def announce_turn(self, turn):
        print("\n" + "=" * 40)
        if turn % 2 == 0:
            print((PLAYER_1_COLOUR + f"Player 1's turn ({self.PLAYER_1})").center(40))
        else:
            print((PLAYER_2_COLOUR + f"Player 2's turn ({self.PLAYER_2})").center(40))
        print("=" * 40 + "\n")

    # Print the move that was made
    def announce_move(self, turn, column):
        print("\n" + "-" * 40)
        if turn % 2 == 0:
            print((PLAYER_1_COLOUR + f"Player 1 ({self.PLAYER_1}) placed a disc in column {column}.").center(40))
            time.sleep(1)
        else:
            print((PLAYER_2_COLOUR + f"Player 2 ({self.PLAYER_2}) placed a disc in column {column}.").center(40))
            time.sleep(1)
        print("-" * 40 + "\n")

    def create_minimax_tree(self, player=2, depth=2):
        player_symbol = self.PLAYER_1 if player == 1 else self.PLAYER_2
        print(f"Creating minimax tree for Player {player} ({player_symbol})...")
        self._print_tree_recursive(self.board, depth, True, 0, -math.inf, math.inf, player_symbol)

    def _print_tree_recursive(self, board_state, depth, maximising_player, indent, alpha, beta, player_symbol):
        indent_str = "    " * indent
        valid_moves = [col for col in range(COLUMN_COUNT) if board_state[0][col] == " "]

        if depth == 0 or not valid_moves:
            score = self.evaluate_board(player_symbol)
            print(f"{indent_str}↳ Score: {score}")
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

            print(f"{indent_str}Column {col} ({'Maximising' if maximising_player else 'Minimising'}):")

            score = self._print_tree_recursive(board_state, depth - 1, not maximising_player, indent + 1, alpha, beta, player_symbol)
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
                print(f"{indent_str}⤷ Pruned further moves (alpha ≥ beta)")
                break

        if indent == 0:
            print(f"\nBest opening move: Column {best_move} with score {best_score}")
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

    # Load ML models
    basic_ml_model = joblib.load("ml_agent.pkl") # Uses dataset from https://archive.ics.uci.edu/dataset/26/connect+4
    minimax_ml_model = joblib.load("ml_agent_minimax.pkl") # Uses generated minimax dataset

    def prompt_agent(player_number):
        while True:
            print(f"\nChoose agent for Player {player_number}:")
            print("1 - Human")
            print("2 - Random Agent")
            print("3 - Smart Agent")
            print("4 - Minimax Agent")
            print("5 - Basic ML Agent")
            print("6 - Minimax-Trained ML Agent")
            choice = input("Enter choice (1-6): ")
            if choice in {"1", "2", "3", "4", "5", "6"}:
                return choice
            print(ERROR_COLOUR + "Oops! Please enter a number between 1 and 6.")

    agent1_choice = prompt_agent(1)
    agent2_choice = prompt_agent(2)

    def get_agent_type(choice):
        if choice == "1":
            return "human", None
        elif choice == "2":
            return "random", None
        elif choice == "3":
            return "smart", None
        elif choice == "4":
            return "minimax", None
        elif choice == "5":
            return "ml", basic_ml_model
        elif choice == "6":
            return "minimax_ml", minimax_ml_model
        else:
            print(ERROR_COLOUR + "Invalid choice. Defaulting to Human.")
            return "human", None
        
    agent1_type, agent1_model = get_agent_type(agent1_choice)
    agent2_type, agent2_model = get_agent_type(agent2_choice)

    game = Connect4(agent1_type=agent1_type, agent2_type=agent2_type,
                    agent1_model=agent1_model, agent2_model=agent2_model)

    # Generate game tree if one of the players is minimax
    if agent1_type == "minimax":
        print("\nGenerating game tree for Player 1 (Minimax)...")
        game.create_minimax_tree(player=1, depth=2)

    if agent2_type == "minimax":
        print("\nGenerating game tree for Player 2 (Minimax)...")
        game.create_minimax_tree(player=2, depth=2)

    game.play()


# TO DO:
# Minimax game tree appearance
# Improve appearance of agent type choices
# Consistent comment capitals
# More comments
# Game UI?
# Citations