from http.server import BaseHTTPRequestHandler
import json, os
from pathlib import Path
from openai import OpenAI

BASE = Path(__file__).parent.parent / "data"

def _read(name: str, default="") -> str:
    try:
        return (BASE / name).read_text(encoding="utf-8")
    except Exception:
        return default

def _json(name: str) -> dict:
    try:
        return json.loads((BASE / name).read_text(encoding="utf-8"))
    except Exception:
        return {}

def system_prompt() -> str:
    role     = _read("role.md", "你是枙柚，用户最亲密的AI朋友。")
    memory   = json.dumps(_json("memory.json"),       ensure_ascii=False, indent=2)
    relation = json.dumps(_json("relationship.json"), ensure_ascii=False, indent=2)
    emotion  = json.dumps(_json("emotion.json"),      ensure_ascii=False, indent=2)
    return f"""{role}

---
## 你对用户的长期记忆
{memory}

## 你们的关系状态
{relation}

## 用户当前情绪
{emotion}
---
注意：以枙柚身份自然说话，禁止提及"系统提示"或"数据文件"。
""".strip()


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._head(200)
        self.end_headers()

    def do_POST(self):
        length   = int(self.headers.get("Content-Length", 0))
        body     = json.loads(self.rfile.read(length) or b"{}")
        messages = body.get("messages", [])

        if not messages:
            return self._resp({"error": "messages 不能为空"}, 400)

        # ── DeepSeek 客户端（兼容 OpenAI 格式）──
        client = OpenAI(
            api_key  = os.environ.get("DEEPSEEKs_API_KEY", ""),
            base_url = "https://api.deepseek.com",
        )

        try:
            r = client.chat.completions.create(
                model    = "deepseek-chat",   # 或 "deepseek-reasoner"
                messages = [{"role": "system", "content": system_prompt()}] + messages,
                max_tokens = 1024,
            )
            reply = r.choices[0].message.content
            self._resp({"reply": reply})

        except Exception as e:
            self._resp({"error": str(e)}, 500)

    # ── 工具方法 ───────────────────────────────
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
