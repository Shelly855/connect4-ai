class Connect4:
    PLAYER_1 = "●" # Human
    PLAYER_2 = "○" # AI

     # Initialise a 6x7 empty board
    def __init__(self):
        self.board = [[" " for _ in range(7)] for _ in range(6)]

    def display_board(self):
        print("  1  2  3  4  5  6  7")
        for row in self.board:
            print("-" * 22) # Print horizontal line
            print("| " + "| ".join(row) + "| ") # Print column lines
        print("-" * 22) # Print last horizontal line

    # Check if column is full - returns Boolean
    def is_valid_move(self, column):
        return self.board[0][column] == " " # Checks top row (row index 0)

    def drop_disc(self, column, player_symbol):
        if not self.is_valid_move(column):
            return False # Invalid move
        
        for row in range(5, -1, -1): # Start from bottom row
            if self.board[row][column] == " ": # Check if slot is empty
                self.board[row][column] = player_symbol # Place disc in slot
                return True # Successful move
        return False
    
    def check_winner(self, player_symbol):

        # Check for horizontal win
        for row in range(6): # Loop through each row
            for col in range(4): # Loop through each column up to index 3
                if all(self.board[row][col + i] == player_symbol for i in range(4)): # Checking for 4 consecutive symbols
                    return True

# Testing
game = Connect4()
game.display_board()