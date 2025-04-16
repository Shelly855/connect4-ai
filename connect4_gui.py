import tkinter as tk
from config import ROW_COUNT, COLUMN_COUNT, PLAYER_1_COLOUR, PLAYER_2_COLOUR, DRAW_COLOUR
from game import Connect4
import math

class Connect4GUI:
    def __init__(self, agent1_type, agent2_type, agent1_model=None, agent2_model=None):
        self.turn = 0

        # New window for GUI
        self.root = tk.Toplevel()
        self.root.title("Connect 4")

        self.game = Connect4(agent1_type=agent1_type, agent2_type=agent2_type,
                            agent1_model=agent1_model, agent2_model=agent2_model)

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=20, pady=20)

        # Left side: board
        # Canvas for drawing grid
        self.canvas = tk.Canvas(self.main_frame, width=700, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT)

        self.canvas.bind("<Button-1>", self.click_handler)
        self.draw_board()

        # Right side: Sidebar for status labels, turn label, minimax tree
        self.sidebar = tk.Frame(self.main_frame)
        self.sidebar.pack(side=tk.RIGHT, padx=20, fill=tk.Y)

        # Shows final outcome
        self.status_label = tk.Label(self.sidebar, text="", font=("Helvetica", 14))
        self.status_label.pack(pady=10)

        # Shows whose turn it is
        self.turn_label = tk.Label(self.sidebar, text="", font=("Helvetica", 12))
        self.turn_label.pack(pady=5)
        self.update_turn_label()

        # Instructions for human player (only shows if one player is a human)
        if agent1_type == "human" or agent2_type == "human":
            self.instructions_label = tk.Label(
                self.sidebar,
                font=("Helvetica", 11),
                text="If you're a human player, click any column to drop your disc."
            )
            self.instructions_label.pack(pady=10)

        # If a player is minimax, show minimax tree
        if agent1_type == "minimax" or agent2_type == "minimax":
            self.tree_visible = tk.BooleanVar(value=True)

            # Button to show or hide tree
            self.toggle_button = tk.Button(
                self.sidebar,
                text="Hide Minimax Tree",
                command=self.toggle_tree
            )
            self.toggle_button.pack(pady=(10, 0))

            # For tree label + text
            self.tree_container = tk.Frame(self.sidebar)
            self.tree_container.pack(pady=10)

            # Game tree title
            self.tree_label = tk.Label(self.tree_container, text="Minimax Game Tree", font=("Helvetica", 14, "bold"))
            self.tree_label.pack()

            # Holds text widget + scrollbar
            self.tree_frame = tk.Frame(self.tree_container)
            self.tree_frame.pack()

            scrollbar = tk.Scrollbar(self.tree_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Text widget
            self.tree_output = tk.Text(
                self.tree_frame,
                height=20,
                width=50,
                font=("Courier", 10),
                yscrollcommand=scrollbar.set
            )
            self.tree_output.pack(side=tk.LEFT)

            # Link scrollbar to text
            scrollbar.config(command=self.tree_output.yview)

            # Generate + display their game tree if player 1 = minimax
            if agent1_type == "minimax":
                self.tree_output.insert(tk.END, "\n=== Player 1 Minimax Tree ===\n\n")
                self.game._print_tree_recursive(
                    self.game.board, # board_state
                    2, True, 0, # depth, maximising_player, indent
                    -math.inf, math.inf,
                    self.game.PLAYER_1, # player_symbol
                    self.tree_output
                )

            if agent2_type == "minimax":
                self.tree_output.insert(tk.END, "\n=== Player 2 Minimax Tree ===\n\n")
                self.game._print_tree_recursive(
                    self.game.board, 2, True, 0,
                    -math.inf, math.inf,
                    self.game.PLAYER_2,
                    self.tree_output
                )

        # If Player 1 is AI, autostart after main game screen appears
        first_agent = agent1_type
        if first_agent != "human":
            self.root.after(500, self.play_turn) # wait 0.5s first

    def toggle_tree(self):
        if self.tree_visible.get():
            self.tree_container.pack_forget()
            self.toggle_button.config(text="Show Minimax Tree")
        else:
            self.tree_container.pack()
            self.toggle_button.config(text="Hide Minimax Tree")
        self.tree_visible.set(not self.tree_visible.get())

    def draw_board(self):
        for row in range(ROW_COUNT):
            for col in range(COLUMN_COUNT):
                # Top left corner of cell
                x0 = col * 100
                y0 = row * 100

                # Bottom right corner of cell
                x1 = x0 + 100
                y1 = y0 + 100

                # Cell background
                self.canvas.create_rectangle(x0, y0, x1, y1, fill="blue")

                # White circle for disc slots
                self.canvas.create_oval(
                    x0+10, y0+10, # inset top left by 10px
                    x1-10, y1-10, # inset bottom right
                    fill="white", 
                    tags=f"cell_{row}_{col}" # So can update later
                    )

    # Change colour at (row, col) to match player's move
    def update_disc(self, row, col, symbol):
        colour = PLAYER_1_COLOUR if symbol == self.game.PLAYER_1 else PLAYER_2_COLOUR
        self.canvas.itemconfig(f"cell_{row}_{col}", fill=colour)

    def click_handler(self, event):
        col = event.x // 100
        self.play_turn(col)

    def play_turn(self, col=None):
        current_player = self.game.PLAYER_1 if self.turn % 2 == 0 else self.game.PLAYER_2
        agent_type = self.game.agent1_type if self.turn % 2 == 0 else self.game.agent2_type
        model = self.game.agent1_model if self.turn % 2 == 0 else self.game.agent2_model

        # If it's an AI's turn & no column manually selected
        if agent_type != "human" and col is None:
            if agent_type == "random":
                col = self.game.random_agent()
            elif agent_type == "smart":
                col = self.game.smart_agent()
            elif agent_type == "minimax":
                col = self.game.minimax_agent_move()
            elif agent_type in ("ml", "minimax_ml"):
                col = self.game.ml_agent_predict(model)
            else:
                return  # unknown agent type

        # Invalid or missing column input
        if col is None or not self.game.is_valid_move(col):
            return

        # Drop disc & update board
        row = self.game.get_lowest_empty_row(col)
        self.game.drop_disc(col, current_player)
        self.update_disc(row, col, current_player)

        # Check for win or draw
        if self.game.check_winner(current_player):
            self.canvas.unbind("<Button-1>")
            player_number = "1" if current_player == self.game.PLAYER_1 else "2"
            colour = PLAYER_1_COLOUR if player_number == "1" else PLAYER_2_COLOUR
            self.status_label.config(text=f"Player {player_number} wins!", fg=colour)
            self.turn_label.config(text="") # clear turn label
            return

        if self.game.is_full():
            self.status_label.config(text="It's a draw!", fg=DRAW_COLOUR)
            self.turn_label.config(text="") # clear turn label
            return

        # Next player's turn
        self.turn += 1
        self.update_turn_label()

        # If next player is AI, play their turn after a delay
        next_agent = self.game.agent1_type if self.turn % 2 == 0 else self.game.agent2_type
        if next_agent != "human":
            self.root.after(500, self.play_turn)

    def update_turn_label(self):
        current_player = "Player 1" if self.turn % 2 == 0 else "Player 2"
        colour = PLAYER_1_COLOUR if self.turn % 2 == 0 else PLAYER_2_COLOUR
        self.turn_label.config(text=f"{current_player}'s turn", fg=colour)

AGENT_OPTIONS = [
    "Human",
    "Random Agent",
    "Smart Agent",
    "Minimax Agent",
    "Basic ML Agent",
    "Minimax-Trained ML Agent"
]

class StartScreen:
    def __init__(self, root, start_callback):
        self.root = root
        self.root.minsize(width=300, height=300)
        self.start_callback = start_callback

        self.frame = tk.Frame(root)
        self.frame.pack(pady=50)

        tk.Label(self.frame, text="Connect 4", font=("Helvetica", 24)).pack(pady=10)

        self.agent1_var = tk.StringVar(value=AGENT_OPTIONS[0])
        self.agent2_var = tk.StringVar(value=AGENT_OPTIONS[0])

        tk.Label(self.frame, text="Player 1 Agent:").pack()
        tk.OptionMenu(self.frame, self.agent1_var, *AGENT_OPTIONS).pack()

        tk.Label(self.frame, text="Player 2 Agent:").pack()
        tk.OptionMenu(self.frame, self.agent2_var, *AGENT_OPTIONS).pack()

        tk.Button(self.frame, text="Start Game", command=self.start_game).pack(pady=20)

    def start_game(self):
        agent1 = self.agent1_var.get()
        agent2 = self.agent2_var.get()
        self.root.withdraw()
        self.start_callback(agent1, agent2)

# TO DO
# Restart game after finish and anytime
# AI agents play slower?
# Show which type of agent?
# Make dropdown menu in startscreen clearer that it's dropdown


