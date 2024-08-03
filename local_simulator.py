import tkinter as tk
from enum import Enum
from typing import List, Tuple, Optional
from action_space import action_map_19x19

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
                    for stone in group:
                        subgame.set(stone, Color.EMPTY)
                        captured_stones.append(stone)
                        if stone in self.quantum_stones:
                            #if quantum stone is captured, remove the same colored quantum stone from the other board
                            other_quantum_stone = next(element for element in self.quantum_stones if element != stone)
                            if(idx == 0): 
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
        for stone in group:
            for neighbor in subgame.neighbors(stone):
                if subgame.at(neighbor) == Color.EMPTY:
                    return True
        return False

    def deduce_captures(self, subgame: BadukBoard) -> List[Coordinate]:
        captures = []
        for x in range(subgame.width):
            for y in range(subgame.height):
                coord = Coordinate([x, y])
                stone = subgame.at(coord)
                if stone != Color.EMPTY:
                    group = self.get_group(subgame, coord)
                    if not self.group_has_liberties(subgame, group):
                        if not self.is_surrounded_by_same_color(subgame, coord):
                            captures.extend(group)
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
            fill_player = "black" if color == Color.BLACK else "white"
            fill_green = "green"
            canvas.create_arc(x0, y0, x1, y1, start=90, extent=180, fill=fill_player, tags="stones")
            canvas.create_arc(x0, y0, x1, y1, start=270, extent=180, fill=fill_green, tags="stones")
        else:
            fill = "black" if color == Color.BLACK else "white"
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

    def play_move(self, action, index):
        player = Color.BLACK if index % 2 == 0 else Color.WHITE
        
        action = 'pass' if action == 361 else Coordinate(action_map_19x19[action])
                                                         
        self.game.play_move(player, action)

        self.display_board()

    def get_result(self):
        return self.game.get_result()
    
    def display_board(self):
        self.gui.update_boards()
        self.root.update()

class LocalSimulator():
    def __init__(self):
        self.game = QuantumGo()

    def play_move(self, action, index):
        player = Color.BLACK if index % 2 == 0 else Color.WHITE
        
        action = 'pass' if action == 361 else Coordinate(action_map_19x19[action])
                                                         
        self.game.play_move(player, action)

    def get_result(self):
        return self.game.get_result()
    
    def display_board(self):
        pass
    