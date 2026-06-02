/* 枙柚 · app.js v4 — 本地存储版 */

// ── 本地存储读写 ──────────────────────────────
function saveLocal(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch(e) {}
}
function loadLocal(key, def) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : def;
  } catch(e) { return def; }
}

// ── 状态（从本地读取）────────────────────────
let history = loadLocal('zhiyou_history', []);
let memory  = loadLocal('zhiyou_memory',  {});
let sending = false;

const chatEl   = document.getElementById('chat-messages');
const inputEl  = document.getElementById('user-input');
const sendBtn  = document.getElementById('send-btn');
const iconMic  = document.getElementById('icon-mic');
const iconSend = document.getElementById('icon-send');

// ── 日期 ─────────────────────────────────────
(function() {
  const el = document.getElementById('today-date');
  if (!el) return;
  const d = new Date();
  el.textContent = `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`;
})();

// ── 启动时恢复历史消息 ────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  if (history.length > 0) {
    // 恢复最近的聊天记录显示
    history.forEach(m => {
      appendBubble(m.role === 'user' ? 'out' : 'in', m.content, '');
    });
  } else {
    // 第一次打开
    setTimeout(() => appendBubble('in', '你好呀 🌿', now()), 500);
    setTimeout(() => appendBubble('in', '今天过得怎么样？', now()), 1000);
  }
});

// ── 输入框 ────────────────────────────────────
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
  const hasText = inputEl.value.trim().length > 0;
  iconMic.style.display  = hasText ? 'none'  : 'block';
  iconSend.style.display = hasText ? 'block' : 'none';
});

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});
sendBtn.addEventListener('click', () => { if (inputEl.value.trim()) send(); });

// ── 发送 ──────────────────────────────────────
async function send() {
  if (sending) return;
  const text = inputEl.value.trim();
  if (!text) return;

  sending = true;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  iconMic.style.display  = 'block';
  iconSend.style.display = 'none';

  appendBubble('out', text, now());
  const typingRow = showTyping();

  try {
    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ message: text, history, memory })
    });
    const data = await res.json();
    removeTyping(typingRow);

    if (data.error) {
      appendBubble('in', '出了点小问题，稍后再试试吧 🌿', now());
    } else {
      appendBubble('in', data.reply, now());
      // 更新本地存储
      history = data.history;
      memory  = data.memory;
      saveLocal('zhiyou_history', history);
      saveLocal('zhiyou_memory',  memory);
    }

  } catch(e) {
    removeTyping(typingRow);
    appendBubble('in', '网络好像有点问题，等一下再试试吧 🥺', now());
  }

  sending = false;
}

// ── 气泡 ──────────────────────────────────────
function appendBubble(dir, content, time) {
  const row = document.createElement('div');
  row.className = `msg-row ${dir}`;

  const avatar = document.createElement('div');
  avatar.className = 'msg-mini-avatar';
  if (dir === 'in') avatar.textContent = '枙';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  const span = document.createElement('span');
  span.textContent = content;
  bubble.appendChild(span);

  const meta = document.createElement('div');
  meta.className = 'bubble-meta';
  meta.innerHTML = `
    <span class="bubble-time">${time}</span>
    ${dir === 'out' ? `<span class="read-tick">
      <svg viewBox="0 0 16 16" fill="none">
        <path d="M2.5 8.5l3 3 3-3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M6.5 11.5l5-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9.5 8.5l2-2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>` : ''}
  `;
  bubble.appendChild(meta);

  if (dir === 'in') { row.appendChild(avatar); row.appendChild(bubble); }
  else { row.appendChild(bubble); }

  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;
}

// ── 打字动画 ──────────────────────────────────
function showTyping() {
  const row = document.createElement('div');
  row.className = 'msg-row in';
  const av = document.createElement('div');
  av.className = 'msg-mini-avatar';
  av.textContent = '枙';
  const bubble = document.createElement('div');
  bubble.className = 'typing-bubble';
  bubble.innerHTML = `<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>`;
  row.appendChild(av); row.appendChild(bubble);
  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;
  return row;
}
function removeTyping(el) { if (el?.parentNode) el.parentNode.removeChild(el); }

function now() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}
