# Connect 4

This is the **final GUI version** of the Connect 4 game, with a visual interface built with `tkinter`.

### Supported Modes

- Human vs Human
- Human vs AI (Random, Smart, Minimax, Basic ML, Minimax-Trained ML)
- AI vs AI

You can adjust the AI speed during the game, and toggle visibility of the minimax game tree (if minimax agent is playing).

---

## Requirements

- Python 3.10 or later
- Recommended: VS Code with the Python extension
- `scikit-learn` (required for ML agents)

> Install with:
>
> ```bash
> pip install scikit-learn
> ```

## How to Run

1. Open a terminal in this project folder.
2. Run the script with:
   ```bash
   python game.py
   ```
3. Use the dropdowns to choose agents, adjust speed, and start the game.

---

## Files

- `game.py` – Core game and AI logic (also launches GUI)
- `connect4_gui.py` - Handles the GUI and game interactions
- `config.py` - Board dimensions, colours, and player tokens
- `ml_agent.pkl` – ML model trained using real game data (UCI dataset)
- `ml_agent_minimax.pkl` – ML model trained using data generated from the minimax algorithm
- `performance_evaluation.py` – Simulates games between agents and collects performance data across 500+ matches
- `game_results.csv` – Raw results from each simulated game (e.g. winner, execution time, nodes expanded, etc.)
  
---

## Notes

- You can reset or restart the game at any time via the sidebar.
- Speed slider affects how quickly AI agents make their moves.
- If a minimax agent is selected, the minimax game tree is automatically generated and viewable.

---

## References

- Keith Galli’s Connect 4 AI (GitHub)
  - https://github.com/KeithGalli/Connect4-Python/blob/master/connect4_with_ai.py
  - Used as a reference for structuring minimax, alpha-beta pruning, and evaluation heuristics
- Science Buddies – “Connect 4 AI Player using Minimax Algorithm with Alpha-Beta Pruning: Python Coding Tutorial” (YouTube):
  - https://www.youtube.com/watch?v=rbmk1qtVEmg
  - Used as a reference for alpha-beta pruning
- Connect 4 Dataset
  - https://archive.ics.uci.edu/dataset/26/connect+4
  - Used to train the basic ML agent
 
---

This folder also has a GitHub repository version, if you'd like to take a look:  
[github.com/Shelly855/connect-4-terminal](https://github.com/Shelly855/connect-4-terminal)
*This link is optional and not required for marking. The GitHub version may be updated after submission.*
