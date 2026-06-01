/* ═══════════════════════════════════════════════
   枙柚 · 知友AI — app.js  v2
   Telegram 风格交互逻辑
═══════════════════════════════════════════════ */

// ── 状态 ─────────────────────────────────────
let history = [];   // 对话历史（发给后端）
let sending = false;

// ── DOM ──────────────────────────────────────
const chatEl   = document.getElementById('chat-messages');
const inputEl  = document.getElementById('user-input');
const sendBtn  = document.getElementById('send-btn');
const iconMic  = document.getElementById('icon-mic');
const iconSend = document.getElementById('icon-send');

// ── 日期药丸显示今天 ──────────────────────────
(function setDate() {
  const el = document.getElementById('today-date');
  if (!el) return;
  const d = new Date();
  el.textContent = `${d.getFullYear()}年${d.getMonth()+1}月${d.getDate()}日`;
})();

// ── 输入框：动态高度 + 图标切换 ──────────────
inputEl.addEventListener('input', () => {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
  const hasText = inputEl.value.trim().length > 0;
  iconMic.style.display  = hasText ? 'none'  : 'block';
  iconSend.style.display = hasText ? 'block' : 'none';
});

// ── 回车发送（Shift+Enter 换行）──────────────
inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
});

sendBtn.addEventListener('click', () => {
  if (inputEl.value.trim()) send();
});

// ── 发送消息 ─────────────────────────────────
async function send() {
  if (sending) return;
  const text = inputEl.value.trim();
  if (!text) return;

  sending = true;
  inputEl.value = '';
  inputEl.style.height = 'auto';
  iconMic.style.display  = 'block';
  iconSend.style.display = 'none';

  // 显示用户气泡
  appendBubble('out', text, now());

  // 加入对话历史
  history.push({ role: 'user', content: text });

  // 打字动画
  const typingRow = showTyping();

  try {
    const res  = await fetch('/api/chat', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ messages: history })
    });
    const data = await res.json();
    removeTyping(typingRow);

    const reply = data.reply || data.error || '出了点小问题，稍后再说话吧 🌿';
    appendBubble('in', reply, now());
    history.push({ role: 'assistant', content: reply });

  } catch (err) {
    removeTyping(typingRow);
    appendBubble('in', '网络好像有点问题，等一下再试试吧 🥺', now());
    console.error(err);
  }

  sending = false;
  scrollBottom();
}

// ── 渲染气泡 ─────────────────────────────────
// dir: 'in'（枙柚）| 'out'（用户）
// type: 'text'（默认）| 'image'
function appendBubble(dir, content, time, type = 'text') {
  const row = document.createElement('div');
  row.className = `msg-row ${dir}`;

  // 对方小头像
  const avatar = document.createElement('div');
  avatar.className = 'msg-mini-avatar';
  if (dir === 'in') avatar.textContent = '枙';

  // 气泡
  const bubble = document.createElement('div');
  bubble.className = type === 'image' ? 'bubble img-bubble' : 'bubble';

  if (type === 'image') {
    const img = document.createElement('img');
    img.src = content;
    img.alt = '图片';
    bubble.appendChild(img);
  } else {
    const textNode = document.createElement('span');
    textNode.textContent = content;
    bubble.appendChild(textNode);
  }

  // 时间 & 已读
  const meta = document.createElement('div');
  meta.className = 'bubble-meta';
  meta.innerHTML = `
    <span class="bubble-time">${time}</span>
    ${dir === 'out' ? `
    <span class="read-tick">
      <svg viewBox="0 0 16 16" fill="none">
        <path d="M2.5 8.5l3 3 3-3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M6.5 11.5l5-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M9.5 8.5l2-2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </span>` : ''}
  `;
  bubble.appendChild(meta);

  // 组装
  if (dir === 'in') {
    row.appendChild(avatar);
    row.appendChild(bubble);
  } else {
    row.appendChild(bubble);
  }

  chatEl.appendChild(row);
  scrollBottom();
}

// ── 打字动画 ─────────────────────────────────
function showTyping() {
  const row = document.createElement('div');
  row.className = 'msg-row in';
  row.id = 'typing-row';

  const av = document.createElement('div');
  av.className = 'msg-mini-avatar';
  av.textContent = '枙';

  const bubble = document.createElement('div');
  bubble.className = 'typing-bubble';
  bubble.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;

  row.appendChild(av);
  row.appendChild(bubble);
  chatEl.appendChild(row);
  scrollBottom();
  return row;
}

function removeTyping(el) {
  if (el?.parentNode) el.parentNode.removeChild(el);
}

// ── 工具 ─────────────────────────────────────
function now() {
  const d = new Date();
  return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

function scrollBottom() {
  chatEl.scrollTop = chatEl.scrollHeight;
}

// ── 开场消息 ─────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    appendBubble('in', '你好呀 🌿', '04:07');
  }, 500);
  setTimeout(() => {
    appendBubble('in', '今天过得怎么样？', '04:08');
  }, 1000);
});
