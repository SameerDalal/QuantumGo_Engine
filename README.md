# Quantum Go Game Engine

## Get Started

Clone the repository here `https://github.com/SameerDalal/QuantumGo_Engine.git`

Choose a branch: `main` or `cuda`. See `Run the Program` to know which branch to use

## Prerequisites
Google Chrome

## Installed Dependencies

Install the following dependencies before running:

```bash
pip install selenium
pip install webdriver-manager
pip install requests
```

## Run the Program

`python main.py -l 3`

This command runs the engine with 3 simulation loops. Each possible action for each board state in the game is simulated 3 times. The higher the number, the better the move chosen by the game engine will be. 

For real time play with the engine you should not go over 7 loops as it takes around 1 minute for the engine to make each move. Instead, use the CUDA-Accelerated version in the `cuda` branch which speeds up simulation time by 5x

## Play

After starting the program, a new Chrome browser will open with the game.

1. **Initial Setup**:
   - The engine will start its first round of simulations and play a move.
   - Ensure the blue selection ring is around the QuantumBot, as it will play the first move.

2. **Your Turn**:
   - After the QuantumBot plays its move, click `Take seat` to take control and play your move.

3. **Subsequent Moves**:
   - After you play your move, make sure the blue selection ring is around your player.
   - The bot will automatically select itself to make its move once it has finished simulating the next round of nodes.


## How it works

The engine uses the Monte Carlo Tree Search (MCTS) method to determine the next best move given a board state. 

1. **Selection**: Starting from the root node (the current board state), the algorithm selects child nodes until it reaches a leaf node.

2. **Expansion**: If the leaf node's game is not over, the algorithm expands the tree by adding one or more child nodes.

3. **Simulation**: From the newly added node, the algorithm plays random moves until the game is over.

4. **Backpropagation**: The result of the simulation is sent to the root node. 

5. **Best Move Selection**: After a number of iterations, the algorithm selects the move that leads to the child node with the highest win rate. The best child node then becomes the root node and the process is repeated.


## Other features

If you would like to see some of the simulations made by the engine, there is a GUI feature available. To use it, modify the following code:

In `engine.py` change `game = LocalSimulator()` to `game = LocalSimulatorWithGUI()`

In `engine.py` uncomment the following lines:
```
game.display_board()
game.root.destroy()
```