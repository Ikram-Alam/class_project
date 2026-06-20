/* ═══════════════════════════════════════════════════════════════════
   Dungeon Crawler AI  –  app.js
   Connects via WebSocket, renders the maze on Canvas, shows AI trace.
═══════════════════════════════════════════════════════════════════ */

const canvas        = document.getElementById('gameCanvas');
const ctx           = canvas.getContext('2d');

const statusPill    = document.getElementById('statusPill');
const statusMessage = document.getElementById('statusMessage');
const turnValue     = document.getElementById('turnValue');
const diffValue     = document.getElementById('difficultyValue');
const stateValue    = document.getElementById('gameStateValue');
const lastMoveValue = document.getElementById('lastMoveValue');
const freezeValue   = document.getElementById('freezeValue');
const freezeRow     = document.getElementById('freezeRow');
const stepsValue    = document.getElementById('stepsValue');
const aiDepthValue  = document.getElementById('aiDepthValue');
const aiNodesValue  = document.getElementById('aiNodesValue');
const aiPrunedValue = document.getElementById('aiPrunedValue');
const aiTrace       = document.getElementById('aiTrace');
const newGameBtn    = document.getElementById('newGameBtn');
const overlay       = document.getElementById('overlay');
const overlayTitle  = document.getElementById('overlayTitle');
const overlayMsg    = document.getElementById('overlayMsg');
const overlayBtn    = document.getElementById('overlayBtn');

const diffBtns  = [...document.querySelectorAll('[data-difficulty]')];
const dpadBtns  = [...document.querySelectorAll('.dpad [data-direction]')];

const KEY_MAP = {
  ArrowUp:'N', ArrowDown:'S', ArrowLeft:'W', ArrowRight:'E',
  w:'N', s:'S', a:'W', d:'E',
  W:'N', S:'S', A:'W', D:'E',
};
const DIR_LABEL = { N:'North', S:'South', E:'East', W:'West' };

let socket;
let state = null;
let activeDiff = 'easy';

// ── WebSocket ────────────────────────────────────────────────────────
function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  socket = new WebSocket(`${proto}://${location.host}/ws`);

  socket.addEventListener('open', () => {
    statusPill.textContent  = '● Connected';
    statusPill.className    = 'status-pill connected';
    // Start a game matching the highlighted difficulty so the UI and server
    // never disagree about which difficulty is in play.
    send({ type: 'new_game', difficulty: activeDiff });
  });
  socket.addEventListener('close', () => {
    statusPill.textContent  = '○ Disconnected';
    statusPill.className    = 'status-pill disconnected';
    statusMessage.textContent = 'Connection dropped. Refresh to reconnect.';
  });
  socket.addEventListener('message', e => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'state') { state = msg.state; render(); }
  });
}

function send(payload) {
  if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(payload));
}

function sendMove(dir) {
  if (!state || state.status !== 'playing') return;
  send({ type: 'move', direction: dir });
}

function startNewGame() {
  overlay.classList.add('hidden');
  send({ type: 'new_game', difficulty: activeDiff });
}

// ── Render ───────────────────────────────────────────────────────────
function render() {
  if (!state) return;

  // responsive canvas
  const maxSz = Math.min(canvas.parentElement.clientWidth - 8, 680);
  if (canvas.width !== maxSz) { canvas.width = maxSz; canvas.height = maxSz; }

  const { maze, player, enemy, exit: ex, ai } = state;
  const cell   = Math.floor(Math.min(canvas.width / maze.width, canvas.height / maze.height));
  const bw     = cell * maze.width;
  const bh     = cell * maze.height;
  const ox     = Math.floor((canvas.width  - bw) / 2);
  const oy     = Math.floor((canvas.height - bh) / 2);

  // clear + background
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const bg = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  bg.addColorStop(0, '#0b1220'); bg.addColorStop(1, '#111827');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // floor tiles
  for (let y = 0; y < maze.height; y++)
    for (let x = 0; x < maze.width; x++) {
      ctx.fillStyle = 'rgba(255,255,255,0.025)';
      ctx.fillRect(ox + x*cell + 1, oy + y*cell + 1, cell - 2, cell - 2);
    }

  // walls
  ctx.strokeStyle = 'rgba(148,163,184,0.4)';
  ctx.lineWidth   = Math.max(1.5, cell * 0.07);
  ctx.lineCap     = 'square';
  ctx.beginPath();
  for (let y = 0; y < maze.height; y++)
    for (let x = 0; x < maze.width; x++) {
      const c = maze.cells[y][x];
      const px = ox + x*cell, py = oy + y*cell;
      if (c.N) { ctx.moveTo(px, py);        ctx.lineTo(px+cell, py); }
      if (c.S) { ctx.moveTo(px, py+cell);   ctx.lineTo(px+cell, py+cell); }
      if (c.W) { ctx.moveTo(px, py);        ctx.lineTo(px, py+cell); }
      if (c.E) { ctx.moveTo(px+cell, py);   ctx.lineTo(px+cell, py+cell); }
    }
  ctx.stroke();

  // exit star
  drawStar(ex.x, ex.y, cell, ox, oy);

  // enemy (draw before player so player always shows on top)
  const frozen = (state.frozen_turns ?? 0) > 0;
  drawCircle(enemy.x, enemy.y, cell, ox, oy,
    frozen ? '#94a3b8' : '#f87171',
    frozen ? '#334155' : '#7f1d1d');

  // player
  drawCircle(player.x, player.y, cell, ox, oy, '#60a5fa', '#1e3a8a');

  // ── Sidebar ─────────────────────────────────────────────────────────
  statusMessage.textContent = state.message;
  turnValue.textContent     = String(state.turn);
  diffValue.textContent     = cap(state.difficulty);
  stateValue.textContent    = cap(state.status);
  stepsValue.textContent    = `${state.player_steps ?? 1}×`;
  lastMoveValue.textContent =
    state.lastEnemyMove  ? `Enemy: ${DIR_LABEL[state.lastEnemyMove]}`
    : state.lastPlayerMove ? `You: ${DIR_LABEL[state.lastPlayerMove]}`
    : 'None';

  const ft = state.frozen_turns ?? 0;
  if (ft > 0) {
    freezeRow.style.display = '';
    freezeValue.textContent = `${ft} turn${ft !== 1 ? 's' : ''}`;
  } else {
    freezeRow.style.display = 'none';
  }

  const trace      = Array.isArray(ai?.trace) ? ai.trace : [];
  const totalNodes  = trace.reduce((s,i) => s + i.nodes,  0);
  const totalPruned = trace.reduce((s,i) => s + i.pruned, 0);
  aiDepthValue.textContent  = String(ai?.depth ?? '—');
  aiNodesValue.textContent  = String(totalNodes);
  aiPrunedValue.textContent = String(totalPruned);

  const sorted = [...trace].sort((a,b) => a.score - b.score);
  aiTrace.innerHTML = sorted.length
    ? sorted.map((item, i) => `
        <div class="trace-item ${i===0?'best':''}">
          <strong>${DIR_LABEL[item.direction]||item.direction}
            → (${item.target.x},${item.target.y})</strong>
          <div>Score:<span class="score">${item.score.toFixed(0)}</span>
            &nbsp;·&nbsp;Nodes:${item.nodes}
            &nbsp;·&nbsp;Pruned:${item.pruned}</div>
        </div>`).join('')
    : `<div class="trace-item"><strong>${frozen?'Enemy is frozen.':'No moves available.'}</strong></div>`;

  // overlay
  if (state.status === 'won' || state.status === 'lost') {
    overlayTitle.textContent = state.status === 'won' ? '🎉 Escaped!' : '💀 Caught!';
    overlayMsg.textContent   = state.status === 'won'
      ? `You escaped in ${state.turn} turns on ${state.difficulty}!`
      : `Caught on turn ${state.turn}. Try again!`;
    overlay.classList.remove('hidden');
  }
}

// ── Draw helpers ─────────────────────────────────────────────────────
function drawCircle(gx, gy, cell, ox, oy, outer, inner) {
  const cx = ox + gx*cell + cell/2;
  const cy = oy + gy*cell + cell/2;
  const r  = cell * 0.30;
  const g  = ctx.createRadialGradient(cx-r*0.3, cy-r*0.35, r*0.05, cx, cy, r);
  g.addColorStop(0, outer); g.addColorStop(1, inner);
  ctx.save();
  ctx.shadowColor = outer; ctx.shadowBlur = 14;
  ctx.fillStyle   = g;
  ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI*2); ctx.fill();
  ctx.strokeStyle = 'rgba(255,255,255,0.45)'; ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.restore();
}

function drawStar(gx, gy, cell, ox, oy) {
  const cx  = ox + gx*cell + cell/2;
  const cy  = oy + gy*cell + cell/2;
  const r   = cell * 0.28;
  const pts = 5;
  ctx.save();
  ctx.shadowColor = '#fbbf24'; ctx.shadowBlur = 22;
  ctx.fillStyle   = '#f7c948';
  ctx.beginPath();
  for (let i = 0; i < pts*2; i++) {
    const angle  = -Math.PI/2 + (i * Math.PI) / pts;
    const radius = i%2===0 ? r : r*0.42;
    const x = cx + Math.cos(angle)*radius;
    const y = cy + Math.sin(angle)*radius;
    i===0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
  }
  ctx.closePath(); ctx.fill();
  ctx.restore();
  ctx.fillStyle = '#fbbf24';
  ctx.font      = `bold ${Math.max(8, Math.round(cell*0.20))}px monospace`;
  ctx.textAlign = 'center';
  ctx.fillText('EXIT', cx, cy + r + Math.round(cell*0.22));
}

function cap(s) { return s ? s.charAt(0).toUpperCase()+s.slice(1) : '—'; }

// ── Input ─────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  const dir = KEY_MAP[e.key];
  if (!dir) return;
  e.preventDefault();
  sendMove(dir);
});

newGameBtn.addEventListener('click', startNewGame);
overlayBtn.addEventListener('click', startNewGame);

diffBtns.forEach(btn => btn.addEventListener('click', () => {
  activeDiff = btn.dataset.difficulty;
  diffBtns.forEach(b => b.classList.toggle('active', b===btn));
  startNewGame();
}));

dpadBtns.forEach(btn => btn.addEventListener('click', () => sendMove(btn.dataset.direction)));

window.addEventListener('resize', () => { if (state) render(); });

connect();