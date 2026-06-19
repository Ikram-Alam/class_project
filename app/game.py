# from __future__ import annotations

# from collections import deque
# from dataclasses import dataclass, field
# import random

# Direction = str
# Position = tuple[int, int]

# DIRS: dict[Direction, tuple[int, int]] = {
#     "N": (0, -1),
#     "S": (0, 1),
#     "E": (1, 0),
#     "W": (-1, 0),
# }

# OPPOSITE: dict[Direction, Direction] = {"N": "S", "S": "N", "E": "W", "W": "E"}

# DIFFICULTIES = {
#     "easy": 2,
#     "medium": 4,
#     "hard": 6,
# }


# @dataclass
# class Maze:
#     width: int
#     height: int
#     walls: list[list[dict[str, bool]]]

#     @classmethod
#     def generate(cls, width: int, height: int, rng: random.Random) -> "Maze":
#         walls = [[{"N": True, "S": True, "E": True, "W": True} for _ in range(width)] for _ in range(height)]
#         visited = [[False for _ in range(width)] for _ in range(height)]
#         stack: list[Position] = [(0, 0)]
#         visited[0][0] = True

#         while stack:
#             x, y = stack[-1]
#             neighbors: list[tuple[Direction, int, int]] = []
#             for direction, (dx, dy) in DIRS.items():
#                 nx, ny = x + dx, y + dy
#                 if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
#                     neighbors.append((direction, nx, ny))

#             if not neighbors:
#                 stack.pop()
#                 continue

#             direction, nx, ny = rng.choice(neighbors)
#             walls[y][x][direction] = False
#             walls[ny][nx][OPPOSITE[direction]] = False
#             visited[ny][nx] = True
#             stack.append((nx, ny))

#         return cls(width=width, height=height, walls=walls)

#     def legal_moves(self, position: Position) -> list[tuple[Direction, Position]]:
#         x, y = position
#         options: list[tuple[Direction, Position]] = []
#         for direction, (dx, dy) in DIRS.items():
#             if not self.walls[y][x][direction]:
#                 nx, ny = x + dx, y + dy
#                 if 0 <= nx < self.width and 0 <= ny < self.height:
#                     options.append((direction, (nx, ny)))
#         return options

#     def shortest_distance(self, start: Position, goal: Position) -> int:
#         if start == goal:
#             return 0

#         queue = deque([(start, 0)])
#         visited = {start}
#         while queue:
#             (x, y), distance = queue.popleft()
#             for _, next_position in self.legal_moves((x, y)):
#                 if next_position in visited:
#                     continue
#                 if next_position == goal:
#                     return distance + 1
#                 visited.add(next_position)
#                 queue.append((next_position, distance + 1))

#         return self.width * self.height

#     def to_payload(self) -> dict:
#         return {
#             "width": self.width,
#             "height": self.height,
#             "cells": self.walls,
#         }


# @dataclass
# class AITraceItem:
#     direction: Direction
#     target: Position
#     score: float
#     nodes: int
#     pruned: int


# @dataclass
# class GameState:
#     maze: Maze
#     player: Position
#     enemy: Position
#     exit: Position
#     difficulty: str
#     turn: int = 0
#     status: str = "playing"
#     message: str = "Reach the exit before the enemy catches you."
#     ai_depth: int = 0
#     ai_trace: list[AITraceItem] = field(default_factory=list)
#     last_player_move: str = ""
#     last_enemy_move: str = ""

#     def to_payload(self) -> dict:
#         return {
#             "maze": self.maze.to_payload(),
#             "player": {"x": self.player[0], "y": self.player[1]},
#             "enemy": {"x": self.enemy[0], "y": self.enemy[1]},
#             "exit": {"x": self.exit[0], "y": self.exit[1]},
#             "turn": self.turn,
#             "status": self.status,
#             "difficulty": self.difficulty,
#             "message": self.message,
#             "ai": {
#                 "depth": self.ai_depth,
#                 "trace": [
#                     {
#                         "direction": item.direction,
#                         "target": {"x": item.target[0], "y": item.target[1]},
#                         "score": item.score,
#                         "nodes": item.nodes,
#                         "pruned": item.pruned,
#                     }
#                     for item in self.ai_trace
#                 ],
#             },
#             "lastPlayerMove": self.last_player_move,
#             "lastEnemyMove": self.last_enemy_move,
#         }


# @dataclass
# class GameSession:
#     width: int = 13
#     height: int = 13
#     seed: int | None = None
#     rng: random.Random = field(init=False)
#     state: GameState = field(init=False)

#     def __post_init__(self) -> None:
#         self.seed = self.seed if self.seed is not None else random.SystemRandom().randint(1, 1_000_000_000)
#         self.rng = random.Random(self.seed)
#         self.reset("medium")

#     def reset(self, difficulty: str = "medium") -> GameState:
#         if difficulty not in DIFFICULTIES:
#             difficulty = "medium"

#         self.seed = random.SystemRandom().randint(1, 1_000_000_000)
#         self.rng = random.Random(self.seed)
#         maze = Maze.generate(self.width, self.height, self.rng)
#         self.state = GameState(
#             maze=maze,
#             player=(0, 0),
#             enemy=(self.width - 1, 0),
#             exit=(self.width - 1, self.height - 1),
#             difficulty=difficulty,
#             ai_depth=DIFFICULTIES[difficulty],
#         )
#         self.state.message = f"New game started on {difficulty.title()} difficulty."
#         return self.state

#     def move_player(self, direction: Direction) -> GameState:
#         if self.state.status != "playing":
#             return self.state

#         self.state.turn += 1
#         self.state.last_player_move = direction
#         self.state.last_enemy_move = ""
#         self.state.ai_trace = []

#         if direction in DIRS:
#             moved = self._step(self.state.player, direction)
#             if moved is not None:
#                 self.state.player = moved
#                 self.state.message = f"You moved {self._direction_name(direction)}."
#             else:
#                 self.state.message = f"You tried to move {self._direction_name(direction)}, but a wall blocked the way."

#         if self.state.player == self.state.exit:
#             self.state.status = "won"
#             self.state.message = "You escaped the dungeon."
#             return self.state

#         if self.state.player == self.state.enemy:
#             self.state.status = "lost"
#             self.state.message = "The enemy caught you."
#             return self.state

#         enemy_move, trace = self._choose_enemy_move()
#         self.state.ai_trace = trace
#         if enemy_move is not None:
#             direction_name, next_enemy = enemy_move
#             self.state.enemy = next_enemy
#             self.state.last_enemy_move = direction_name
#             if trace:
#                 self.state.message = (
#                     f"Enemy chose {self._direction_name(direction_name)} with a minimax score of {trace[0].score:.1f}."
#                 )

#         if self.state.enemy == self.state.player:
#             self.state.status = "lost"
#             self.state.message = "The enemy caught you."

#         return self.state

#     def _step(self, position: Position, direction: Direction) -> Position | None:
#         x, y = position
#         if self.state.maze.walls[y][x][direction]:
#             return None
#         dx, dy = DIRS[direction]
#         return x + dx, y + dy

#     def _direction_name(self, direction: Direction) -> str:
#         return {"N": "North", "S": "South", "E": "East", "W": "West"}[direction]

#     def _evaluate(self, player: Position, enemy: Position) -> float:
#         if player == self.state.exit:
#             return 10_000.0
#         if player == enemy:
#             return -10_000.0

#         distance = self.state.maze.shortest_distance(enemy, player)
#         return float(distance * 10)

#     def _choose_enemy_move(self) -> tuple[tuple[Direction, Position] | None, list[AITraceItem]]:
#         moves = self.state.maze.legal_moves(self.state.enemy)
#         if not moves:
#             return None, []

#         depth = self.state.ai_depth
#         trace: list[AITraceItem] = []
#         best_move: tuple[Direction, Position] | None = None
#         best_score = float("inf")

#         for direction, target in moves:
#             search = self._make_search()
#             score = search(self.state.player, target, depth - 1, True, float("-inf"), float("inf"))
#             stats = getattr(search, "stats", {"nodes": 0, "pruned": 0})
#             trace.append(AITraceItem(direction=direction, target=target, score=score, nodes=stats["nodes"], pruned=stats["pruned"]))
#             if score < best_score:
#                 best_score = score
#                 best_move = (direction, target)

#         trace.sort(key=lambda item: item.score)
#         return best_move, trace

#     def _make_search(self):
#         maze = self.state.maze
#         goal = self.state.exit
#         stats = {"nodes": 0, "pruned": 0}

#         def search(player: Position, enemy: Position, depth: int, maximizing: bool, alpha: float, beta: float) -> float:
#             stats["nodes"] += 1
#             if depth <= 0 or player == goal or player == enemy:
#                 return self._evaluate(player, enemy)

#             if maximizing:
#                 best = float("-inf")
#                 for _, next_player in maze.legal_moves(player):
#                     score = search(next_player, enemy, depth - 1, False, alpha, beta)
#                     best = max(best, score)
#                     alpha = max(alpha, best)
#                     if alpha >= beta:
#                         stats["pruned"] += 1
#                         break
#                 return best if best != float("-inf") else self._evaluate(player, enemy)

#             best = float("inf")
#             for _, next_enemy in maze.legal_moves(enemy):
#                 score = search(player, next_enemy, depth - 1, True, alpha, beta)
#                 best = min(best, score)
#                 beta = min(beta, best)
#                 if alpha >= beta:
#                     stats["pruned"] += 1
#                     break
#             return best if best != float("inf") else self._evaluate(player, enemy)

#         search.stats = stats  # type: ignore[attr-defined]
#         return search


# def create_session(difficulty: str = "medium", width: int = 13, height: int = 13) -> GameSession:
#     session = GameSession(width=width, height=height)
#     session.reset(difficulty)
#     return session













from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import random

Direction = str
Position = tuple[int, int]

DIRS: dict[Direction, tuple[int, int]] = {
    "N": (0, -1),
    "S": (0, 1),
    "E": (1, 0),
    "W": (-1, 0),
}

OPPOSITE: dict[Direction, Direction] = {"N": "S", "S": "N", "E": "W", "W": "E"}

DIFFICULTIES = {
    "easy":   {"depth": 2, "player_bias": 3.0},
    "medium": {"depth": 4, "player_bias": 1.5},
    "hard":   {"depth": 6, "player_bias": 0.5},
}


@dataclass
class Maze:
    width: int
    height: int
    walls: list[list[dict[str, bool]]]

    @classmethod
    def generate(cls, width: int, height: int, rng: random.Random) -> "Maze":
        walls = [[{"N": True, "S": True, "E": True, "W": True} for _ in range(width)] for _ in range(height)]
        visited = [[False for _ in range(width)] for _ in range(height)]
        stack: list[Position] = [(0, 0)]
        visited[0][0] = True

        while stack:
            x, y = stack[-1]
            neighbors: list[tuple[Direction, int, int]] = []
            for direction, (dx, dy) in DIRS.items():
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                    neighbors.append((direction, nx, ny))

            if not neighbors:
                stack.pop()
                continue

            direction, nx, ny = rng.choice(neighbors)
            walls[y][x][direction] = False
            walls[ny][nx][OPPOSITE[direction]] = False
            visited[ny][nx] = True
            stack.append((nx, ny))

        return cls(width=width, height=height, walls=walls)

    def legal_moves(self, position: Position) -> list[tuple[Direction, Position]]:
        x, y = position
        options: list[tuple[Direction, Position]] = []
        for direction, (dx, dy) in DIRS.items():
            if not self.walls[y][x][direction]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    options.append((direction, (nx, ny)))
        return options

    def shortest_distance(self, start: Position, goal: Position) -> int:
        if start == goal:
            return 0

        queue = deque([(start, 0)])
        visited = {start}
        while queue:
            (x, y), distance = queue.popleft()
            for _, next_position in self.legal_moves((x, y)):
                if next_position in visited:
                    continue
                if next_position == goal:
                    return distance + 1
                visited.add(next_position)
                queue.append((next_position, distance + 1))

        return self.width * self.height

    def to_payload(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "cells": self.walls,
        }


@dataclass
class AITraceItem:
    direction: Direction
    target: Position
    score: float
    nodes: int
    pruned: int


@dataclass
class GameState:
    maze: Maze
    player: Position
    enemy: Position
    exit: Position
    difficulty: str
    turn: int = 0
    status: str = "playing"
    message: str = "Reach the exit before the enemy catches you."
    ai_depth: int = 0
    player_bias: float = 1.5
    ai_trace: list[AITraceItem] = field(default_factory=list)
    last_player_move: str = ""
    last_enemy_move: str = ""

    def to_payload(self) -> dict:
        return {
            "maze": self.maze.to_payload(),
            "player": {"x": self.player[0], "y": self.player[1]},
            "enemy": {"x": self.enemy[0], "y": self.enemy[1]},
            "exit": {"x": self.exit[0], "y": self.exit[1]},
            "turn": self.turn,
            "status": self.status,
            "difficulty": self.difficulty,
            "message": self.message,
            "ai": {
                "depth": self.ai_depth,
                "trace": [
                    {
                        "direction": item.direction,
                        "target": {"x": item.target[0], "y": item.target[1]},
                        "score": item.score,
                        "nodes": item.nodes,
                        "pruned": item.pruned,
                    }
                    for item in self.ai_trace
                ],
            },
            "lastPlayerMove": self.last_player_move,
            "lastEnemyMove": self.last_enemy_move,
        }


@dataclass
class GameSession:
    width: int = 13
    height: int = 13
    seed: int | None = None
    rng: random.Random = field(init=False)
    state: GameState = field(init=False)

    def __post_init__(self) -> None:
        self.seed = self.seed if self.seed is not None else random.SystemRandom().randint(1, 1_000_000_000)
        self.rng = random.Random(self.seed)
        self.reset("medium")

    def reset(self, difficulty: str = "medium") -> GameState:
        if difficulty not in DIFFICULTIES:
            difficulty = "medium"

        self.seed = random.SystemRandom().randint(1, 1_000_000_000)
        self.rng = random.Random(self.seed)
        maze = Maze.generate(self.width, self.height, self.rng)

        cfg = DIFFICULTIES[difficulty]

        # Player: top-left corner (0,0)
        # Exit:   bottom-right corner (W-1, H-1)
        # Enemy:  bottom-left corner (0, H-1)  ← opposite side from exit
        # This means the enemy must travel diagonally to intercept you,
        # rather than sitting right next to the exit already.
        self.state = GameState(
            maze=maze,
            player=(0, 0),
            enemy=(0, self.height - 1),
            exit=(self.width - 1, self.height - 1),
            difficulty=difficulty,
            ai_depth=cfg["depth"],
            player_bias=cfg["player_bias"],
        )
        self.state.message = f"New game started on {difficulty.title()} difficulty."
        return self.state

    def move_player(self, direction: Direction) -> GameState:
        if self.state.status != "playing":
            return self.state

        self.state.turn += 1
        self.state.last_player_move = direction
        self.state.last_enemy_move = ""
        self.state.ai_trace = []

        if direction in DIRS:
            moved = self._step(self.state.player, direction)
            if moved is not None:
                self.state.player = moved
                self.state.message = f"You moved {self._direction_name(direction)}."
            else:
                self.state.message = f"You tried to move {self._direction_name(direction)}, but a wall blocked the way."

        if self.state.player == self.state.exit:
            self.state.status = "won"
            self.state.message = "You escaped the dungeon! 🎉"
            return self.state

        if self.state.player == self.state.enemy:
            self.state.status = "lost"
            self.state.message = "The enemy caught you."
            return self.state

        enemy_move, trace = self._choose_enemy_move()
        self.state.ai_trace = trace
        if enemy_move is not None:
            direction_name, next_enemy = enemy_move
            self.state.enemy = next_enemy
            self.state.last_enemy_move = direction_name
            if trace:
                self.state.message = (
                    f"Enemy moved {self._direction_name(direction_name)} "
                    f"(minimax score {trace[0].score:.1f})."
                )

        if self.state.enemy == self.state.player:
            self.state.status = "lost"
            self.state.message = "The enemy caught you."

        return self.state

    def _step(self, position: Position, direction: Direction) -> Position | None:
        x, y = position
        if self.state.maze.walls[y][x][direction]:
            return None
        dx, dy = DIRS[direction]
        return x + dx, y + dy

    def _direction_name(self, direction: Direction) -> str:
        return {"N": "North", "S": "South", "E": "East", "W": "West"}[direction]

    def _evaluate(self, player: Position, enemy: Position) -> float:
        """
        Score from the ENEMY's perspective (enemy minimizes this value).

        Terminal states:
          player at exit  → enemy failed  → very high score (good for player)
          player == enemy → enemy caught  → very low score  (bad for player)

        Heuristic (non-terminal):
          We want a score the enemy minimises that naturally balances:
            - closing the gap to the player  (enemy wants distance_ep small)
            - preventing the player reaching exit (enemy wants distance_pe large)

          score = player_bias * distance_to_exit  -  distance_enemy_to_player

          player_bias > 1 → player has an advantage (easier difficulty)
          player_bias ≈ 0 → enemy ignores exit, pure pursuit (hardest)

          The enemy minimises this, so:
            - minimising player_bias * distance_to_exit means blocking the exit path
            - minimising (- distance_ep) means catching the player
        """
        if player == self.state.exit:
            return 10_000.0
        if player == enemy:
            return -10_000.0

        dist_enemy_to_player = self.state.maze.shortest_distance(enemy, player)
        dist_player_to_exit  = self.state.maze.shortest_distance(player, self.state.exit)

        return (self.state.player_bias * dist_player_to_exit * 10) - (dist_enemy_to_player * 10)

    def _choose_enemy_move(self) -> tuple[tuple[Direction, Position] | None, list[AITraceItem]]:
        moves = self.state.maze.legal_moves(self.state.enemy)
        if not moves:
            return None, []

        depth = self.state.ai_depth
        trace: list[AITraceItem] = []
        best_move: tuple[Direction, Position] | None = None
        best_score = float("inf")

        for direction, target in moves:
            search = self._make_search()
            score = search(self.state.player, target, depth - 1, True, float("-inf"), float("inf"))
            stats = getattr(search, "stats", {"nodes": 0, "pruned": 0})
            trace.append(AITraceItem(
                direction=direction,
                target=target,
                score=score,
                nodes=stats["nodes"],
                pruned=stats["pruned"],
            ))
            if score < best_score:
                best_score = score
                best_move = (direction, target)

        trace.sort(key=lambda item: item.score)
        return best_move, trace

    def _make_search(self):
        maze = self.state.maze
        goal = self.state.exit
        stats = {"nodes": 0, "pruned": 0}

        def search(player: Position, enemy: Position, depth: int, maximizing: bool, alpha: float, beta: float) -> float:
            stats["nodes"] += 1
            if depth <= 0 or player == goal or player == enemy:
                return self._evaluate(player, enemy)

            if maximizing:
                best = float("-inf")
                for _, next_player in maze.legal_moves(player):
                    score = search(next_player, enemy, depth - 1, False, alpha, beta)
                    best = max(best, score)
                    alpha = max(alpha, best)
                    if alpha >= beta:
                        stats["pruned"] += 1
                        break
                return best if best != float("-inf") else self._evaluate(player, enemy)

            best = float("inf")
            for _, next_enemy in maze.legal_moves(enemy):
                score = search(player, next_enemy, depth - 1, True, alpha, beta)
                best = min(best, score)
                beta = min(beta, best)
                if alpha >= beta:
                    stats["pruned"] += 1
                    break
            return best if best != float("inf") else self._evaluate(player, enemy)

        search.stats = stats  # type: ignore[attr-defined]
        return search


def create_session(difficulty: str = "medium", width: int = 13, height: int = 13) -> GameSession:
    session = GameSession(width=width, height=height)
    session.reset(difficulty)
    return session

















# from __future__ import annotations

# from collections import deque
# from dataclasses import dataclass, field
# import random

# Direction = str
# Position = tuple[int, int]

# DIRS: dict[Direction, tuple[int, int]] = {
#     "N": (0, -1),
#     "S": (0, 1),
#     "E": (1, 0),
#     "W": (-1, 0),
# }

# OPPOSITE: dict[Direction, Direction] = {"N": "S", "S": "N", "E": "W", "W": "E"}

# # Difficulty config:
# #   depth        = minimax lookahead (higher = smarter enemy)
# #   chase_weight = how aggressively enemy prioritises catching player vs blocking exit
# #                  1.0 = pure chase, 0.0 = pure exit block, 0.6 = balanced
# DIFFICULTIES = {
#     "easy":   {"depth": 2, "chase_weight": 0.5},
#     "medium": {"depth": 3, "chase_weight": 0.7},
#     "hard":   {"depth": 5, "chase_weight": 0.9},
# }


# @dataclass
# class Maze:
#     width: int
#     height: int
#     walls: list[list[dict[str, bool]]]

#     @classmethod
#     def generate(cls, width: int, height: int, rng: random.Random) -> "Maze":
#         walls = [[{"N": True, "S": True, "E": True, "W": True}
#                   for _ in range(width)] for _ in range(height)]
#         visited = [[False] * width for _ in range(height)]
#         stack: list[Position] = [(0, 0)]
#         visited[0][0] = True

#         while stack:
#             x, y = stack[-1]
#             dirs = list(DIRS.items())
#             rng.shuffle(dirs)
#             pushed = False
#             for direction, (dx, dy) in dirs:
#                 nx, ny = x + dx, y + dy
#                 if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
#                     walls[y][x][direction] = False
#                     walls[ny][nx][OPPOSITE[direction]] = False
#                     visited[ny][nx] = True
#                     stack.append((nx, ny))
#                     pushed = True
#                     break
#             if not pushed:
#                 stack.pop()

#         return cls(width=width, height=height, walls=walls)

#     def legal_moves(self, position: Position) -> list[tuple[Direction, Position]]:
#         x, y = position
#         options: list[tuple[Direction, Position]] = []
#         for direction, (dx, dy) in DIRS.items():
#             if not self.walls[y][x][direction]:
#                 nx, ny = x + dx, y + dy
#                 if 0 <= nx < self.width and 0 <= ny < self.height:
#                     options.append((direction, (nx, ny)))
#         return options

#     def bfs_distance(self, start: Position, goal: Position) -> int:
#         """BFS shortest path distance through maze walls."""
#         if start == goal:
#             return 0
#         queue: deque[tuple[Position, int]] = deque([(start, 0)])
#         visited: set[Position] = {start}
#         while queue:
#             pos, dist = queue.popleft()
#             for _, npos in self.legal_moves(pos):
#                 if npos == goal:
#                     return dist + 1
#                 if npos not in visited:
#                     visited.add(npos)
#                     queue.append((npos, dist + 1))
#         return self.width * self.height  # unreachable fallback

#     def bfs_next_step(self, start: Position, goal: Position) -> Position | None:
#         """Return the first step on the BFS shortest path from start → goal."""
#         if start == goal:
#             return None
#         queue: deque[tuple[Position, Position]] = deque([(start, start)])
#         visited: set[Position] = {start}
#         # store (current, first_step)
#         first_steps: dict[Position, Position] = {}
#         for _, npos in self.legal_moves(start):
#             first_steps[npos] = npos
#             visited.add(npos)
#             queue.append((npos, npos))

#         while queue:
#             pos, first = queue.popleft()
#             if pos == goal:
#                 return first
#             for _, npos in self.legal_moves(pos):
#                 if npos not in visited:
#                     visited.add(npos)
#                     first_steps[npos] = first
#                     queue.append((npos, first))
#         return None

#     def to_payload(self) -> dict:
#         return {
#             "width": self.width,
#             "height": self.height,
#             "cells": self.walls,
#         }


# @dataclass
# class AITraceItem:
#     direction: Direction
#     target: Position
#     score: float
#     nodes: int
#     pruned: int


# @dataclass
# class GameState:
#     maze: Maze
#     player: Position
#     enemy: Position
#     exit: Position
#     difficulty: str
#     turn: int = 0
#     status: str = "playing"
#     message: str = "Reach the exit before the enemy catches you."
#     ai_depth: int = 0
#     chase_weight: float = 0.7
#     ai_trace: list[AITraceItem] = field(default_factory=list)
#     last_player_move: str = ""
#     last_enemy_move: str = ""

#     def to_payload(self) -> dict:
#         return {
#             "maze": self.maze.to_payload(),
#             "player": {"x": self.player[0], "y": self.player[1]},
#             "enemy": {"x": self.enemy[0], "y": self.enemy[1]},
#             "exit": {"x": self.exit[0], "y": self.exit[1]},
#             "turn": self.turn,
#             "status": self.status,
#             "difficulty": self.difficulty,
#             "message": self.message,
#             "ai": {
#                 "depth": self.ai_depth,
#                 "trace": [
#                     {
#                         "direction": item.direction,
#                         "target": {"x": item.target[0], "y": item.target[1]},
#                         "score": item.score,
#                         "nodes": item.nodes,
#                         "pruned": item.pruned,
#                     }
#                     for item in self.ai_trace
#                 ],
#             },
#             "lastPlayerMove": self.last_player_move,
#             "lastEnemyMove": self.last_enemy_move,
#         }


# @dataclass
# class GameSession:
#     width: int = 13
#     height: int = 13
#     seed: int | None = None
#     rng: random.Random = field(init=False)
#     state: GameState = field(init=False)

#     def __post_init__(self) -> None:
#         self.seed = self.seed if self.seed is not None else random.SystemRandom().randint(1, 1_000_000_000)
#         self.rng = random.Random(self.seed)
#         self.reset("medium")

#     def reset(self, difficulty: str = "medium") -> GameState:
#         if difficulty not in DIFFICULTIES:
#             difficulty = "medium"

#         self.seed = random.SystemRandom().randint(1, 1_000_000_000)
#         self.rng = random.Random(self.seed)
#         maze = Maze.generate(self.width, self.height, self.rng)
#         cfg = DIFFICULTIES[difficulty]

#         # Layout:
#         #   Player  → top-left  (0, 0)
#         #   Exit    → bottom-right (W-1, H-1)
#         #   Enemy   → top-right (W-1, 0)  — far from exit, must cross full maze
#         self.state = GameState(
#             maze=maze,
#             player=(0, 0),
#             enemy=(self.width - 1, 0),
#             exit=(self.width - 1, self.height - 1),
#             difficulty=difficulty,
#             ai_depth=cfg["depth"],
#             chase_weight=cfg["chase_weight"],
#         )
#         self.state.message = f"New game started on {difficulty.title()} difficulty. Reach the ★ exit!"
#         return self.state

#     # ------------------------------------------------------------------ #
#     #  Public API                                                          #
#     # ------------------------------------------------------------------ #

#     def move_player(self, direction: Direction) -> GameState:
#         if self.state.status != "playing":
#             return self.state

#         self.state.turn += 1
#         self.state.last_player_move = direction
#         self.state.last_enemy_move = ""
#         self.state.ai_trace = []

#         # --- player move ---
#         if direction in DIRS:
#             moved = self._step(self.state.player, direction)
#             if moved is not None:
#                 self.state.player = moved
#                 self.state.message = f"You moved {self._dir_name(direction)}."
#             else:
#                 self.state.message = f"Wall blocked your {self._dir_name(direction)} move."

#         if self._check_win_loss():
#             return self.state

#         # --- enemy move (minimax) ---
#         enemy_dir, next_enemy, trace = self._enemy_move()
#         self.state.ai_trace = trace
#         if enemy_dir is not None and next_enemy is not None:
#             self.state.enemy = next_enemy
#             self.state.last_enemy_move = enemy_dir
#             best_score = trace[0].score if trace else 0.0
#             self.state.message = (
#                 f"Enemy moved {self._dir_name(enemy_dir)} "
#                 f"(score {best_score:.1f}). "
#                 f"You moved {self._dir_name(self.state.last_player_move)}."
#             )

#         self._check_win_loss()
#         return self.state

#     # ------------------------------------------------------------------ #
#     #  Internal helpers                                                    #
#     # ------------------------------------------------------------------ #

#     def _check_win_loss(self) -> bool:
#         if self.state.player == self.state.exit:
#             self.state.status = "won"
#             self.state.message = "🎉 You escaped the dungeon!"
#             return True
#         if self.state.player == self.state.enemy:
#             self.state.status = "lost"
#             self.state.message = "💀 The enemy caught you!"
#             return True
#         return False

#     def _step(self, position: Position, direction: Direction) -> Position | None:
#         x, y = position
#         if self.state.maze.walls[y][x][direction]:
#             return None
#         dx, dy = DIRS[direction]
#         return (x + dx, y + dy)

#     def _dir_name(self, d: Direction) -> str:
#         return {"N": "North", "S": "South", "E": "East", "W": "West"}.get(d, d)

#     # ------------------------------------------------------------------ #
#     #  Evaluation                                                          #
#     # ------------------------------------------------------------------ #

#     def _evaluate(self, player: Position, enemy: Position) -> float:
#         """
#         Score from the PLAYER's perspective (high = good for player).
#         Enemy minimises this score via minimax.

#         Terminal:
#           player at exit  →  +10000  (player wins)
#           player == enemy →  -10000  (enemy wins)

#         Heuristic:
#           dist_ep  = BFS distance enemy → player    (enemy wants this small)
#           dist_pe  = BFS distance player → exit     (player wants this small)

#           score = chase_weight * dist_ep  -  (1 - chase_weight) * dist_pe * 2

#           chase_weight high → enemy prioritises closing in on player
#           chase_weight low  → enemy prioritises blocking the exit path
#           Both always contribute, preventing oscillation.
#         """
#         if player == self.state.exit:
#             return 10_000.0
#         if player == enemy:
#             return -10_000.0

#         maze = self.state.maze
#         dist_ep = maze.bfs_distance(enemy, player)
#         dist_pe = maze.bfs_distance(player, self.state.exit)
#         cw = self.state.chase_weight

#         return float(cw * dist_ep * 10 - (1.0 - cw) * dist_pe * 20)

#     # ------------------------------------------------------------------ #
#     #  Minimax with alpha-beta                                             #
#     # ------------------------------------------------------------------ #

#     def _enemy_move(self) -> tuple[Direction | None, Position | None, list[AITraceItem]]:
#         moves = self.state.maze.legal_moves(self.state.enemy)
#         if not moves:
#             return None, None, []

#         depth = self.state.ai_depth
#         trace: list[AITraceItem] = []
#         best_dir: Direction | None = None
#         best_pos: Position | None = None
#         best_score = float("inf")      # enemy MINIMISES

#         for direction, target in moves:
#             stats: dict[str, int] = {"nodes": 0, "pruned": 0}
#             score = self._minimax(
#                 self.state.player, target,
#                 depth - 1, True,
#                 float("-inf"), float("inf"),
#                 stats,
#             )
#             trace.append(AITraceItem(
#                 direction=direction,
#                 target=target,
#                 score=score,
#                 nodes=stats["nodes"],
#                 pruned=stats["pruned"],
#             ))
#             if score < best_score:
#                 best_score = score
#                 best_dir = direction
#                 best_pos = target

#         trace.sort(key=lambda i: i.score)
#         return best_dir, best_pos, trace

#     def _minimax(
#         self,
#         player: Position,
#         enemy: Position,
#         depth: int,
#         maximizing: bool,
#         alpha: float,
#         beta: float,
#         stats: dict[str, int],
#     ) -> float:
#         stats["nodes"] += 1

#         if depth <= 0 or player == self.state.exit or player == enemy:
#             return self._evaluate(player, enemy)

#         maze = self.state.maze

#         if maximizing:  # player's turn — maximise score
#             best = float("-inf")
#             for _, np in maze.legal_moves(player):
#                 v = self._minimax(np, enemy, depth - 1, False, alpha, beta, stats)
#                 if v > best:
#                     best = v
#                 alpha = max(alpha, best)
#                 if alpha >= beta:
#                     stats["pruned"] += 1
#                     break
#             return best if best != float("-inf") else self._evaluate(player, enemy)

#         else:           # enemy's turn — minimise score
#             best = float("inf")
#             for _, ne in maze.legal_moves(enemy):
#                 v = self._minimax(player, ne, depth - 1, True, alpha, beta, stats)
#                 if v < best:
#                     best = v
#                 beta = min(beta, best)
#                 if alpha >= beta:
#                     stats["pruned"] += 1
#                     break
#             return best if best != float("inf") else self._evaluate(player, enemy)


# def create_session(difficulty: str = "medium", width: int = 13, height: int = 13) -> GameSession:
#     session = GameSession(width=width, height=height)
#     session.reset(difficulty)
#     return session