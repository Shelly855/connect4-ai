import tkinter as tk
from config import ROW_COUNT, COLUMN_COUNT, PLAYER_1_COLOUR, PLAYER_2_COLOUR, DRAW_COLOUR
from game import Connect4
import math


class Connect4GUI:

    # Formatting agent types for labels
    AGENT_DISPLAY_NAMES = {
        "human": "Human",
        "random": "Random Agent",
        "smart": "Smart Agent",
        "minimax": "Minimax Agent",
        "ml": "ML Agent",
        "minimax_ml": "Minimax-Trained ML Agent"
    }

    def __init__(self, agent1_type, agent2_type, agent1_model=None, agent2_model=None, root=None):
        self.turn = 0

        self.agent1_type = agent1_type
        self.agent2_type = agent2_type
        self.agent1_model = agent1_model
        self.agent2_model = agent2_model

        # New window for GUI
        self.root = tk.Toplevel(root)
        self.root.title("Connect 4")
        self.parent_root = root

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
        self.sidebar = tk.Frame(self.main_frame, width=300) # fixed width (number can be adjusted)
        self.sidebar.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        self.sidebar.pack_propagate(False) # stop window resizing

        # Shows final outcome
        self.status_label = tk.Label(self.sidebar, text="", font=("Helvetica", 14))
        self.status_label.pack(pady=10)

        # Shows whose turn it is
        self.turn_label = tk.Label(self.sidebar, text="", font=("Helvetica", 12))
        self.turn_label.pack(pady=5)
        self.update_turn_label()

        # Speed slider
        speed_frame = tk.LabelFrame(self.sidebar, text="AI Speed (ms):")
        speed_frame.pack(pady=10, fill=tk.X, padx=10)

        self.speed_slider = tk.Scale(
            speed_frame,
            from_=100,
            to=2000,
            resolution=100,
            orient=tk.HORIZONTAL
        )
        self.speed_slider.set(1000) # default
        self.speed_slider.pack(padx=10)

        button_frame = tk.Frame(self.sidebar)
        button_frame.pack(pady=10)

        # Clears board but agents stay the same
        self.reset_button = tk.Button(
            button_frame,
            text="Reset Game",
            command=self.reset_board
        )
        self.reset_button.pack(pady=5)

        # Returns to agent options
        self.new_game_button = tk.Button(
            button_frame,
            text="New Game",
            command=self.return_to_start
        )
        self.new_game_button.pack(pady=5)

        # Instructions for human player (only shows if one player is a human)
        if agent1_type == "human" or agent2_type == "human":
            self.instructions_label = tk.Label(
                self.sidebar,
                font=("Helvetica", 11),
                text="If you're a human player, click\nany column to drop your disc."
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

            self.refresh_minimax_tree()

        # If Player 1 is AI, autostart after main game screen appears
        first_agent = agent1_type
        if first_agent != "human":
            delay = self.speed_slider.get() if hasattr(self, "speed_slider") else 1000
            self.root.after(delay, self.play_turn)

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
                    tags=f"cell_{row}_{col}" # so can update later
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

        # If AI's turn & no column manually selected
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
                return

        # Invalid or missing column input
        if col is None or not self.game.is_valid_move(col):
            return
        
        row = self.game.get_lowest_empty_row(col)
        self.game.drop_disc(col, current_player)
        self.update_disc(row, col, current_player)

        if self.game.check_winner(current_player):
            self.canvas.unbind("<Button-1>")
            player_number = "1" if current_player == self.game.PLAYER_1 else "2"
            agent_type = self.game.agent1_type if player_number == "1" else self.game.agent2_type
            colour = PLAYER_1_COLOUR if player_number == "1" else PLAYER_2_COLOUR

            # For formatting agent names
            agent_display = self.AGENT_DISPLAY_NAMES.get(agent_type, agent_type)

            self.status_label.config(text=f"Player {player_number}\n({agent_display}) wins!", fg=colour)
            self.turn_label.config(text="") # clear turn label
            return

        if self.game.is_full():
            self.status_label.config(text="It's a draw!", fg=DRAW_COLOUR)
            self.turn_label.config(text="")
            return

        # Next player's turn
        self.turn += 1
        self.update_turn_label()

        # If next player is AI, play their turn after a delay
        next_agent = self.game.agent1_type if self.turn % 2 == 0 else self.game.agent2_type
        if next_agent != "human":
            delay = self.speed_slider.get() if hasattr(self, "speed_slider") else 1000
            self.root.after(delay, self.play_turn)


    def update_turn_label(self):
        if self.turn % 2 == 0:
            current_player = "Player 1"
            agent_type = self.game.agent1_type
            colour = PLAYER_1_COLOUR
        else:
            current_player = "Player 2"
            agent_type = self.game.agent2_type
            colour = PLAYER_2_COLOUR

        # For formatting agent name
        agent_display = self.AGENT_DISPLAY_NAMES.get(agent_type, agent_type)

        self.turn_label.config(
            text=f"{current_player} ({agent_display})'s turn",
            fg=colour
        )

    def reset_board(self):
        self.turn = 0
        self.game = Connect4(
            agent1_type=self.agent1_type,
            agent2_type=self.agent2_type,
            agent1_model=self.agent1_model,
            agent2_model=self.agent2_model
        )

        # Clear outcome and turn messages
        self.status_label.config(text="")
        self.turn_label.config(text="")
        
        if hasattr(self, "instructions_label"):
                self.instructions_label.config(
                    text="If you're a human player, click any column to drop your disc."
                )
                self.instructions_label.pack()

        # Clear and redraw board
        self.canvas.delete("all")
        self.draw_board()
        self.canvas.bind("<Button-1>", self.click_handler)
        self.update_turn_label()
    
        self.refresh_minimax_tree()
        
        if self.agent1_type != "human":
            delay = self.speed_slider.get() if hasattr(self, "speed_slider") else 1000
            self.root.after(delay, self.play_turn)

    # Show agent options again
    def return_to_start(self):
        self.root.destroy()
        self.parent_root.deiconify()

    def refresh_minimax_tree(self):
        if hasattr(self, "tree_output"):
            self.tree_output.delete("1.0", tk.END)

            # Generate + display their game tree if player 1 = minimax
            if self.agent1_type == "minimax":
                self.tree_output.insert(tk.END, "\n=== Player 1 Minimax Tree ===\n\n")
                self.game._print_tree_recursive(
                    self.game.board, # board_state
                    2, True, 0, # depth, maximising_player, indent
                    -math.inf, math.inf,
                    self.game.PLAYER_1, # player_symbol
                    self.tree_output
                )

            if self.agent2_type == "minimax":
                self.tree_output.insert(tk.END, "\n=== Player 2 Minimax Tree ===\n\n")
                self.game._print_tree_recursive(
                    self.game.board, 2, True, 0,
                    -math.inf, math.inf,
                    self.game.PLAYER_2,
                    self.tree_output
                )

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

        agent_frame = tk.LabelFrame(self.frame, text="Choose Agents", labelanchor="n", padx=10, pady=10)
        agent_frame.pack(pady=(10, 0))

        tk.Label(agent_frame, text="Player 1 Agent:").pack(anchor="w")
        agent1_menu = tk.OptionMenu(agent_frame, self.agent1_var, *AGENT_OPTIONS)
        agent1_menu.config(width=24)
        agent1_menu.pack()

        tk.Label(agent_frame, text="Player 2 Agent:").pack(anchor="w", pady=(5, 0))
        agent2_menu = tk.OptionMenu(agent_frame, self.agent2_var, *AGENT_OPTIONS)
        agent2_menu.config(width=24)
        agent2_menu.pack()

        tk.Button(self.frame, text="Start Game", command=self.start_game).pack(pady=20)

    def start_game(self):
        agent1 = self.agent1_var.get()
        agent2 = self.agent2_var.get()
        self.root.withdraw()
        self.start_callback(agent1, agent2)

# python game.py