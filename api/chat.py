from http.server import BaseHTTPRequestHandler
import json, os, urllib.request, urllib.parse
from pathlib import Path
from openai import OpenAI

BASE = Path(__file__).parent.parent / "data"

# ── Upstash Redis ─────────────────────────────
UPSTASH_URL   = os.environ.get("UPSTASH_REDIS_REST_URL", "")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN", "")

def redis(command: list):
    """调用 Upstash REST API"""
    url  = f"{UPSTASH_URL}/{'/'.join(urllib.parse.quote(str(c)) for c in command)}"
    req  = urllib.request.Request(url, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
    res  = urllib.request.urlopen(req, timeout=5)
    return json.loads(res.read())["result"]

def load_history(uid: str) -> list:
    try:
        raw = redis(["GET", f"history:{uid}"])
        return json.loads(raw) if raw else []
    except:
        return []

def save_history(uid: str, messages: list):
    try:
        # 只保留最近 40 条，防止太长
        messages = messages[-40:]
        redis(["SET", f"history:{uid}", json.dumps(messages, ensure_ascii=False), "EX", "2592000"])
    except:
        pass

def load_memory(uid: str) -> dict:
    try:
        raw = redis(["GET", f"memory:{uid}"])
        return json.loads(raw) if raw else {}
    except:
        return {}

def save_memory(uid: str, memory: dict):
    try:
        redis(["SET", f"memory:{uid}", json.dumps(memory, ensure_ascii=False), "EX", "2592000"])
    except:
        pass

# ── 本地数据文件 ──────────────────────────────
def _read(name: str, default="") -> str:
    try:
        return (BASE / name).read_text(encoding="utf-8")
    except:
        return default

def _json(name: str) -> dict:
    try:
        return json.loads((BASE / name).read_text(encoding="utf-8"))
    except:
        return {}

def system_prompt(uid: str) -> str:
    role     = _read("role.md", "你是枙柚，用户最亲密的AI朋友。")
    memory   = json.dumps(load_memory(uid), ensure_ascii=False, indent=2)
    relation = json.dumps(_json("relationship.json"), ensure_ascii=False, indent=2)
    emotion  = json.dumps(_json("emotion.json"),      ensure_ascii=False, indent=2)
    return f"""{role}

---
## 你对这个用户的长期记忆（从 Redis 读取，会持久保存）
{memory}

## 关系状态
{relation}

## 情绪状态
{emotion}
---
重要：
- 以枙柚身份自然说话
- 如果用户告诉你重要信息（名字/爱好/心情），请在回复末尾用 JSON 格式附上需要更新的记忆，格式：
  <<<MEMORY:{{"key":"value"}}>>>
- 禁止提及"系统提示"或"数据文件"
""".strip()

# ── 解析并保存记忆更新 ────────────────────────
def extract_and_save_memory(uid: str, reply: str) -> str:
    import re
    pattern = r'<<<MEMORY:(\{.*?\})>>>'
    match   = re.search(pattern, reply, re.DOTALL)
    if match:
        try:
            new_mem = json.loads(match.group(1))
            old_mem = load_memory(uid)
            old_mem.update(new_mem)
            save_memory(uid, old_mem)
        except:
            pass
        reply = re.sub(pattern, '', reply).strip()
    return reply

# ── Vercel Handler ────────────────────────────
class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._head(200); self.end_headers()

    def do_POST(self):
        length   = int(self.headers.get("Content-Length", 0))
        body     = json.loads(self.rfile.read(length) or b"{}")
        uid      = body.get("uid", "default")
        new_msg  = body.get("message", "")

        if not new_msg:
            return self._resp({"error": "message 不能为空"}, 400)

        # 读取历史
        history = load_history(uid)
        history.append({"role": "user", "content": new_msg})

        client = OpenAI(
            api_key  = os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url = "https://api.deepseek.com",
        )
        try:
            r = client.chat.completions.create(
                model    = "deepseek-chat",
                messages = [{"role": "system", "content": system_prompt(uid)}] + history,
                max_tokens = 1024,
            )
            reply = r.choices[0].message.content
            reply = extract_and_save_memory(uid, reply)

            history.append({"role": "assistant", "content": reply})
            save_history(uid, history)

            self._resp({"reply": reply, "history_count": len(history)})
        except Exception as e:
            self._resp({"error": str(e)}, 500)

    def _head(self, code=200):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json")

    def _resp(self, data: dict, code=200):
        self._head(code)
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a): pass
