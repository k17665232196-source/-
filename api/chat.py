from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse
from pathlib import Path
from openai import OpenAI

BASE   = Path(__file__).parent.parent / "data"
UPSTASH_URL   = os.environ.get("UPSTASH_REDIS_REST_URL", "")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

client = OpenAI(
    api_key  = os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url = "https://api.deepseek.com",
)

# ── Upstash 操作 ──────────────────────────────
def redis_get(key: str):
    try:
        url = f"{UPSTASH_URL}/get/{urllib.parse.quote(key)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        res = urllib.request.urlopen(req, timeout=5)
        return json.loads(res.read()).get("result")
    except:
        return None

def redis_set(key: str, value: str, ex: int = 2592000):
    try:
        url  = f"{UPSTASH_URL}/set/{urllib.parse.quote(key)}/{urllib.parse.quote(value)}?ex={ex}"
        req  = urllib.request.Request(url, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
        urllib.request.urlopen(req, timeout=5)
    except:
        pass

# ── 读写记忆 ──────────────────────────────────
def load_memory(uid: str) -> dict:
    raw = redis_get(f"memory:{uid}")
    return json.loads(raw) if raw else {}

def save_memory(uid: str, memory: dict):
    redis_set(f"memory:{uid}", json.dumps(memory, ensure_ascii=False))

# ── 读写聊天历史 ──────────────────────────────
def load_history(uid: str) -> list:
    raw = redis_get(f"history:{uid}")
    return json.loads(raw) if raw else []

def save_history(uid: str, messages: list):
    # 只保留最近 30 条
    redis_set(f"history:{uid}", json.dumps(messages[-30:], ensure_ascii=False))

# ── 读取本地数据文件 ──────────────────────────
def read_file(name: str, default="") -> str:
    try:
        return (BASE / name).read_text(encoding="utf-8")
    except:
        return default

# ── 构建系统 Prompt ───────────────────────────
def build_system(uid: str) -> str:
    role    = read_file("role.md", "你是枙柚，用户最好的朋友。")
    memory  = load_memory(uid)
    history = load_history(uid)

    mem_text = json.dumps(memory, ensure_ascii=False, indent=2) if memory else "（还没有记忆，这是第一次聊天）"

    # 最近3条对话摘要注入
    recent = ""
    if history:
        recent = "\n".join([
            f"{'用户' if m['role']=='user' else '枙柚'}：{m['content']}"
            for m in history[-6:]
        ])

    return f"""{role}

---
## 你对这个用户的长期记忆
{mem_text}

## 最近的对话
{recent if recent else "（暂无）"}
---
规则：
1. 用枙柚的身份自然说话，像老朋友聊天
2. 结合长期记忆主动提起用户说过的事
3. 禁止说"作为AI"、"系统提示"等话
""".strip()

# ── 自动提取记忆 ──────────────────────────────
def extract_memory(uid: str, user_msg: str, ai_reply: str):
    """让 DeepSeek 判断这轮对话有没有值得记住的信息"""
    old_memory = load_memory(uid)

    extract_prompt = f"""你是一个记忆提取助手。
分析下面这轮对话，判断有没有值得长期记住的信息（比如用户的名字、爱好、心情、重要事件、偏好等）。

当前已有记忆：
{json.dumps(old_memory, ensure_ascii=False, indent=2)}

这轮对话：
用户说：{user_msg}
AI回复：{ai_reply}

如果有新信息需要记住，返回 JSON 格式（只返回 JSON，不要其他文字）：
{{"key": "value", "key2": "value2"}}

如果没有值得记住的，返回：
{{}}
"""
    try:
        r = client.chat.completions.create(
            model    = "deepseek-chat",
            messages = [{"role": "user", "content": extract_prompt}],
            max_tokens = 300,
        )
        text = r.choices[0].message.content.strip()
        # 清理可能的 markdown
        text = text.replace("```json", "").replace("```", "").strip()
        new_mem = json.loads(text)
        if new_mem:
            old_memory.update(new_mem)
            save_memory(uid, old_memory)
    except:
        pass

# ── 读写关系和情绪（每10轮更新一次）─────────────
def update_relationship(uid: str, history: list):
    if len(history) % 20 != 0:
        return
    rel = redis_get(f"relation:{uid}")
    rel = json.loads(rel) if rel else {"intimacy": 1, "stage": "新朋友", "total_msgs": 0}
    rel["total_msgs"] = len(history)
    if len(history) > 100:
        rel["intimacy"] = min(10, rel["intimacy"] + 0.5)
        rel["stage"] = "熟悉"
    if len(history) > 300:
        rel["stage"] = "亲密"
    redis_set(f"relation:{uid}", json.dumps(rel, ensure_ascii=False))

# ── Vercel Handler ────────────────────────────
class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._head(); self.end_headers()

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = json.loads(self.rfile.read(length) or b"{}")
        uid     = body.get("uid", "user_001")
        msg     = body.get("message", "").strip()

        if not msg:
            return self._resp({"error": "message 不能为空"}, 400)

        # 读历史
        history = load_history(uid)
        history.append({"role": "user", "content": msg})

        try:
            # 调 DeepSeek 回复
            r = client.chat.completions.create(
                model    = "deepseek-chat",
                messages = [{"role": "system", "content": build_system(uid)}] + history,
                max_tokens = 1024,
            )
            reply = r.choices[0].message.content.strip()

            # 保存历史
            history.append({"role": "assistant", "content": reply})
            save_history(uid, history)

            # 异步提取记忆（不影响回复速度，直接调用）
            extract_memory(uid, msg, reply)

            # 更新关系等级
            update_relationship(uid, history)

            self._resp({"reply": reply})

        except Exception as e:
            self._resp({"error": str(e)}, 500)

    def _head(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")

    def _resp(self, data, code=200):
        self._head(code)
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass
