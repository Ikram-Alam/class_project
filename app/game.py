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
DIR_NAMES: dict[Direction, str] = {"N": "North", "S": "South", "E": "East", "W": "West"}

# Terminal evaluation values, from the PLAYER's perspective.
# Player maximises this value; the enemy minimises it.
PLAYER_ESCAPES = 10_000.0   # player reached the exit  -> best for player
PLAYER_CAUGHT = -10_000.0   # enemy landed on player    -> best for enemy

# ── Difficulty configuration ──────────────────────────────────────────────
#
#   depth        minimax look-ahead in plies (higher = smarter enemy)
#   chase_w      weight on "enemy distance to player" (drives pursuit)
#   exit_w       weight on "player distance to exit"  (drives interception:
#                the enemy predicts the player heads for the exit and cuts
#                it off). chase_w/exit_w are coprime to minimise score ties.
#   head_start   turns the enemy is frozen at the start of the game
#   blunder      probability per turn the enemy plays a random legal move
#                instead of the optimal one (used to soften Easy)
#   move_every   the enemy only acts on every Nth player turn (2 = half speed,
#                which effectively lets the player move twice as often)
#
# Together these give roughly:
#   easy   – very beatable: shallow, naive pursuit, half-speed, freeze, blunders
#   medium – fair fight
#   hard   – deep look-ahead, full speed, no freeze, strong interception
DIFFICULTIES: dict[str, dict] = {
    "easy":   {"depth": 2, "chase_w": 5,  "exit_w": 0, "head_start": 5, "blunder": 0.35, "move_every": 2},
    "medium": {"depth": 4, "chase_w": 7,  "exit_w": 5, "head_start": 2, "blunder": 0.05, "move_every": 1},
    "hard":   {"depth": 6, "chase_w": 11, "exit_w": 7, "head_start": 0, "blunder": 0.0,  "move_every": 1},
}

DEFAULT_DIFFICULTY = "medium"


# ── Maze ──────────────────────────────────────────────────────────────────

@dataclass
class Maze:
    width: int
    height: int
    walls: list[list[dict[str, bool]]]
    # Cache of single-source BFS distance maps, keyed by source cell.
    # Excluded from equality/repr so two structurally equal mazes still compare.
    _dist_cache: dict[Position, dict[Position, int]] = field(
        default_factory=dict, compare=False, repr=False
    )

    @classmethod
    def generate(cls, width: int, height: int, rng: random.Random) -> "Maze":
        """Recursive-backtracker (DFS) perfect maze: every cell reachable by
        exactly one path, so there are no loops."""
        walls = [
            [{"N": True, "S": True, "E": True, "W": True} for _ in range(width)]
            for _ in range(height)
        ]
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
        cell = self.walls[y][x]
        options: list[tuple[Direction, Position]] = []
        for direction, (dx, dy) in DIRS.items():
            if not cell[direction]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    options.append((direction, (nx, ny)))
        return options

    def distances_from(self, source: Position) -> dict[Position, int]:
        """BFS the whole reachable region once and cache the full distance map.

        A single BFS yields the shortest-path distance from ``source`` to every
        cell, so callers that need many distances from the same source (the
        minimax leaves do) pay for one traversal instead of one-per-query.
        """
        cached = self._dist_cache.get(source)
        if cached is not None:
            return cached

        distances: dict[Position, int] = {source: 0}
        queue: deque[Position] = deque([source])
        while queue:
            current = queue.popleft()
            base = distances[current]
            for _, nxt in self.legal_moves(current):
                if nxt not in distances:
                    distances[nxt] = base + 1
                    queue.append(nxt)

        self._dist_cache[source] = distances
        return distances

    def shortest_distance(self, start: Position, goal: Position) -> int:
        """BFS shortest-path distance through the maze (memoised)."""
        distances = self.distances_from(start)
        # In a perfect maze everything is reachable; the fallback is defensive.
        return distances.get(goal, self.width * self.height)

    def to_payload(self) -> dict:
        return {"width": self.width, "height": self.height, "cells": self.walls}


# ── AI trace (sent to the UI to visualise the enemy's reasoning) ───────────

@dataclass
class AITraceItem:
    direction: Direction
    target: Position
    score: float
    nodes: int
    pruned: int


# ── Game state ─────────────────────────────────────────────────────────────

@dataclass
class GameState:
    maze: Maze
    player: Position
    enemy: Position
    exit: Position
    difficulty: str
    # AI tuning derived from the difficulty config
    ai_depth: int = 0
    chase_weight: int = 7
    exit_weight: int = 5
    blunder: float = 0.0
    move_every: int = 1
    # Runtime bookkeeping
    turn: int = 0
    frozen_turns: int = 0
    status: str = "playing"
    message: str = "Reach the exit before the enemy catches you."
    ai_trace: list[AITraceItem] = field(default_factory=list)
    last_player_move: str = ""
    last_enemy_move: str = ""
    # Anti-oscillation history
    enemy_prev: Position | None = None
    enemy_history: list[Position] = field(default_factory=list)

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
            "frozen_turns": self.frozen_turns,
            "player_steps": 1,
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


# ── Session / game loop ─────────────────────────────────────────────────────

# How many recent enemy cells to remember when penalising re-visits.
ENEMY_HISTORY_LEN = 10


@dataclass
class GameSession:
    width: int = 13
    height: int = 13
    seed: int | None = None
    rng: random.Random = field(init=False)
    state: GameState = field(init=False)

    def __post_init__(self) -> None:
        if self.seed is None:
            self.seed = random.SystemRandom().randint(1, 1_000_000_000)
        self.rng = random.Random(self.seed)
        self.reset(DEFAULT_DIFFICULTY)

    # ── public API ──────────────────────────────────────────────────────

    def reset(self, difficulty: str = DEFAULT_DIFFICULTY) -> GameState:
        if difficulty not in DIFFICULTIES:
            difficulty = DEFAULT_DIFFICULTY

        # Fresh maze each game.
        self.seed = random.SystemRandom().randint(1, 1_000_000_000)
        self.rng = random.Random(self.seed)
        maze = Maze.generate(self.width, self.height, self.rng)
        cfg = DIFFICULTIES[difficulty]

        # Player: top-left (0,0).  Exit: bottom-right (W-1, H-1).
        # Enemy: bottom-left (0, H-1) — the opposite side from the exit, so it
        # has to travel to intercept rather than camping the goal.
        self.state = GameState(
            maze=maze,
            player=(0, 0),
            enemy=(0, self.height - 1),
            exit=(self.width - 1, self.height - 1),
            difficulty=difficulty,
            ai_depth=cfg["depth"],
            chase_weight=cfg["chase_w"],
            exit_weight=cfg["exit_w"],
            blunder=cfg["blunder"],
            move_every=cfg["move_every"],
            frozen_turns=cfg["head_start"],
        )

        path = maze.shortest_distance(self.state.player, self.state.exit)
        freeze = (
            f" Enemy frozen for {cfg['head_start']} turns."
            if cfg["head_start"] > 0
            else ""
        )
        self.state.message = (
            f"{difficulty.title()} game started — your path to the exit is "
            f"{path} steps.{freeze}"
        )
        return self.state

    def move_player(self, direction: Direction) -> GameState:
        if self.state.status != "playing":
            return self.state
        if direction not in DIRS:
            return self.state

        moved = self._step(self.state.player, direction)
        if moved is None:
            # A blocked move is a no-op: it costs no turn and the enemy does not
            # get a free move, so probing walls is never punished.
            self.state.message = (
                f"A wall blocks the way {DIR_NAMES[direction]}."
            )
            return self.state

        self.state.turn += 1
        self.state.player = moved
        self.state.last_player_move = direction
        self.state.last_enemy_move = ""
        self.state.ai_trace = []
        self.state.message = f"You moved {DIR_NAMES[direction]}."

        if self.state.player == self.state.exit:
            self.state.status = "won"
            self.state.message = "You escaped the dungeon! 🎉"
            return self.state
        if self.state.player == self.state.enemy:
            self.state.status = "lost"
            self.state.message = "The enemy caught you."
            return self.state

        # Enemy turn (unless still frozen during its head-start).
        if self.state.frozen_turns > 0:
            self.state.frozen_turns -= 1
            self.state.message += f" (Enemy frozen: {self.state.frozen_turns} left.)"
            return self.state

        # A slow enemy (easy mode) only acts on every Nth turn.
        if self.state.move_every > 1 and self.state.turn % self.state.move_every != 0:
            self.state.message += " (Enemy resting.)"
            return self.state

        enemy_move, trace = self._choose_enemy_move()
        self.state.ai_trace = trace
        if enemy_move is not None:
            direction_name, next_enemy = enemy_move
            self.state.enemy_prev = self.state.enemy
            self.state.enemy_history.append(self.state.enemy)
            del self.state.enemy_history[:-ENEMY_HISTORY_LEN]
            self.state.enemy = next_enemy
            self.state.last_enemy_move = direction_name
            best_score = trace[0].score if trace else 0.0
            self.state.message = (
                f"Enemy moved {DIR_NAMES[direction_name]} "
                f"(minimax score {best_score:.0f})."
            )

        if self.state.enemy == self.state.player:
            self.state.status = "lost"
            self.state.message = "The enemy caught you."

        return self.state

    # ── internals ──────────────────────────────────────────────────────

    def _step(self, position: Position, direction: Direction) -> Position | None:
        x, y = position
        if self.state.maze.walls[y][x][direction]:
            return None
        dx, dy = DIRS[direction]
        return x + dx, y + dy

    def _evaluate(self, player: Position, enemy: Position) -> float:
        """Static evaluation from the PLAYER's perspective.

        The player maximises this score and the enemy minimises it:

          * player on the exit            -> +PLAYER_ESCAPES  (best for player)
          * enemy on the player           -> +PLAYER_CAUGHT   (best for enemy)
          * otherwise:
                score = chase_w * dist(enemy → player)      # player wants this big
                      -  exit_w * dist(player → exit)        # player wants this small

        So a MINIMISING enemy is driven to shrink its distance to the player
        (pursuit) while the exit term makes it assume the player is racing for
        the exit and lets it cut the player off (interception). Coprime weights
        keep distinct distance pairs from colliding, which avoids score ties.
        """
        if player == self.state.exit:
            return PLAYER_ESCAPES
        if player == enemy:
            return PLAYER_CAUGHT

        maze = self.state.maze
        dist_enemy_to_player = maze.shortest_distance(enemy, player)
        dist_player_to_exit = maze.shortest_distance(player, self.state.exit)
        return (
            self.state.chase_weight * dist_enemy_to_player
            - self.state.exit_weight * dist_player_to_exit
        )

    def _choose_enemy_move(
        self,
    ) -> tuple[tuple[Direction, Position] | None, list[AITraceItem]]:
        moves = self.state.maze.legal_moves(self.state.enemy)
        if not moves:
            return None, []

        depth = self.state.ai_depth
        candidates: list[tuple[Direction, Position, float]] = []
        trace: list[AITraceItem] = []

        for direction, target in moves:
            stats = {"nodes": 0, "pruned": 0}
            # After the enemy moves to `target` it becomes the player's turn,
            # so the next ply maximises.
            score = self._minimax(
                player=self.state.player,
                enemy=target,
                depth=depth - 1,
                maximizing=True,
                alpha=float("-inf"),
                beta=float("inf"),
                stats=stats,
            )
            candidates.append((direction, target, score))
            trace.append(
                AITraceItem(
                    direction=direction,
                    target=target,
                    score=score,
                    nodes=stats["nodes"],
                    pruned=stats["pruned"],
                )
            )

        trace.sort(key=lambda item: item.score)

        # Easy mode occasionally blunders so it is not robotically optimal.
        if self.state.blunder > 0 and self.rng.random() < self.state.blunder:
            direction, target, _ = self.rng.choice(candidates)
            return (direction, target), trace

        best = min(candidates, key=self._move_sort_key)
        return (best[0], best[1]), trace

    def _move_sort_key(
        self, candidate: tuple[Direction, Position, float]
    ) -> tuple:
        """Ordering used to pick the enemy move.

        The minimax score is always primary, so intelligence is never
        sacrificed — the remaining keys only break genuine ties and exist to
        stop oscillation:

          1. score                  – the minimax value (enemy minimises)
          2. reversal penalty       – avoid stepping straight back where it came
          3. revisit penalty        – avoid recently visited cells
          4. greedy distance        – otherwise make real progress toward player
          5. direction              – final deterministic tie-break
        """
        direction, target, score = candidate
        reversal = 1 if target == self.state.enemy_prev else 0
        revisit = self.state.enemy_history.count(target)
        dist_after = self.state.maze.shortest_distance(target, self.state.player)
        # round() neutralises float noise; heuristic scores are integral.
        return (round(score, 3), reversal, revisit, dist_after, direction)

    def _minimax(
        self,
        player: Position,
        enemy: Position,
        depth: int,
        maximizing: bool,
        alpha: float,
        beta: float,
        stats: dict[str, int],
    ) -> float:
        """Minimax with alpha-beta pruning.

        `maximizing` is True on the player's plies (they maximise the score)
        and False on the enemy's plies (they minimise). Alpha is the best value
        the maximiser can guarantee so far, beta the best for the minimiser;
        once alpha >= beta the remaining siblings cannot affect the result and
        are pruned.
        """
        stats["nodes"] += 1

        if depth <= 0 or player == self.state.exit or player == enemy:
            return self._evaluate(player, enemy)

        maze = self.state.maze

        if maximizing:  # player's turn
            best = float("-inf")
            for _, next_player in maze.legal_moves(player):
                value = self._minimax(
                    next_player, enemy, depth - 1, False, alpha, beta, stats
                )
                best = max(best, value)
                alpha = max(alpha, best)
                if alpha >= beta:
                    stats["pruned"] += 1
                    break
            return best if best != float("-inf") else self._evaluate(player, enemy)

        # enemy's turn
        best = float("inf")
        for _, next_enemy in maze.legal_moves(enemy):
            value = self._minimax(
                player, next_enemy, depth - 1, True, alpha, beta, stats
            )
            best = min(best, value)
            beta = min(beta, best)
            if alpha >= beta:
                stats["pruned"] += 1
                break
        return best if best != float("inf") else self._evaluate(player, enemy)


def create_session(
    difficulty: str = DEFAULT_DIFFICULTY, width: int = 13, height: int = 13
) -> GameSession:
    session = GameSession(width=width, height=height)
    session.reset(difficulty)
    return session
