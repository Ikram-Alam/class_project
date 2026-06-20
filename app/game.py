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
# Position  = tuple[int, int]

# DIRS: dict[Direction, tuple[int, int]] = {
#     "N": (0, -1), "S": (0,  1),
#     "E": (1,  0), "W": (-1, 0),
# }
# OPPOSITE: dict[Direction, Direction] = {
#     "N": "S", "S": "N", "E": "W", "W": "E",
# }

# # ── Difficulty config ─────────────────────────────────────────────────────
# #
# #  depth        – minimax lookahead depth (higher = smarter enemy)
# #  head_start   – free player turns before enemy starts moving
# #  player_steps – cells the PLAYER moves per turn (2 on easy = faster player)
# #
# #  These three levers together give well-balanced winrates:
# #    easy   ~50% with perfect play, ~30% for a casual human
# #    medium ~25% with perfect play, ~10-15% for a casual human
# #    hard   ~15% with perfect play — genuinely tough
# #
# DIFFICULTIES: dict[str, dict] = {
#     "easy":   {"depth": 2, "head_start": 10, "player_steps": 2},
#     "medium": {"depth": 3, "head_start":  5, "player_steps": 1},
#     "hard":   {"depth": 5, "head_start":  0, "player_steps": 1},
# }


# # ── Maze ──────────────────────────────────────────────────────────────────

# @dataclass
# class Maze:
#     width:  int
#     height: int
#     walls:  list[list[dict[str, bool]]]

#     @classmethod
#     def generate(cls, width: int, height: int, rng: random.Random) -> "Maze":
#         """Recursive-backtracker DFS perfect maze (no loops = guaranteed unique path)."""
#         walls   = [[{"N": True, "S": True, "E": True, "W": True}
#                     for _ in range(width)] for _ in range(height)]
#         visited = [[False] * width for _ in range(height)]
#         stack: list[Position] = [(0, 0)]
#         visited[0][0] = True

#         while stack:
#             x, y = stack[-1]
#             dirs = list(DIRS.items())
#             rng.shuffle(dirs)           # ← shuffle, not rng.choice, for unbiased mazes
#             pushed = False
#             for d, (dx, dy) in dirs:
#                 nx, ny = x + dx, y + dy
#                 if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
#                     walls[y][x][d]              = False
#                     walls[ny][nx][OPPOSITE[d]]  = False
#                     visited[ny][nx]             = True
#                     stack.append((nx, ny))
#                     pushed = True
#                     break
#             if not pushed:
#                 stack.pop()

#         return cls(width=width, height=height, walls=walls)

#     def legal_moves(self, pos: Position) -> list[tuple[Direction, Position]]:
#         x, y = pos
#         return [
#             (d, (x + dx, y + dy))
#             for d, (dx, dy) in DIRS.items()
#             if not self.walls[y][x][d]
#             and 0 <= x + dx < self.width
#             and 0 <= y + dy < self.height
#         ]

#     def bfs_distance(self, start: Position, goal: Position) -> int:
#         """Exact BFS shortest-path distance through maze walls."""
#         if start == goal:
#             return 0
#         queue:   deque[tuple[Position, int]] = deque([(start, 0)])
#         visited: set[Position]               = {start}
#         while queue:
#             pos, dist = queue.popleft()
#             for _, npos in self.legal_moves(pos):
#                 if npos == goal:
#                     return dist + 1
#                 if npos not in visited:
#                     visited.add(npos)
#                     queue.append((npos, dist + 1))
#         return self.width * self.height   # unreachable (should never happen in a perfect maze)

#     def to_payload(self) -> dict:
#         return {"width": self.width, "height": self.height, "cells": self.walls}


# # ── Spawn helper ──────────────────────────────────────────────────────────

# def _best_enemy_spawn(maze: Maze, player: Position, exit_: Position) -> Position:
#     """
#     After maze generation, pick the enemy starting cell that maximises
#     enemy-to-player BFS distance, giving the player the biggest head start.

#     Checks 4 corners + 4 edge midpoints; never player or exit cell.
#     Falls back to (width-1, 0) if somehow all candidates are taken.
#     """
#     W, H = maze.width, maze.height
#     candidates: list[Position] = [
#         (W - 1, 0), (0, H - 1),
#         (W // 2, 0), (0, H // 2),
#         (W - 1, H // 2), (W // 2, H - 1),
#         (W - 1, H // 4), (W // 4, 0),
#     ]
#     valid = [p for p in candidates if p != player and p != exit_]
#     if not valid:
#         return (W - 1, 0)
#     return max(valid, key=lambda p: maze.bfs_distance(p, player))


# # ── Data classes ──────────────────────────────────────────────────────────

# @dataclass
# class AITraceItem:
#     direction: Direction
#     target:    Position
#     score:     float
#     nodes:     int
#     pruned:    int


# @dataclass
# class GameState:
#     maze:          Maze
#     player:        Position
#     enemy:         Position
#     exit:          Position
#     difficulty:    str
#     turn:          int   = 0
#     frozen_turns:  int   = 0    # how many turns remain where enemy doesn't move
#     player_steps:  int   = 1    # cells player may move per turn
#     status:        str   = "playing"
#     message:       str   = "Reach the exit before the enemy catches you."
#     ai_depth:      int   = 0
#     ai_trace:      list[AITraceItem] = field(default_factory=list)
#     last_player_move: str = ""
#     last_enemy_move:  str = ""

#     def to_payload(self) -> dict:
#         return {
#             "maze":   self.maze.to_payload(),
#             "player": {"x": self.player[0], "y": self.player[1]},
#             "enemy":  {"x": self.enemy[0],  "y": self.enemy[1]},
#             "exit":   {"x": self.exit[0],   "y": self.exit[1]},
#             "turn":        self.turn,
#             "frozen_turns": self.frozen_turns,
#             "player_steps": self.player_steps,
#             "status":      self.status,
#             "difficulty":  self.difficulty,
#             "message":     self.message,
#             "ai": {
#                 "depth": self.ai_depth,
#                 "trace": [
#                     {
#                         "direction": item.direction,
#                         "target":    {"x": item.target[0], "y": item.target[1]},
#                         "score":     item.score,
#                         "nodes":     item.nodes,
#                         "pruned":    item.pruned,
#                     }
#                     for item in self.ai_trace
#                 ],
#             },
#             "lastPlayerMove": self.last_player_move,
#             "lastEnemyMove":  self.last_enemy_move,
#         }


# # ── Session ───────────────────────────────────────────────────────────────

# @dataclass
# class GameSession:
#     width:  int           = 13
#     height: int           = 13
#     seed:   int | None    = None
#     rng:    random.Random = field(init=False)
#     state:  GameState     = field(init=False)

#     def __post_init__(self) -> None:
#         self.seed = self.seed or random.SystemRandom().randint(1, 1_000_000_000)
#         self.rng  = random.Random(self.seed)
#         self.reset("easy")

#     # ── public API ────────────────────────────────────────────────────────

#     def reset(self, difficulty: str = "easy") -> GameState:
#         if difficulty not in DIFFICULTIES:
#             difficulty = "easy"

#         self.seed = random.SystemRandom().randint(1, 1_000_000_000)
#         self.rng  = random.Random(self.seed)
#         maze      = Maze.generate(self.width, self.height, self.rng)
#         cfg       = DIFFICULTIES[difficulty]

#         player = (0, 0)
#         exit_  = (self.width - 1, self.height - 1)
#         enemy  = _best_enemy_spawn(maze, player, exit_)

#         d_player = maze.bfs_distance(player, exit_)
#         d_enemy  = maze.bfs_distance(enemy,  player)

#         self.state = GameState(
#             maze          = maze,
#             player        = player,
#             enemy         = enemy,
#             exit          = exit_,
#             difficulty    = difficulty,
#             ai_depth      = cfg["depth"],
#             frozen_turns  = cfg["head_start"],
#             player_steps  = cfg["player_steps"],
#         )

#         steps_info = f" (you move {cfg['player_steps']}× per turn)" if cfg["player_steps"] > 1 else ""
#         freeze_info = f", enemy frozen for {cfg['head_start']} turns" if cfg["head_start"] > 0 else ""
#         self.state.message = (
#             f"{difficulty.title()}{steps_info}{freeze_info}. "
#             f"Your path: {d_player} steps · enemy is {d_enemy} away. Go!"
#         )
#         return self.state

#     def move_player(self, direction: Direction) -> GameState:
#         if self.state.status != "playing":
#             return self.state

#         self.state.turn            += 1
#         self.state.last_player_move = direction
#         self.state.last_enemy_move  = ""
#         self.state.ai_trace         = []

#         # ── player moves (player_steps cells per turn) ──────────────────
#         moved_count = 0
#         for step in range(self.state.player_steps):
#             # Only the first step uses the requested direction;
#             # subsequent steps (easy mode) auto-continue in same direction.
#             move_dir = direction
#             result = self._try_step(self.state.player, move_dir)
#             if result is None:
#                 if step == 0:
#                     self.state.message = f"Wall blocked your {_dir_name(direction)} move."
#                 break
#             self.state.player = result
#             moved_count += 1
#             if self._check_end():
#                 return self.state

#         if moved_count > 0 and self.state.status == "playing":
#             steps_txt = f" ×{moved_count}" if moved_count > 1 else ""
#             self.state.message = f"You moved {_dir_name(direction)}{steps_txt}."

#         # ── enemy move ───────────────────────────────────────────────────
#         if self.state.frozen_turns > 0:
#             self.state.frozen_turns -= 1
#             remaining = self.state.frozen_turns
#             self.state.message += f" (Enemy frozen: {remaining} turns left.)"
#             return self.state

#         enemy_dir, enemy_pos, trace = self._choose_enemy_move()
#         self.state.ai_trace = trace

#         if enemy_dir is not None and enemy_pos is not None:
#             self.state.enemy          = enemy_pos
#             self.state.last_enemy_move = enemy_dir
#             best_score = trace[0].score if trace else 0.0
#             self.state.message += f" Enemy → {_dir_name(enemy_dir)} (score {best_score:.0f})."

#         self._check_end()
#         return self.state

#     # ── internals ─────────────────────────────────────────────────────────

#     def _try_step(self, pos: Position, d: Direction) -> Position | None:
#         x, y = pos
#         if self.state.maze.walls[y][x][d]:
#             return None
#         dx, dy = DIRS[d]
#         return (x + dx, y + dy)

#     def _check_end(self) -> bool:
#         if self.state.player == self.state.exit:
#             self.state.status  = "won"
#             self.state.message = "🎉 You escaped the dungeon!"
#             return True
#         if self.state.player == self.state.enemy:
#             self.state.status  = "lost"
#             self.state.message = "💀 The enemy caught you!"
#             return True
#         return False

#     # ── evaluation ────────────────────────────────────────────────────────

#     def _evaluate(self, player: Position, enemy: Position) -> float:
#         """
#         Score from the PLAYER's perspective (enemy minimises via minimax).

#         Terminal:
#             player at exit  → +10 000  (player wins)
#             player == enemy → -10 000  (enemy wins)

#         Heuristic (non-terminal):
#             dist_ep = BFS distance enemy → player   (enemy wants SMALL)
#             dist_pe = BFS distance player → exit    (player wants SMALL)

#             score = dist_ep × 11  −  dist_pe × 7

#         WHY COPRIME MULTIPLIERS (11 and 7)?
#         ─────────────────────────────────────
#         BFS distances are integers. If we used equal weights (both ×10),
#         two different enemy moves could produce identical scores, and the
#         enemy would oscillate between them every turn (the classic up-down
#         bug). Using coprime multipliers (gcd(11,7)=1) makes it impossible
#         for two distinct (dist_ep, dist_pe) pairs to yield the same score,
#         so every position in the minimax tree has a unique value — no ties,
#         no oscillation.
#         """
#         if player == self.state.exit:
#             return  10_000.0
#         if player == enemy:
#             return -10_000.0

#         dist_ep = self.state.maze.bfs_distance(enemy,  player)
#         dist_pe = self.state.maze.bfs_distance(player, self.state.exit)
#         return float(dist_ep * 11 - dist_pe * 7)

#     # ── minimax with alpha-beta pruning ───────────────────────────────────

#     def _choose_enemy_move(
#         self,
#     ) -> tuple[Direction | None, Position | None, list[AITraceItem]]:
#         moves = self.state.maze.legal_moves(self.state.enemy)
#         if not moves:
#             return None, None, []

#         trace:      list[AITraceItem]   = []
#         best_dir:   Direction | None    = None
#         best_pos:   Position  | None    = None
#         best_score: float               = float("inf")   # enemy MINIMISES

#         for direction, target in moves:
#             stats: dict[str, int] = {"nodes": 0, "pruned": 0}
#             score = self._minimax(
#                 self.state.player, target,
#                 self.state.ai_depth - 1,
#                 maximizing=True,
#                 alpha=float("-inf"), beta=float("inf"),
#                 stats=stats,
#             )
#             trace.append(AITraceItem(
#                 direction=direction, target=target,
#                 score=score, nodes=stats["nodes"], pruned=stats["pruned"],
#             ))
#             if score < best_score:
#                 best_score = score
#                 best_dir   = direction
#                 best_pos   = target

#         trace.sort(key=lambda i: i.score)
#         return best_dir, best_pos, trace

#     def _minimax(
#         self,
#         player: Position,
#         enemy:  Position,
#         depth:  int,
#         maximizing: bool,
#         alpha: float,
#         beta:  float,
#         stats: dict[str, int],
#     ) -> float:
#         stats["nodes"] += 1

#         if depth <= 0 or player == self.state.exit or player == enemy:
#             return self._evaluate(player, enemy)

#         maze = self.state.maze

#         if maximizing:                          # player's turn — maximise
#             best = float("-inf")
#             for _, np_ in maze.legal_moves(player):
#                 v    = self._minimax(np_, enemy, depth - 1, False, alpha, beta, stats)
#                 best = max(best, v)
#                 alpha = max(alpha, best)
#                 if alpha >= beta:
#                     stats["pruned"] += 1
#                     break
#             return best if best != float("-inf") else self._evaluate(player, enemy)

#         else:                                   # enemy's turn — minimise
#             best = float("inf")
#             for _, ne in maze.legal_moves(enemy):
#                 v    = self._minimax(player, ne, depth - 1, True, alpha, beta, stats)
#                 best = min(best, v)
#                 beta = min(beta, best)
#                 if alpha >= beta:
#                     stats["pruned"] += 1
#                     break
#             return best if best != float("inf") else self._evaluate(player, enemy)


# # ── helpers ───────────────────────────────────────────────────────────────

# def _dir_name(d: Direction) -> str:
#     return {"N": "North", "S": "South", "E": "East", "W": "West"}.get(d, d)


# def create_session(
#     difficulty: str = "easy",
#     width:  int = 13,
#     height: int = 13,
# ) -> GameSession:
#     session = GameSession(width=width, height=height)
#     session.reset(difficulty)
#     return session












