// const canvas = document.getElementById('gameCanvas');
// const ctx = canvas.getContext('2d');

// const statusPill = document.getElementById('statusPill');
// const statusMessage = document.getElementById('statusMessage');
// const turnValue = document.getElementById('turnValue');
// const difficultyValue = document.getElementById('difficultyValue');
// const gameStateValue = document.getElementById('gameStateValue');
// const lastMoveValue = document.getElementById('lastMoveValue');
// const aiDepthValue = document.getElementById('aiDepthValue');
// const aiPrunedValue = document.getElementById('aiPrunedValue');
// const aiNodesValue = document.getElementById('aiNodesValue');
// const aiTrace = document.getElementById('aiTrace');
// const newGameBtn = document.getElementById('newGameBtn');
// const difficultyButtons = Array.from(document.querySelectorAll('[data-difficulty]'));
// const dpadButtons = Array.from(document.querySelectorAll('.dpad [data-direction]'));

// const directionToKey = {
//   ArrowUp: 'N',
//   ArrowDown: 'S',
//   ArrowLeft: 'W',
//   ArrowRight: 'E',
//   w: 'N',
//   s: 'S',
//   a: 'W',
//   d: 'E',
//   W: 'N',
//   S: 'S',
//   A: 'W',
//   D: 'E',
// };

// let socket;
// let currentState = null;
// let activeDifficulty = 'easy';

// function connect() {
//   socket = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`);

//   socket.addEventListener('open', () => {
//     statusPill.textContent = 'Connected';
//   });

//   socket.addEventListener('close', () => {
//     statusPill.textContent = 'Disconnected';
//     statusMessage.textContent = 'The connection dropped. Refresh the page to reconnect.';
//   });

//   socket.addEventListener('message', (event) => {
//     const payload = JSON.parse(event.data);
//     if (payload.type === 'state') {
//       currentState = payload.state;
//       renderState();
//     }
//   });
// }

// function send(payload) {
//   if (socket && socket.readyState === WebSocket.OPEN) {
//     socket.send(JSON.stringify(payload));
//   }
// }

// function sendMove(direction) {
//   if (!currentState || currentState.status !== 'playing') {
//     return;
//   }
//   send({ type: 'move', direction });
// }

// function startNewGame() {
//   send({ type: 'new_game', difficulty: activeDifficulty });
// }

// function renderState() {
//   if (!currentState) {
//     return;
//   }

//   const { maze, player, enemy, exit, ai } = currentState;
//   const cellSize = Math.floor(Math.min(canvas.width / maze.width, canvas.height / maze.height));
//   const boardWidth = cellSize * maze.width;
//   const boardHeight = cellSize * maze.height;
//   const offsetX = Math.floor((canvas.width - boardWidth) / 2);
//   const offsetY = Math.floor((canvas.height - boardHeight) / 2);

//   ctx.clearRect(0, 0, canvas.width, canvas.height);

//   const background = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
//   background.addColorStop(0, '#0b1220');
//   background.addColorStop(1, '#0e1728');
//   ctx.fillStyle = background;
//   ctx.fillRect(0, 0, canvas.width, canvas.height);

//   ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
//   for (let y = 0; y < maze.height; y += 1) {
//     for (let x = 0; x < maze.width; x += 1) {
//       ctx.fillRect(offsetX + x * cellSize, offsetY + y * cellSize, cellSize - 1, cellSize - 1);
//     }
//   }

//   ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
//   ctx.lineWidth = Math.max(2, Math.floor(cellSize * 0.1));
//   ctx.lineCap = 'round';

//   for (let y = 0; y < maze.height; y += 1) {
//     for (let x = 0; x < maze.width; x += 1) {
//       const cell = maze.cells[y][x];
//       const px = offsetX + x * cellSize;
//       const py = offsetY + y * cellSize;

//       if (cell.N) {
//         drawWall(px, py, px + cellSize, py);
//       }
//       if (cell.S) {
//         drawWall(px, py + cellSize, px + cellSize, py + cellSize);
//       }
//       if (cell.W) {
//         drawWall(px, py, px, py + cellSize);
//       }
//       if (cell.E) {
//         drawWall(px + cellSize, py, px + cellSize, py + cellSize);
//       }
//     }
//   }

//   drawMarker(exit.x, exit.y, cellSize, offsetX, offsetY, '#f7c948', 'EXIT');
//   drawCharacter(player.x, player.y, cellSize, offsetX, offsetY, '#60a5fa');
//   drawCharacter(enemy.x, enemy.y, cellSize, offsetX, offsetY, '#f87171');

//   statusMessage.textContent = currentState.message;
//   turnValue.textContent = String(currentState.turn);
//   difficultyValue.textContent = currentState.difficulty.charAt(0).toUpperCase() + currentState.difficulty.slice(1);
//   gameStateValue.textContent = currentState.status.charAt(0).toUpperCase() + currentState.status.slice(1);
//   lastMoveValue.textContent = currentState.lastEnemyMove || currentState.lastPlayerMove || 'None';
//   aiDepthValue.textContent = String(ai.depth);

//   const trace = Array.isArray(ai.trace) ? ai.trace : [];
//   const totalPruned = trace.reduce((sum, item) => sum + item.pruned, 0);
//   const totalNodes = trace.reduce((sum, item) => sum + item.nodes, 0);
//   aiPrunedValue.textContent = String(totalPruned);
//   aiNodesValue.textContent = String(totalNodes);

//   const sortedTrace = [...trace].sort((a, b) => a.score - b.score);
//   aiTrace.innerHTML = sortedTrace.map((item, index) => `
//     <div class="trace-item ${index === 0 ? 'best' : ''}">
//       <strong>${directionLabel(item.direction)} to (${item.target.x}, ${item.target.y})</strong>
//       <div>Score: <span class="score">${item.score.toFixed(1)}</span> | Nodes: ${item.nodes} | Pruned: ${item.pruned}</div>
//     </div>
//   `).join('') || '<div class="trace-item"><strong>No available enemy moves</strong><div>The enemy is trapped.</div></div>';
// }

// function drawWall(x1, y1, x2, y2) {
//   ctx.beginPath();
//   ctx.moveTo(x1, y1);
//   ctx.lineTo(x2, y2);
//   ctx.stroke();
// }

// function drawCharacter(x, y, cellSize, offsetX, offsetY, color) {
//   const cx = offsetX + x * cellSize + cellSize / 2;
//   const cy = offsetY + y * cellSize + cellSize / 2;
//   const radius = cellSize * 0.26;
//   const gradient = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.2, cx, cy, radius * 1.4);
//   gradient.addColorStop(0, color);
//   gradient.addColorStop(1, '#0b1220');
//   ctx.fillStyle = gradient;
//   ctx.beginPath();
//   ctx.arc(cx, cy, radius, 0, Math.PI * 2);
//   ctx.fill();
//   ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
//   ctx.lineWidth = 2;
//   ctx.stroke();
// }

// function drawMarker(x, y, cellSize, offsetX, offsetY, color, label) {
//   const cx = offsetX + x * cellSize + cellSize / 2;
//   const cy = offsetY + y * cellSize + cellSize / 2;
//   const radius = cellSize * 0.23;
//   ctx.save();
//   ctx.fillStyle = color;
//   ctx.shadowColor = color;
//   ctx.shadowBlur = 18;
//   ctx.beginPath();
//   ctx.moveTo(cx, cy - radius);
//   for (let step = 0; step < 5; step += 1) {
//     const outerAngle = -Math.PI / 2 + step * (Math.PI * 2 / 5);
//     const innerAngle = outerAngle + Math.PI / 5;
//     ctx.lineTo(cx + Math.cos(outerAngle) * radius, cy + Math.sin(outerAngle) * radius);
//     ctx.lineTo(cx + Math.cos(innerAngle) * radius * 0.45, cy + Math.sin(innerAngle) * radius * 0.45);
//   }
//   ctx.closePath();
//   ctx.fill();
//   ctx.restore();
//   ctx.fillStyle = 'rgba(11, 18, 32, 0.85)';
//   ctx.font = 'bold 12px Trebuchet MS';
//   ctx.textAlign = 'center';
//   ctx.fillText(label, cx, cy + radius + 16);
// }

// function directionLabel(direction) {
//   return {
//     N: 'North',
//     S: 'South',
//     E: 'East',
//     W: 'West',
//   }[direction] || direction;
// }

// document.addEventListener('keydown', (event) => {
//   const direction = directionToKey[event.key];
//   if (!direction) {
//     return;
//   }
//   event.preventDefault();
//   sendMove(direction);
// });

// newGameBtn.addEventListener('click', startNewGame);

// difficultyButtons.forEach((button) => {
//   button.addEventListener('click', () => {
//     activeDifficulty = button.dataset.difficulty;
//     difficultyButtons.forEach((item) => item.classList.toggle('active', item === button));
//     if (currentState) {
//       startNewGame();
//     }
//   });
// });

// dpadButtons.forEach((button) => {
//   button.addEventListener('click', () => sendMove(button.dataset.direction));
// });

// connect();




const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

const statusPill       = document.getElementById('statusPill');
const statusMessage    = document.getElementById('statusMessage');
const turnValue        = document.getElementById('turnValue');
const difficultyValue  = document.getElementById('difficultyValue');
const gameStateValue   = document.getElementById('gameStateValue');
const lastMoveValue    = document.getElementById('lastMoveValue');
const aiDepthValue     = document.getElementById('aiDepthValue');
const aiPrunedValue    = document.getElementById('aiPrunedValue');
const aiNodesValue     = document.getElementById('aiNodesValue');
const aiTrace          = document.getElementById('aiTrace');
const newGameBtn       = document.getElementById('newGameBtn');
const overlay          = document.getElementById('overlay');
const overlayTitle     = document.getElementById('overlayTitle');
const overlayMsg       = document.getElementById('overlayMsg');
const overlayBtn       = document.getElementById('overlayBtn');

const difficultyButtons = Array.from(document.querySelectorAll('[data-difficulty]'));
const dpadButtons       = Array.from(document.querySelectorAll('.dpad [data-direction]'));

const KEY_MAP = {
  ArrowUp: 'N', ArrowDown: 'S', ArrowLeft: 'W', ArrowRight: 'E',
  w: 'N', s: 'S', a: 'W', d: 'E',
  W: 'N', S: 'S', A: 'W', D: 'E',
};

const DIR_LABEL = { N: 'North', S: 'South', E: 'East', W: 'West' };

let socket;
let currentState    = null;
let activeDifficulty = 'easy';
let animFrame       = null;

// ── WebSocket ──────────────────────────────────────────────────────────
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  socket = new WebSocket(`${proto}://${location.host}/ws`);

  socket.addEventListener('open', () => {
    statusPill.textContent = 'Connected';
    statusPill.className = 'status-pill connected';
  });
  socket.addEventListener('close', () => {
    statusPill.textContent = 'Disconnected';
    statusPill.className = 'status-pill disconnected';
    statusMessage.textContent = 'Connection dropped. Refresh to reconnect.';
  });
  socket.addEventListener('message', (e) => {
    const payload = JSON.parse(e.data);
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

function sendMove(dir) {
  if (!currentState || currentState.status !== 'playing') return;
  send({ type: 'move', direction: dir });
}

function startNewGame() {
  overlay.classList.add('hidden');
  send({ type: 'new_game', difficulty: activeDifficulty });
}

// ── Render ─────────────────────────────────────────────────────────────
function renderState() {
  if (!currentState) return;

  const { maze, player, enemy, exit: exitPos, ai, status } = currentState;

  // Responsive canvas sizing
  const maxSize = Math.min(canvas.parentElement.clientWidth - 16, 700);
  canvas.width  = maxSize;
  canvas.height = maxSize;

  const cellSize  = Math.floor(Math.min(canvas.width / maze.width, canvas.height / maze.height));
  const boardW    = cellSize * maze.width;
  const boardH    = cellSize * maze.height;
  const offX      = Math.floor((canvas.width  - boardW) / 2);
  const offY      = Math.floor((canvas.height - boardH) / 2);

  // Background
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const bg = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  bg.addColorStop(0, '#0b1220');
  bg.addColorStop(1, '#111827');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Cell floors
  for (let y = 0; y < maze.height; y++) {
    for (let x = 0; x < maze.width; x++) {
      ctx.fillStyle = 'rgba(255,255,255,0.03)';
      ctx.fillRect(offX + x * cellSize + 1, offY + y * cellSize + 1, cellSize - 2, cellSize - 2);
    }
  }

  // Walls
  ctx.strokeStyle = 'rgba(148,163,184,0.35)';
  ctx.lineWidth   = Math.max(2, Math.round(cellSize * 0.08));
  ctx.lineCap     = 'square';

  for (let y = 0; y < maze.height; y++) {
    for (let x = 0; x < maze.width; x++) {
      const cell = maze.cells[y][x];
      const px   = offX + x * cellSize;
      const py   = offY + y * cellSize;

      ctx.beginPath();
      if (cell.N) { ctx.moveTo(px, py);             ctx.lineTo(px + cellSize, py); }
      if (cell.S) { ctx.moveTo(px, py + cellSize);  ctx.lineTo(px + cellSize, py + cellSize); }
      if (cell.W) { ctx.moveTo(px, py);             ctx.lineTo(px, py + cellSize); }
      if (cell.E) { ctx.moveTo(px + cellSize, py);  ctx.lineTo(px + cellSize, py + cellSize); }
      ctx.stroke();
    }
  }

  // Exit star
  drawStar(exitPos.x, exitPos.y, cellSize, offX, offY);

  // Player (blue circle)
  drawCircle(player.x, player.y, cellSize, offX, offY, '#60a5fa', '#1d4ed8');

  // Enemy (red circle) — draw on top so it's always visible
  drawCircle(enemy.x, enemy.y, cellSize, offX, offY, '#f87171', '#991b1b');

  // ── Sidebar ──
  statusMessage.textContent = currentState.message;
  turnValue.textContent      = String(currentState.turn);
  difficultyValue.textContent = currentState.difficulty.charAt(0).toUpperCase() + currentState.difficulty.slice(1);
  gameStateValue.textContent  = status.charAt(0).toUpperCase() + status.slice(1);
  lastMoveValue.textContent   = (currentState.lastEnemyMove
    ? `Enemy: ${DIR_LABEL[currentState.lastEnemyMove]}`
    : (currentState.lastPlayerMove ? `You: ${DIR_LABEL[currentState.lastPlayerMove]}` : 'None'));

  const trace      = Array.isArray(ai.trace) ? ai.trace : [];
  const totalNodes  = trace.reduce((s, i) => s + i.nodes,  0);
  const totalPruned = trace.reduce((s, i) => s + i.pruned, 0);
  aiDepthValue.textContent  = String(ai.depth);
  aiNodesValue.textContent  = String(totalNodes);
  aiPrunedValue.textContent = String(totalPruned);

  const sorted = [...trace].sort((a, b) => a.score - b.score);
  aiTrace.innerHTML = sorted.length
    ? sorted.map((item, i) => `
        <div class="trace-item ${i === 0 ? 'best' : ''}">
          <strong>${DIR_LABEL[item.direction] || item.direction}
            → (${item.target.x}, ${item.target.y})</strong>
          <div>Score: <span class="score">${item.score.toFixed(1)}</span>
            &nbsp;·&nbsp; Nodes: ${item.nodes}
            &nbsp;·&nbsp; Pruned: ${item.pruned}</div>
        </div>`).join('')
    : '<div class="trace-item"><strong>Enemy has no moves.</strong></div>';

  // Win / loss overlay
  if (status === 'won' || status === 'lost') {
    overlayTitle.textContent = status === 'won' ? '🎉 You Escaped!' : '💀 Caught!';
    overlayMsg.textContent   = status === 'won'
      ? `Escaped in ${currentState.turn} turns on ${currentState.difficulty}.`
      : `The enemy caught you on turn ${currentState.turn}.`;
    overlay.classList.remove('hidden');
  }
}

function drawCircle(gx, gy, cellSize, offX, offY, colorOuter, colorInner) {
  const cx = offX + gx * cellSize + cellSize / 2;
  const cy = offY + gy * cellSize + cellSize / 2;
  const r  = cellSize * 0.32;

  const grad = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 0.1, cx, cy, r);
  grad.addColorStop(0, colorOuter);
  grad.addColorStop(1, colorInner);

  ctx.save();
  ctx.shadowColor = colorOuter;
  ctx.shadowBlur  = 12;
  ctx.fillStyle   = grad;
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = 'rgba(255,255,255,0.5)';
  ctx.lineWidth   = 1.5;
  ctx.stroke();
  ctx.restore();
}

function drawStar(gx, gy, cellSize, offX, offY) {
  const cx = offX + gx * cellSize + cellSize / 2;
  const cy = offY + gy * cellSize + cellSize / 2;
  const r  = cellSize * 0.30;
  const ir = r * 0.42;
  const pts = 5;

  ctx.save();
  ctx.shadowColor = '#fbbf24';
  ctx.shadowBlur  = 20;
  ctx.fillStyle   = '#f7c948';
  ctx.beginPath();
  for (let i = 0; i < pts * 2; i++) {
    const angle  = -Math.PI / 2 + (i * Math.PI) / pts;
    const radius = i % 2 === 0 ? r : ir;
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius;
    i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fill();
  ctx.restore();

  // "EXIT" label below star
  ctx.fillStyle = '#fbbf24';
  ctx.font      = `bold ${Math.max(9, Math.round(cellSize * 0.22))}px monospace`;
  ctx.textAlign = 'center';
  ctx.fillText('EXIT', cx, cy + r + Math.round(cellSize * 0.22));
}

// ── Input ──────────────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
  const dir = KEY_MAP[e.key];
  if (!dir) return;
  e.preventDefault();
  sendMove(dir);
});

newGameBtn.addEventListener('click', startNewGame);
overlayBtn.addEventListener('click', startNewGame);

difficultyButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    activeDifficulty = btn.dataset.difficulty;
    difficultyButtons.forEach((b) => b.classList.toggle('active', b === btn));
    startNewGame();
  });
});

dpadButtons.forEach((btn) => {
  btn.addEventListener('click', () => sendMove(btn.dataset.direction));
});

window.addEventListener('resize', () => { if (currentState) renderState(); });

connect();