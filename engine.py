import random
from action_space import action_map_19x19
from web_board import Board
from web_board import Player
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

import copy

from local_simulator import LocalSimulator
from local_simulator import LocalSimulatorWithGUI


#monte carlo tree search
class MCTS:

    def __init__(self):
        pass

    def run(self):
        board = Board()
        board_driver = board.get_driver()

        board.login()
        board.create_game()

        player_black = Player('black', board_driver)
        player_black.take_seat()
        
        parent = Node([], action_map_19x19.copy(), None, 0, 0, None)

        need_to_select_player = False

        player_has_passed = False

        while True:

            parent.create_children(parent.get_board_state(), parent.get_action_space(), parent)
            parent.simulate_children_and_update()

            if(need_to_select_player):
                player_black.select_player(player_has_passed)

            best_child = parent.get_best_child()

            next_move = parent.get_best_move(best_child)

            print("Best move: ", next_move)

            player_black.make_move(next_move)
            
            if(next_move == 362):
                break
            elif(next_move == 361):
                player_has_passed = True
        
            parent = best_child

            parent.get_action_space().pop(next_move)

            need_to_select_player = True

            #need to wait until player white makes move.
            time.sleep(10)

            # the move that player white makes is not available to player black.
            parent.get_action_space().pop(board.get_sgf_data()[-1])

        print("Game Over")

        
class Node:

    def __init__(self, board_state, action_space, parent, games_played, games_won, next_move):

        self.board_state = copy.copy(board_state)

        self.action_space = action_space

        self.parent = copy.copy(parent)

        self.games_played = games_played

        self.games_won = games_won

        self.next_move = next_move

        self.children = []

    def get_board_state(self):
            
        return self.board_state
    
    def get_action_space(self):

        return self.action_space

    def get_parent(self):
            
        return self.parent    

    def get_children(self):
    
        return self.children

    def get_games_played(self):

        return self.games_played
    
    def get_games_won(self):

        return self.games_won
    
    def get_next_move(self):
        
        return self.next_move
    
    def set_board_state(self, board_state):

        self.board_state = board_state
    
    def set_action_space(self, action_space):
            
        self.action_space = action_space

    def set_parent(self, parent):

        self.parent = parent        

    def set_child(self, child):

        self.children.append(child)

    def set_games_played(self, games_played):
            
        self.games_played = games_played
    
    def set_games_won(self, games_won):

        self.games_won = games_won
    
    def set_next_move(self, next_move):

        self.next_move = next_move

    def create_children(self, board_state, action_space, parent):

        for key, value in action_space.items():

            child = Node(board_state, action_space, parent, 0, 0, key)
            parent.set_child(child)
            child.set_parent(parent)


    def simulate_children_and_update(self):

        def simulate_child(child):
            
            child_board_state = child.get_board_state()
            child_board_state.append(child.get_next_move())

            child.set_board_state(child_board_state)

            print("Child board state: ", child.get_board_state())

            child_result = child.simulate(child_board_state.copy())
        
            if child_result == 'B':
                child.set_games_won(child.get_games_won() + 1)
            
            child.set_games_played(child.get_games_played() + 1)

       
        with ThreadPoolExecutor() as executor:
            executor.map(simulate_child, self.children)

        """
        for child in self.children:
            simulate_child(child)
        """
       
        print("Done simulating the next round of children")

    def simulate(self, prev_board_state):

        current_game_moves = []

        temp_action_space = action_map_19x19.copy()

        current_game_moves = prev_board_state

        total_moves = len(current_game_moves)

        game = LocalSimulator()

        index = 0

        while game.get_result() == None:

            random_action = random.choice(list(temp_action_space.keys()))

            #cannot pass during quantum stone placment phase
            while total_moves <= 2 and random_action == 361:
                random_action = random.choice(list(temp_action_space.keys()))

            if(random_action == 362):
                #the game result if one player resigns
                game.root.destroy()
                return 'B' if total_moves % 2 == 0 else 'W'

            game.play_move(random_action, index)
            
            # we dont want to remove the 'pass' action from the action space
            if not (random_action == 361):
                temp_action_space.pop(random_action)
            
            current_game_moves.append(random_action)

            total_moves += 1
            index +=1

            game.display_board()
        
        game_result = game.get_result()
        print("Game result when both players passed:", game_result)
        game.root.destroy()
        return game_result
       

    def get_best_child(self):

        max_ratio = 0
        best_child = None
        best_children = []

        for child in self.children:
            
            win_ratio = child.get_games_won() / child.get_games_played()

            if win_ratio > max_ratio:
                max_ratio = win_ratio
                best_child = child
                best_children = []
            elif win_ratio == max_ratio:
                best_children.append(child)
                
        #need to make sure we are not just selecting the first child if some ratios are same
        #exploration vs exploitation - use upper confidence bound instead
        return best_child if best_children == [] else random.choice(best_children)

    def get_best_move(self, child):

        return child.get_next_move()