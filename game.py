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
        print("  0  1  2  3  4  5  6")
        for row in self.board:
            print("-" * 22) # Print horizontal line
            print("| " + "| ".join(row) + "| ") # Print column lines
        print("-" * 22) # Print bottom horizontal line

    # Check if column is full - returns Boolean
    def is_valid_move(self, column):
        return self.board[0][column] == " " # Checks top row (row index 0)

    def drop_disc(self, column, player_symbol):
        if not self.is_valid_move(column):
            return False # Invalid move
        
        # range (start, stop, step):
        # - Start from bottom row (5)
        # - Run until row 0, stop before -1 (makes sure all 6 rows are checked (5-0))
        # - Moves backward (from bottom to top)
        for row in range(5, -1, -1):
            if self.board[row][column] == " ": # Check if slot is empty
                self.board[row][column] = player_symbol # Place disc in slot
                return True # Successful move
        return False
    
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

    def play(self):
        players = [self.PLAYER_1, self.PLAYER_2] # List stores player symbols
        turn = 0 # 0 for Player 1 (human), 1 for AI

        # Run until win or board is full
        while True:
            self.display_board() # Show state of board before each turn

            # turn % 2 == 0 is Player 1's turn
            # turn % 2 == 1 is Player 2's
            current_player = players[turn % 2]

            # Makes sure user enters valid column number
            try:
                column = int(input(f"Player {turn % 2 + 1} ({current_player}), choose a column (0-6): "))

                # Check if input between 0 & 6
                if column < 0 or column > 6:
                    print("Invalid column! Please enter a number between 0 and 6.")
                    continue # Skip this turn & ask again

            except ValueError:
                print("Invalid input! Please enter a number between 0 and 6.")
                continue # Skip this turn & ask again

            # Make a move
            if self.drop_disc(column, current_player): # If move is valid
                if self.check_winner(current_player):
                    self.display_board()
                    print(f"Player {turn % 2 + 1} ({current_player}) wins!")
                    break
            
                # Check for draw
                if self.is_full():
                    self.display_board()
                    print("A draw!")
                    break

                turn += 1 # Switch to next player's turn (even is player 1, odd is player 2)
            else:
                print("Invalid move! Try again.")

# Start game
if __name__ == "__main__":
    game = Connect4()
    game.play()

# TEST: different wins