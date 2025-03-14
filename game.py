import random
import time
from colorama import Fore, Style, init # For colours
init(autoreset=True) # Reset colour after each print

PLAYER_1_COLOUR = Fore.GREEN
PLAYER_2_COLOUR = Fore.BLUE
ERROR_COLOUR = Fore.RED
AI_COLOUR = Fore.YELLOW

class Connect4:
    
    # Constants: Fixed values that do not change during execution
    PLAYER_1 = "●" # Human
    PLAYER_2 = "○" # AI

    # Initialise a 6-row by 7-column empty board as a nested list:
    # - Inner loop (for _ in range(7)) creates a row of 7 spaces
    # - Outer loop (for _ in range(6)) repeats this process for 6 rows
    # 'self' = instance of the class, allowing access to its attributes & methods
    def __init__(self):
        self.board = [[" " for _ in range(7)] for _ in range(6)]

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
        for row in range(6): # Iterate through all 6 rows

            # Only check up to column index 3 (last valid starting position)
            # Checking beyond column 3 would go out of bounds for this 7-column board
            for col in range(4):

                # Check if this position and the next 3 to the right match the player's symbol
                # - col + 0: 1st symbol in sequence
                # - col + 1: 2nd symbol
                # - col + 2: 3rd symbol
                # - col + 3: 4th symbol
                if all(self.board[row][col + i] == player_symbol for i in range(4)):
                    return True # Found 4 in a row - win
                
        # Check for vertical win |
        for col in range(7):
            for row in range(3): # Only check up to row index 2
                if all (self.board[row + i][col] == player_symbol for i in range(4)):
                    return True
                
        # Check for diagonal win /
        for row in range(3, 6): # Check from rows 3-5 to ensure enough space above for win
            for col in range(4):

                # Check if 4 pieces match diagonally (bottom-left -> top-right)
                # - row - i moves up (decrease row index)
                # - col + i moves right (increase column index)
                if all(self.board[row - i][col + i] == player_symbol for i in range(4)):
                    return True
                
        # Check for diagonal win \
        for row in range(3, 6):
            for col in range(3, 7):

                # Check if 4 pieces match diagonally (bottom-right -> top-left)
                # - row - i moves up
                # - col - i moves left
                if all(self.board[row - i][col - i] == player_symbol for i in range(4)):
                    return True
        
        return False # No winner
    
    # Check if board is full = draw
    def is_full(self):
        return all(self.board[0][col] != " " for col in range(7))
    
    def random_agent(self):
        valid_moves = [col for col in range(7) if self.is_valid_move(col)]

        if valid_moves:
            chosen_move = random.choice(valid_moves)
            return chosen_move
        return None
    
    # For smart agent method
    def find_winning_move(self, player_symbol):
        for col in range(7):
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
                        if 0 <= column <= 6:
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
                column = self.smart_agent()

                # If AI has no valid moves
                if column is None:
                    print(ERROR_COLOUR + "AI couldn't find a valid move! The game is likely a draw.")
                    return # End game

            # Make a move
            if self.drop_disc(column, current_player): # If move is valid
                self.announce_move(turn, column) # Announce the move that was made
                
                if turn % 2 == 1: # If AI moved
                    time.sleep(1.5) # Pause to let human see new board before continuing

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
        for row in range(5, -1, -1):
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