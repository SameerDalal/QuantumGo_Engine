from engine import MCTS


class QuantumGame():
            
    def __init__(self):
        engine = MCTS()
        engine.run()

env = QuantumGame()
