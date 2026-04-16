const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const statusPill = document.getElementById('statusPill');
const statusMessage = document.getElementById('statusMessage');
const turnValue = document.getElementById('turnValue');
const difficultyValue = document.getElementById('difficultyValue');
const gameStateValue = document.getElementById('gameStateValue');
const lastMoveValue = document.getElementById('lastMoveValue');
const aiDepthValue = document.getElementById('aiDepthValue');
const aiPrunedValue = document.getElementById('aiPrunedValue');
const aiNodesValue = document.getElementById('aiNodesValue');
const aiTrace = document.getElementById('aiTrace');
const newGameBtn = document.getElementById('newGameBtn');
const difficultyButtons = Array.from(document.querySelectorAll('[data-difficulty]'));
const dpadButtons = Array.from(document.querySelectorAll('.dpad [data-direction]'));

const directionToKey = {
  ArrowUp: 'N',
  ArrowDown: 'S',
  ArrowLeft: 'W',
  ArrowRight: 'E',
  w: 'N',
  s: 'S',
  a: 'W',
  d: 'E',
  W: 'N',
  S: 'S',
  A: 'W',
  D: 'E',
};

let socket;
let currentState = null;
let activeDifficulty = 'easy';

function connect() {
  socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);

  socket.addEventListener('open', () => {
    statusPill.textContent = 'Connected';
  });

  socket.addEventListener('close', () => {
    statusPill.textContent = 'Disconnected';
    statusMessage.textContent = 'The connection dropped. Refresh the page to reconnect.';
  });

  socket.addEventListener('message', (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === 'state') {
      currentState = payload.state;
      renderState();
    }
  });
}

function send(payload) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
  }
}

function sendMove(direction) {
  if (!currentState || currentState.status !== 'playing') {
    return;
  }
  send({ type: 'move', direction });
}

function startNewGame() {
  send({ type: 'new_game', difficulty: activeDifficulty });
}

function renderState() {
  if (!currentState) {
    return;
  }

  const { maze, player, enemy, exit, ai } = currentState;
  const cellSize = Math.floor(Math.min(canvas.width / maze.width, canvas.height / maze.height));
  const boardWidth = cellSize * maze.width;
  const boardHeight = cellSize * maze.height;
  const offsetX = Math.floor((canvas.width - boardWidth) / 2);
  const offsetY = Math.floor((canvas.height - boardHeight) / 2);

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const background = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  background.addColorStop(0, '#0b1220');
  background.addColorStop(1, '#0e1728');
  ctx.fillStyle = background;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
  for (let y = 0; y < maze.height; y += 1) {
    for (let x = 0; x < maze.width; x += 1) {
      ctx.fillRect(offsetX + x * cellSize, offsetY + y * cellSize, cellSize - 1, cellSize - 1);
    }
  }

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
  ctx.lineWidth = Math.max(2, Math.floor(cellSize * 0.1));
  ctx.lineCap = 'round';

  for (let y = 0; y < maze.height; y += 1) {
    for (let x = 0; x < maze.width; x += 1) {
      const cell = maze.cells[y][x];
      const px = offsetX + x * cellSize;
      const py = offsetY + y * cellSize;

      if (cell.N) {
        drawWall(px, py, px + cellSize, py);
      }
      if (cell.S) {
        drawWall(px, py + cellSize, px + cellSize, py + cellSize);
      }
      if (cell.W) {
        drawWall(px, py, px, py + cellSize);
      }
      if (cell.E) {
        drawWall(px + cellSize, py, px + cellSize, py + cellSize);
      }
    }
  }

  drawMarker(exit.x, exit.y, cellSize, offsetX, offsetY, '#f7c948', 'EXIT');
  drawCharacter(player.x, player.y, cellSize, offsetX, offsetY, '#60a5fa');
  drawCharacter(enemy.x, enemy.y, cellSize, offsetX, offsetY, '#f87171');

  statusMessage.textContent = currentState.message;
  turnValue.textContent = String(currentState.turn);
  difficultyValue.textContent = currentState.difficulty.charAt(0).toUpperCase() + currentState.difficulty.slice(1);
  gameStateValue.textContent = currentState.status.charAt(0).toUpperCase() + currentState.status.slice(1);
  lastMoveValue.textContent = currentState.lastEnemyMove || currentState.lastPlayerMove || 'None';
  aiDepthValue.textContent = String(ai.depth);

  const trace = Array.isArray(ai.trace) ? ai.trace : [];
  const totalPruned = trace.reduce((sum, item) => sum + item.pruned, 0);
  const totalNodes = trace.reduce((sum, item) => sum + item.nodes, 0);
  aiPrunedValue.textContent = String(totalPruned);
  aiNodesValue.textContent = String(totalNodes);

  const sortedTrace = [...trace].sort((a, b) => a.score - b.score);
  aiTrace.innerHTML = sortedTrace.map((item, index) => `
    <div class="trace-item ${index === 0 ? 'best' : ''}">
      <strong>${directionLabel(item.direction)} to (${item.target.x}, ${item.target.y})</strong>
      <div>Score: <span class="score">${item.score.toFixed(1)}</span> | Nodes: ${item.nodes} | Pruned: ${item.pruned}</div>
    </div>
  `).join('') || '<div class="trace-item"><strong>No available enemy moves</strong><div>The enemy is trapped.</div></div>';
}

function drawWall(x1, y1, x2, y2) {
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
}

function drawCharacter(x, y, cellSize, offsetX, offsetY, color) {
  const cx = offsetX + x * cellSize + cellSize / 2;
  const cy = offsetY + y * cellSize + cellSize / 2;
  const radius = cellSize * 0.26;
  const gradient = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.2, cx, cy, radius * 1.4);
  gradient.addColorStop(0, color);
  gradient.addColorStop(1, '#0b1220');
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawMarker(x, y, cellSize, offsetX, offsetY, color, label) {
  const cx = offsetX + x * cellSize + cellSize / 2;
  const cy = offsetY + y * cellSize + cellSize / 2;
  const radius = cellSize * 0.23;
  ctx.save();
  ctx.fillStyle = color;
  ctx.shadowColor = color;
  ctx.shadowBlur = 18;
  ctx.beginPath();
  ctx.moveTo(cx, cy - radius);
  for (let step = 0; step < 5; step += 1) {
    const outerAngle = -Math.PI / 2 + step * (Math.PI * 2 / 5);
    const innerAngle = outerAngle + Math.PI / 5;
    ctx.lineTo(cx + Math.cos(outerAngle) * radius, cy + Math.sin(outerAngle) * radius);
    ctx.lineTo(cx + Math.cos(innerAngle) * radius * 0.45, cy + Math.sin(innerAngle) * radius * 0.45);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();
  ctx.fillStyle = 'rgba(11, 18, 32, 0.85)';
  ctx.font = 'bold 12px Trebuchet MS';
  ctx.textAlign = 'center';
  ctx.fillText(label, cx, cy + radius + 16);
}

function directionLabel(direction) {
  return {
    N: 'North',
    S: 'South',
    E: 'East',
    W: 'West',
  }[direction] || direction;
}

document.addEventListener('keydown', (event) => {
  const direction = directionToKey[event.key];
  if (!direction) {
    return;
  }
  event.preventDefault();
  sendMove(direction);
});

newGameBtn.addEventListener('click', startNewGame);

difficultyButtons.forEach((button) => {
  button.addEventListener('click', () => {
    activeDifficulty = button.dataset.difficulty;
    difficultyButtons.forEach((item) => item.classList.toggle('active', item === button));
    if (currentState) {
      startNewGame();
    }
  });
});

dpadButtons.forEach((button) => {
  button.addEventListener('click', () => sendMove(button.dataset.direction));
});

connect();