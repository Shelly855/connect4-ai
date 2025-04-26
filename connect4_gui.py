"""
connect4_gui.py - Graphical interface for Connect 4 with agent integration.

This module provides the full Tkinter-based GUI for the Connect 4 game. It supports:
- Human vs Human, Human vs AI, and AI vs AI matches
- AI agent types: Random, Smart (1-ply), Minimax, Basic ML, and Minimax-Trained ML
- Visual representation of the board and moves
- Real-time game tree visualisation for Minimax agents
- Adjustable AI move speed via a slider
- Sidebar for status messages, reset options, and new game setup

Also includes the initial start screen UI for selecting agents and launching games.

Reference:
- Real Python - Python GUI Programming With Tkinter
    https://realpython.com/python-gui-tkinter/
    Used as a reference for building the GUI layout and event handling with Tkinter.
"""

import tkinter as tk
from config import (
    ROW_COUNT,
    COLUMN_COUNT,
    PLAYER_1_COLOUR,
    PLAYER_2_COLOUR,
    DRAW_COLOUR,
    SEARCH_DEPTH,
)
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
        "minimax_ml": "Minimax-Trained ML Agent",
    }

    def __init__(
        self, agent1_type, agent2_type, agent1_model=None, agent2_model=None, root=None
    ):
        """Initialises the game window, sets up the board, sidebar, and event handlers."""
        self.turn = 0

        self.agent1_type = agent1_type
        self.agent2_type = agent2_type
        self.agent1_model = agent1_model
        self.agent2_model = agent2_model

        # New window for GUI
        self.root = tk.Toplevel(root)
        self.root.title("Connect 4")
        self.parent_root = root
        self.root.minsize(1000, 700)

        # Exit cleanly when users close window using x button
        self.root.protocol("WM_DELETE_WINDOW", self.exit_game)

        self.game = Connect4(
            agent1_type=agent1_type,
            agent2_type=agent2_type,
            agent1_model=agent1_model,
            agent2_model=agent2_model,
        )

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=20, pady=20)

        # Left side: board
        # Canvas for drawing grid
        self.canvas = tk.Canvas(self.main_frame, width=700, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT)

        self.canvas.bind("<Button-1>", self.click_handler)
        self.draw_board()

        # Right side: Sidebar for status labels, turn label, minimax tree
        self.sidebar = tk.Frame(self.main_frame, width=320)
        self.sidebar.pack(side=tk.RIGHT, padx=20, fill=tk.Y)
        self.sidebar.pack_propagate(False)  # stop window resizing

        # Shows final outcome
        self.status_label = tk.Label(self.sidebar, text="", font=("Helvetica", 14))
        self.status_label.pack(pady=10)

        # Shows whose turn it is
        self.turn_label = tk.Label(self.sidebar, text="", font=("Helvetica", 12))
        self.turn_label.pack(pady=5)
        self.update_turn_label()

        # Only show AI speed slider if any agent is not human
        if self.agent1_type != "human" or self.agent2_type != "human":
            speed_frame = tk.LabelFrame(self.sidebar, text="AI Speed (ms):")
            speed_frame.pack(pady=10, fill=tk.X, padx=10)

            self.speed_slider = tk.Scale(
                speed_frame, from_=100, to=2000, resolution=100, orient=tk.HORIZONTAL
            )
            self.speed_slider.set(1000)  # default
            self.speed_slider.pack(padx=10)

        # Instructions for human player (only shows if one player is a human)
        if agent1_type == "human" or agent2_type == "human":
            self.instructions_label = tk.Label(
                self.sidebar,
                font=("Helvetica", 11),
                text="If you're a human player, click\nany column to drop your disc.",
            )
            self.instructions_label.pack(pady=10)

        button_frame = tk.Frame(self.sidebar)
        button_frame.pack(pady=10)

        # Clear board but agents stay the same
        self.reset_button = tk.Button(
            button_frame, text="Reset Game", command=self.reset_board
        )
        self.reset_button.pack(pady=5)

        # Return to agent options
        self.new_game_button = tk.Button(
            button_frame, text="New Game", command=self.return_to_start
        )
        self.new_game_button.pack(pady=5)

        self.exit_button = tk.Button(
            self.sidebar, text="Exit Game", command=self.exit_game
        )
        self.exit_button.pack(pady=5)

        if agent1_type == "minimax" or agent2_type == "minimax":
            self.expand_button = tk.Button(
                self.sidebar,
                text="View Minimax Tree",
                command=self.open_tree_in_new_window,
            )
            self.expand_button.pack(pady=(10, 0))

        # If Player 1 is AI, autostart after main game screen appears
        first_agent = agent1_type
        if first_agent != "human":
            delay = self.speed_slider.get() if hasattr(self, "speed_slider") else 1000
            self.root.after(delay, self.play_turn)

    def draw_board(self):
        """Draws the Connect 4 board grid and empty disc slots on the canvas."""
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
                    x0 + 10,
                    y0 + 10,  # inset top left by 10px
                    x1 - 10,
                    y1 - 10,  # inset bottom right
                    fill="white",
                    tags=f"cell_{row}_{col}",  # so can update later
                )

    def update_disc(self, row, col, symbol):
        """Fills the disc slot at (row, col) with the correct colour based on the player's symbol."""
        colour = PLAYER_1_COLOUR if symbol == self.game.PLAYER_1 else PLAYER_2_COLOUR
        self.canvas.itemconfig(f"cell_{row}_{col}", fill=colour)

    def click_handler(self, event):
        """Called when a human clicks the board. Passes the selected column to play_turn()."""
        agent_type = (
            self.game.agent1_type if self.turn % 2 == 0 else self.game.agent2_type
        )
        if agent_type != "human":
            return
    
        col = event.x // 100
        self.play_turn(col)

    def show_game_over_message(self, text, colour):
        self.game_over_label = tk.Label(self.canvas, text=text, font=("Helvetica", 32, "bold"), fg=colour, bg="white")
        self.game_over_label.place(relx=0.5, rely=0.5, anchor="center")

    def play_turn(self, col=None):
        """Handles a single turn: gets move, updates the board, and checks for win/draw."""
        current_player = (
            self.game.PLAYER_1 if self.turn % 2 == 0 else self.game.PLAYER_2
        )
        agent_type = (
            self.game.agent1_type if self.turn % 2 == 0 else self.game.agent2_type
        )
        model = self.game.agent1_model if self.turn % 2 == 0 else self.game.agent2_model

        # If AI's turn & no column manually selected
        if agent_type != "human" and col is None:
            if agent_type == "random":
                col = self.game.random_agent()
            elif agent_type == "smart":
                col = self.game.smart_agent(current_player)
            elif agent_type == "minimax":
                col = self.game.minimax_agent_move(current_player)
            elif agent_type in ("ml", "minimax_ml"):
                col = self.game.ml_agent_predict(model)
            else:
                return

        # Invalid or missing column input
        if col is None or not self.game.is_valid_move(col):
            return

        # Execute valid move
        row = self.game.get_lowest_empty_row(col)
        self.game.drop_disc(col, current_player)
        self.update_disc(row, col, current_player)

        if self.game.check_winner(current_player):
            self.canvas.unbind("<Button-1>")
            player_number = "1" if current_player == self.game.PLAYER_1 else "2"
            agent_type = (
                self.game.agent1_type if player_number == "1" else self.game.agent2_type
            )
            colour = PLAYER_1_COLOUR if player_number == "1" else PLAYER_2_COLOUR

            # For formatting agent names
            agent_display = self.AGENT_DISPLAY_NAMES.get(agent_type, agent_type)

            self.status_label.config(
                text=f"Player {player_number}\n({agent_display}) wins!", fg=colour
            ) 
            self.turn_label.config(text="")  # clear turn label
            self.show_game_over_message(f"Player {player_number} Wins!", colour)
            self.root.after(300, self.show_game_stats)
            return

        # Check for draw
        if self.game.is_full():
            self.status_label.config(text="It's a draw!", fg=DRAW_COLOUR)
            self.turn_label.config(text="")
            self.show_game_over_message("It's a Draw!", DRAW_COLOUR)
            self.root.after(300, self.show_game_stats)
            return

        # Next player's turn
        self.turn += 1
        self.update_turn_label()

        # If next player is AI, play their turn after a delay
        next_agent = (
            self.game.agent1_type if self.turn % 2 == 0 else self.game.agent2_type
        )
        if next_agent != "human":
            delay = self.speed_slider.get() if hasattr(self, "speed_slider") else 1000
            self.root.after(delay, self.play_turn)

    def update_turn_label(self):
        """Updates the sidebar label to show whose turn it is."""
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
            text=f"{current_player} ({agent_display})'s turn", fg=colour
        )

    def reset_board(self):
        """Resets the game board and turn counter, keeping the same agents."""
        self.turn = 0
        self.game = Connect4(
            agent1_type=self.agent1_type,
            agent2_type=self.agent2_type,
            agent1_model=self.agent1_model,
            agent2_model=self.agent2_model,
        )

        if hasattr(self, "game_over_label"):
            self.game_over_label.destroy()
            del self.game_over_label

        # Clear outcome and turn messages
        self.status_label.config(text="")
        self.turn_label.config(text="")

        if hasattr(self, "instructions_label"):
            self.instructions_label.config(
                text="If you're a human player, click\n any column to drop your disc."
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

    def return_to_start(self):
        """Closes the game window and returns to the agent selection screen."""
        self.root.destroy()
        self.parent_root.deiconify()

    def exit_game(self):
        """Closes both the game window and the initial setup window."""
        self.root.destroy()
        if self.parent_root:
            self.parent_root.destroy()

    def refresh_minimax_tree(self):
        """Refreshes the minimax tree display (if applicable) based on the current board state."""
        if hasattr(self, "tree_output"):
            self.tree_output.delete("1.0", tk.END)

            # Generate + display their game tree
            if self.agent1_type == "minimax":
                self.tree_output.insert(tk.END, "\n=== Player 1 Minimax Tree ===\n\n")
                best_move, _ = self.game._print_tree_recursive(
                    self.game.board,  # board_state
                    SEARCH_DEPTH,
                    True,  # maximising_player
                    0,  # indent
                    -math.inf,
                    math.inf,
                    self.game.PLAYER_1,  # player_symbol
                    self.tree_output,
                )

            if self.agent2_type == "minimax":
                self.tree_output.insert(tk.END, "\n=== Player 2 Minimax Tree ===\n\n")
                best_move, _ = self.game._print_tree_recursive(
                    self.game.board,
                    SEARCH_DEPTH,
                    True,
                    0,
                    -math.inf,
                    math.inf,
                    self.game.PLAYER_2,
                    self.tree_output,
                )

    def open_tree_in_new_window(self):
        """Opens a new window to display the full minimax decision tree for one or both players."""
        new_win = tk.Toplevel(self.root)
        new_win.title("Full Minimax Tree")

        # Build the text area with a scrollbar
        text_frame = tk.Frame(new_win)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(
            text_frame, font=("Courier", 10), wrap=tk.NONE, yscrollcommand=scrollbar.set
        )
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        # Updates text box with the latest minimax tree(s)
        def refresh_tree_contents():
            text_widget.delete("1.0", tk.END)
            text_widget.insert(
                tk.END,
                f"Turn {self.turn + 1} — Current Player: {'Player 1' if self.turn % 2 == 0 else 'Player 2'}\n\n",
            )

            if self.agent1_type == "minimax":
                text_widget.insert(tk.END, "=== Player 1 Minimax Tree ===\n\n")
                self.game._print_tree_recursive(
                    self.game.board,
                    SEARCH_DEPTH,
                    True,
                    0,
                    -math.inf,
                    math.inf,
                    self.game.PLAYER_1,
                    text_widget,
                )

            if self.agent2_type == "minimax":
                text_widget.insert(tk.END, "\n=== Player 2 Minimax Tree ===\n\n")
                self.game._print_tree_recursive(
                    self.game.board,
                    SEARCH_DEPTH,
                    True,
                    0,
                    -math.inf,
                    math.inf,
                    self.game.PLAYER_2,
                    text_widget,
                )

        # Scrolls straight to the selected player's tree
        def jump_to_player(player_num):
            tag = f"=== Player {player_num} Minimax Tree ==="
            index = text_widget.search(tag, "1.0", tk.END)
            if index:
                text_widget.see(index)
                text_widget.mark_set("insert", index)
                text_widget.focus()

        # Buttons for refresh and jump
        button_frame = tk.Frame(new_win)
        button_frame.pack(pady=5)

        tk.Button(
            button_frame, text="Refresh Tree", command=refresh_tree_contents
        ).pack(side=tk.LEFT, padx=5)

        if self.agent1_type == "minimax":
            tk.Button(
                button_frame, text="Jump to Player 1", command=lambda: jump_to_player(1)
            ).pack(side=tk.LEFT, padx=5)
        if self.agent2_type == "minimax":
            tk.Button(
                button_frame, text="Jump to Player 2", command=lambda: jump_to_player(2)
            ).pack(side=tk.LEFT, padx=5)

        # Show tree right away when the window opens
        refresh_tree_contents()

    def show_game_stats(self):
        """Displays game statistics in a popup window after match ends."""
        moves_played = self.turn + 1

        stats_lines = [f"Moves played: {moves_played}"]

        if self.agent1_type == "minimax" or self.agent2_type == "minimax":
            stats_lines.append(f"Total nodes expanded: {self.game.nodes_expanded}")
            stats_lines.append(f"Maximum search depth reached: {self.game.search_depth_used}")

            if self.game.branching_factors:
                avg_branching = sum(self.game.branching_factors) / len(self.game.branching_factors)
                stats_lines.append(f"Average branching factor: {avg_branching:.2f}")

            if self.game.heuristic_deltas:
                avg_heuristic = sum(self.game.heuristic_deltas) / len(self.game.heuristic_deltas)
                stats_lines.append(f"Average heuristic delta: {avg_heuristic:.2f}")

        stats_window = tk.Toplevel(self.root)
        stats_window.title("Game Stats")
        stats_window.geometry("320x300")
        stats_window.resizable(False, False)

        title_label = tk.Label(stats_window, text="Game Statistics", font=("Helvetica", 16, "bold"), fg="darkblue")
        title_label.pack(pady=(15, 10))

        stats_frame = tk.Frame(stats_window)
        stats_frame.pack(padx=20, pady=10)

        for line in stats_lines:
            stat_label = tk.Label(stats_frame, text=line, font=("Helvetica", 12), anchor="w", justify="left")
            stat_label.pack(anchor="w")

        close_button = tk.Button(stats_window, text="Close", command=stats_window.destroy)
        close_button.pack(pady=15)


AGENT_OPTIONS = [
    "Human",
    "Random Agent",
    "Smart Agent",
    "Minimax Agent",
    "Basic ML Agent",
    "Minimax-Trained ML Agent",
]


class StartScreen:
    def __init__(self, root, start_callback):
        """Sets up the initial agent selection screen and game launch button."""
        self.root = root
        self.root.minsize(width=300, height=300)
        self.start_callback = start_callback

        self.frame = tk.Frame(root)
        self.frame.pack(pady=50)

        tk.Label(self.frame, text="Connect 4", font=("Helvetica", 24)).pack(pady=10)

        # Dropdown selections for each player's agent type
        self.agent1_var = tk.StringVar(value=AGENT_OPTIONS[0])
        self.agent2_var = tk.StringVar(value=AGENT_OPTIONS[0])

        agent_frame = tk.LabelFrame(
            self.frame, text="Choose Agents", labelanchor="n", padx=10, pady=10
        )
        agent_frame.pack(pady=(10, 0))

        tk.Label(agent_frame, text="Player 1 Agent:").pack(anchor="w")
        agent1_menu = tk.OptionMenu(agent_frame, self.agent1_var, *AGENT_OPTIONS)
        agent1_menu.config(width=24)
        agent1_menu.pack()

        tk.Label(agent_frame, text="Player 2 Agent:").pack(anchor="w", pady=(5, 0))
        agent2_menu = tk.OptionMenu(agent_frame, self.agent2_var, *AGENT_OPTIONS)
        agent2_menu.config(width=24)
        agent2_menu.pack()

        # Start button that launches game with selected agents
        tk.Button(self.frame, text="Start Game", command=self.start_game).pack(pady=20)

    def start_game(self):
        """Reads the selected agent types and launches the game GUI."""
        agent1 = self.agent1_var.get()
        agent2 = self.agent2_var.get()
        self.root.withdraw()
        self.start_callback(agent1, agent2)
