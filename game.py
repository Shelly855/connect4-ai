# === General References ===
# - Keith Galli’s Connect 4 AI (GitHub):
#   https://github.com/KeithGalli/Connect4-Python/blob/master/connect4_with_ai.py
#   Used as a reference for structuring minimax, alpha-beta pruning, and evaluation heuristics.

import random
import time
import math
from colorama import Fore, Style, init # For colours
init(autoreset=True) # Reset colour after each print
import joblib
model = joblib.load("ml_agent.pkl")
print("Example prediction:", model.predict([[0]*42]))

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
    def __init__(self):
        self.board = [[" " for _ in range(COLUMN_COUNT)] for _ in range(ROW_COUNT)]

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

# Uses dataset from https://archive.ics.uci.edu/dataset/26/connect+4
    def ml_agent_predict(self):
        # Flatten board & convert symbols to numeric
        flat_board = [self.convert_symbol(cell) for row in self.board for cell in row]

        # Predict best column using trained ML model
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

    # Main game loop
    def play(self):
        players = [self.PLAYER_1, self.PLAYER_2] # List stores player symbols
        turn = 0 # Track turn number (even = human, odd = AI)

        # Run until win or board is full
        while True:
            self.announce_turn(turn)
            self.display_board() # Show state of board before each turn

            # Check for draw
            if self.is_full():
                self.display_board()
                print(AI_COLOUR + "\nIt's a draw!\n")
                return # End game

            # turn % 2 == 0 is human's turn
            # turn % 2 == 1 is AI's
            current_player = players[turn % 2]

            if turn % 2 == 0: # Human's turn
                while True: # Loop until valid

                    # Makes sure user enters valid column number
                    try:
                        column = int(input(f"Player 1 ({self.PLAYER_1}), choose a column (0-6): "))

                        # Check if input between 0 & 6
                        if 0 <= column <= COLUMN_COUNT - 1:
                            if self.is_valid_move(column):
                                break
                            else:
                                print(ERROR_COLOUR + "That column is full! Try again.\n")
                        else:
                            print(ERROR_COLOUR + "Oops! Choose a number between 0 and 6.\n")

                    except ValueError:
                        print(ERROR_COLOUR + "Oops! Please enter a number between 0 and 6.\n")
            
            else: # AI's turn
                print(AI_COLOUR + f"AI ({self.PLAYER_2}) is thinking...\n")
                time.sleep(1)
                
                column = self.ml_agent_predict()
                # column = self.random_agent()
                # column = self.smart_agent()

                # If AI has no valid moves
                if column is None:
                    print(ERROR_COLOUR + "AI couldn't find a valid move! The game is likely a draw.")
                    return # End game

            # Make a move
            if self.drop_disc(column, current_player): # If move is valid
                self.announce_move(turn, column) # Announce the move that was made

                if self.check_winner(current_player):
                    self.display_board()
                    print(PLAYER_1_COLOUR + f"\n{'Player 1' if turn % 2 == 0 else 'AI'} ({current_player}) wins!\n")
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
            print((PLAYER_2_COLOUR + f"AI's turn ({self.PLAYER_2})").center(40))
        print("=" * 40 + "\n")

    # Print the move that was made
    def announce_move(self, turn, column):
        print("\n" + "-" * 40)
        if turn % 2 == 0:
            print((PLAYER_1_COLOUR + f"Player 1 ({self.PLAYER_1}) placed a disc in column {column}.").center(40))
        else:
            print((PLAYER_2_COLOUR + f"AI ({self.PLAYER_2}) placed a disc in column {column}.").center(40))
        print("-" * 40 + "\n")
    
# Start game
if __name__ == "__main__":
    game = Connect4()
    game.play()


# TEST: draw