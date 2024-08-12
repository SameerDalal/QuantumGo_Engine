import tkinter as tk
from enum import Enum
from typing import List, Tuple, Optional
from action_space import action_map_19x19
from numba import cuda
import numpy as np


class Color(Enum):
    EMPTY = 0
    BLACK = 1
    WHITE = 2

class Coordinate:
    def __init__(self, coord: List[int]):
        self.x = int(coord[0]) -1
        self.y = int(coord[1]) -1

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"({self.x}, {self.y})"

class BadukBoard:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.board = [[Color.EMPTY for _ in range(width)] for _ in range(height)]

    def at(self, coord: Coordinate) -> Color:
        return self.board[coord.y][coord.x]

    def set(self, coord: Coordinate, color: Color):
        self.board[coord.y][coord.x] = color

    def is_in_bounds(self, coord: Coordinate) -> bool:
        return 0 <= coord.x < self.width and 0 <= coord.y < self.height

    def serialize(self) -> List[List[Color]]:
        return [[color for color in row] for row in self.board]

    def neighbors(self, coord: Coordinate) -> List[Coordinate]:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return [Coordinate([coord.x + dx + 1, coord.y + dy + 1]) for dx, dy in deltas if self.is_in_bounds(Coordinate([coord.x + dx + 1, coord.y + dy + 1]))]

class QuantumGo:
    def __init__(self, width: int = 19, height: int = 19, komi: float = 6.5):
        self.subgames = [BadukBoard(width, height), BadukBoard(width, height)]
        self.quantum_stones: List[Coordinate] = []
        self.komi = komi
        self.round = 0
        self.phase = "play"
        self.result = None
        self.current_player = Color.BLACK
        self.captures = {Color.BLACK: 0, Color.WHITE: 0}
        self.consecutive_passes = 0

        #change threads per block    
        self.threads_per_block = 128
        

    def play_move(self, player: Color, move: object):
        if self.phase == "gameover":
            raise ValueError("Game is already over.")
        
        if player != self.current_player:
            raise ValueError(f"It's {self.current_player.name}'s turn to play.")
        
        if isinstance(move, str):
            if move == "resign":
                self.phase = "gameover"
                self.result = "B+R" if player == Color.WHITE else "W+R"
                return
            elif move == "pass":
                self.consecutive_passes += 1
                if self.consecutive_passes == 2:
                    self.phase = "gameover"
                    score = sum(self.captures[Color.BLACK] for _ in self.subgames) - self.komi
                    if score < 0:
                        self.result = f"W+{-score}"
                    elif score > 0:
                        self.result = f"B+{score}"
                    else:
                        self.result = "Tie"
                    return
                else:
                    self.current_player = Color.WHITE if self.current_player == Color.BLACK else Color.BLACK
                    return
            else:
                raise ValueError("Invalid move type")
        
        self.consecutive_passes = 0

        if self.round < 2:
            self.quantum_stones.append(move)
            if self.round == 1:
                self.subgames[0].set(self.quantum_stones[0], Color.BLACK)
                self.subgames[0].set(self.quantum_stones[1], Color.WHITE)
                self.subgames[1].set(self.quantum_stones[1], Color.BLACK)
                self.subgames[1].set(self.quantum_stones[0], Color.WHITE)
        else:
            moves = [move, move]
            
            captures = []
            for i in range(2):
                subgame = self.subgames[i]
                self.play_subgame_move(subgame, player, moves[i])
                captures.append(self.deduce_captures(subgame))

        self.round += 1
        self.current_player = Color.WHITE if self.current_player == Color.BLACK else Color.BLACK

    def play_subgame_move(self, subgame: BadukBoard, player: Color, coord: Coordinate):
        if subgame.at(coord) != Color.EMPTY:
            raise ValueError("Cannot place a stone on an occupied intersection.")
        subgame.set(coord, player)
        self.remove_captures(subgame, player, coord)
    

    def remove_captures(self, subgame: BadukBoard, player: Color, coord: Coordinate, is_quantum: bool = False):
        opponent = Color.BLACK if player == Color.WHITE else Color.WHITE
        captured_stones = []
        idx = 0
        for neighbor in subgame.neighbors(coord):
            if subgame.at(neighbor) == opponent:
                group = self.get_group(subgame, neighbor)
                if not self.group_has_liberties(subgame, group):
                    self.captures[player] += len(group)
                    
                    host_board_array = np.array([[subgame.board[y][x].value for x in range(subgame.width)] for y in range(subgame.height)])
                    host_group_array = np.array([(stone.x, stone.y) for stone in group])
                    host_captures_array = np.zeros(len(host_group_array), dtype=np.int32)

                    blocks_per_grid = (len(host_group_array) + (self.threads_per_block - 1)) // self.threads_per_block

                    device_board_array = cuda.to_device(host_board_array)
                    device_group_array = cuda.to_device(host_group_array)
                    device_captures_array = cuda.to_device(host_captures_array)

                    remove_captures_kernel[blocks_per_grid, self.threads_per_block](
                        device_board_array, device_group_array, player.value, device_captures_array
                    )


                    host_board_array = device_board_array.copy_to_host()
                    host_group_array = device_group_array.copy_to_host()
                    host_captures_array = device_captures_array.copy_to_host()
                    

                    for i in range(len(host_group_array)):
                        if host_captures_array[i] == 1:
                            x, y = host_group_array[i]
                            subgame.set(Coordinate([x + 1, y + 1]), Color.EMPTY)
                            captured_stones.append(Coordinate([x + 1, y + 1]))

                            if captured_stones[-1] in self.quantum_stones:
                                #if quantum stone is captured, remove the same colored quantum stone from the other board
                                other_quantum_stone = next(element for element in self.quantum_stones if element != captured_stones[-1])
                                if idx == 0:
                                    self.subgames[0].set(other_quantum_stone, Color.EMPTY)
                                else:
                                    self.subgames[1].set(other_quantum_stone, Color.EMPTY)
            idx += 1    
        return captured_stones

    def is_surrounded_by_same_color(self, subgame: BadukBoard, coord: Coordinate) -> bool:
        color = subgame.at(coord)
        return all(subgame.at(neighbor) == color for neighbor in subgame.neighbors(coord))

    def get_group(self, subgame: BadukBoard, coord: Coordinate) -> List[Coordinate]:
        color = subgame.at(coord)
        stack = [coord]
        group = set()
        while stack:
            stone = stack.pop()
            if stone not in group:
                group.add(stone)
                for neighbor in subgame.neighbors(stone):
                    if subgame.at(neighbor) == color:
                        stack.append(neighbor)
        return list(group)

    def group_has_liberties(self, subgame: BadukBoard, group: List[Coordinate]) -> bool:
        host_board_array = np.array([[subgame.board[y][x].value for x in range(subgame.width)] for y in range(subgame.height)])
        host_group_array = np.array([(stone.x, stone.y) for stone in group], dtype=np.int32)
        host_result_array = np.array([False], dtype=np.bool_)
            
        blocks_per_grid = (len(host_group_array) + (self.threads_per_block - 1)) // self.threads_per_block

        device_board_array = cuda.to_device(host_board_array)
        device_group_array = cuda.to_device(host_group_array)
        device_result_array = cuda.to_device(host_result_array)
        
        group_has_liberties_kernel[blocks_per_grid, self.threads_per_block](device_board_array, device_group_array, device_result_array)
        
        host_result_array = device_result_array.copy_to_host()

        return host_result_array[0]

    def deduce_captures(self, subgame: BadukBoard) -> List[Coordinate]:

        width = subgame.width
        height = subgame.height
        host_board_array = np.array([[subgame.board[y][x].value for x in range(width)] for y in range(height)])
        host_captures_array = np.zeros(width * height, dtype=np.int32)
        
        #number of blocks needed to cover the entire board
        blocks_per_grid = (width * height + (self.threads_per_block - 1)) // self.threads_per_block

        device_board_array = cuda.to_device(host_board_array)
        device_captures_array = cuda.to_device(host_captures_array)
        
        deduce_captures_kernel[blocks_per_grid, self.threads_per_block](device_board_array, width, height, device_captures_array)
        
        host_captures_array = device_captures_array.copy_to_host()

        captures = []
        for idx in range(width * height):
            if host_captures_array[idx] == 1:
                x = idx % width
                y = idx // width
                captures.append(Coordinate([x + 1, y + 1]))
        
        return captures

    def get_board_state(self) -> Tuple[List[List[Color]], List[List[Color]]]:
        return self.subgames[0].serialize(), self.subgames[1].serialize()

    def get_result(self) -> Optional[str]:
        return self.result
    
class QuantumGoGUI:
    def __init__(self, master, game: QuantumGo):
        self.master = master
        self.game = game
        self.canvas_size = 500
        self.cell_size = self.canvas_size // 19

        self.canvas1 = tk.Canvas(master, width=self.canvas_size, height=self.canvas_size, bg="white")
        self.canvas2 = tk.Canvas(master, width=self.canvas_size, height=self.canvas_size, bg="white")
        self.canvas1.grid(row=0, column=0)
        self.canvas2.grid(row=0, column=1)

        self.draw_board(self.canvas1)
        self.draw_board(self.canvas2)
        self.update_boards()

    def draw_board(self, canvas):
        offset = self.cell_size // 2
        for i in range(19):
            canvas.create_line(offset + self.cell_size * i, offset, offset + self.cell_size * i, self.canvas_size - offset)
            canvas.create_line(offset, offset + self.cell_size * i, self.canvas_size - offset, offset + self.cell_size * i)

    def update_boards(self):
        board1, board2 = self.game.get_board_state()
        self.draw_stones(self.canvas1, board1)
        self.draw_stones(self.canvas2, board2)

    def draw_stones(self, canvas, board):
        canvas.delete("stones")
        for y in range(19):
            for x in range(19):
                color = board[y][x]
                if color != Color.EMPTY:
                    is_quantum = Coordinate([x, y]) in self.game.quantum_stones
                    self.draw_stone(canvas, x, y, color, is_quantum)


    def draw_stone(self, canvas, x, y, color, is_quantum=False):
        offset = self.cell_size // 2
        x0 = offset + x * self.cell_size - offset // 2
        y0 = offset + y * self.cell_size - offset // 2
        x1 = offset + x * self.cell_size + offset // 2
        y1 = offset + y * self.cell_size + offset // 2
        if is_quantum:
            fill_player = "black" if color == Color.BLACK else "grey"
            fill_green = "green"
            canvas.create_arc(x0, y0, x1, y1, start=90, extent=180, fill=fill_player, tags="stones")
            canvas.create_arc(x0, y0, x1, y1, start=270, extent=180, fill=fill_green, tags="stones")
        else:
            fill = "black" if color == Color.BLACK else "grey"
            canvas.create_oval(x0, y0, x1, y1, fill=fill, tags="stones")


    def on_click(self, event, board_index):
        x = event.x // self.cell_size +1
        y = event.y // self.cell_size +1
        move = Coordinate([x, y])
        player = self.game.current_player

        try:
            self.game.play_move(player, move)
            self.update_boards()
            result = self.game.get_result()
            if result:
                tk.messagebox.showinfo("Game Over", f"Result: {result}")
        except ValueError as e:
            tk.messagebox.showerror("Invalid Move", str(e))

class LocalSimulatorWithGUI():

    def __init__(self):
        self.root = tk.Tk()
        self.game = QuantumGo()
        self.gui = QuantumGoGUI(self.root, self.game)
        self.display_board()

    def play_moves(self, actions):
        index = 0
        for action in actions:
            
            player = Color.BLACK if index % 2 == 0 else Color.WHITE

            action = 'pass' if action == 361 else Coordinate(action_map_19x19[action])

            self.game.play_move(player, action)

            index +=1    

            self.display_board()

    def get_result(self):
        return self.game.get_result()
    
    def display_board(self):
        self.gui.update_boards()
        self.root.update()

class LocalSimulator():
    def __init__(self):
        self.game = QuantumGo()

    def play_moves(self, actions):

        for index, action in enumerate(actions):

            player = Color.BLACK if index % 2 == 0 else Color.WHITE

            action = 'pass' if action == 361 else Coordinate(action_map_19x19[action])

            self.game.play_move(player, action)        

    def get_result(self):
        return self.game.get_result()
    
    def display_board(self):
        pass

# need to modify blocks per grid and threads per block

@cuda.jit
def remove_captures_kernel(board, group, player, captures):
    idx = cuda.grid(1)
    if idx < len(group):
        x, y = group[idx]
        if board[y, x] != player:
            captures[idx] = 1
            board[y, x] = 0  

@cuda.jit
def group_has_liberties_kernel(board, group, result):
    idx = cuda.grid(1)
    if idx < len(group):
        x, y = group[idx]
        if y > 0 and board[y - 1, x] == Color.EMPTY.value:
            result[0] = True
        elif y < board.shape[0] - 1 and board[y + 1, x] == Color.EMPTY.value:
            result[0] = True
        elif x > 0 and board[y, x - 1] == Color.EMPTY.value:
            result[0] = True
        elif x < board.shape[1] - 1 and board[y, x + 1] == Color.EMPTY.value:
            result[0] = True

@cuda.jit
def deduce_captures_kernel(board, width, height, captures):
    idx = cuda.grid(1)
    if idx < width * height:
        x = idx % width
        y = idx // width
        stone = board[y, x]
        
        if stone != Color.EMPTY.value:
            has_liberty = False
            if y > 0 and board[y - 1, x] == Color.EMPTY.value:
                has_liberty = True
            elif y < height - 1 and board[y + 1, x] == Color.EMPTY.value:
                has_liberty = True
            elif x > 0 and board[y, x - 1] == Color.EMPTY.value:
                has_liberty = True
            elif x < width - 1 and board[y, x + 1] == Color.EMPTY.value:
                has_liberty = True

            if not has_liberty:
                captures[idx] = 1