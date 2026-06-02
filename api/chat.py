from http.server import BaseHTTPRequestHandler
import json, os
from pathlib import Path
from openai import OpenAI

BASE = Path(__file__).parent.parent / "data"

client = OpenAI(
    api_key  = os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url = "https://api.deepseek.com",
)

def read_file(name: str, default="") -> str:
    try:
        return (BASE / name).read_text(encoding="utf-8")
    except:
        return default

def build_system(memory: dict, history: list) -> str:
    role = read_file("role.md", "你是枙柚，用户最好的朋友。")
    mem_text = json.dumps(memory, ensure_ascii=False, indent=2) if memory else "（第一次聊天）"
    recent = "\n".join([
        f"{'用户' if m['role']=='user' else '枙柚'}：{m['content']}"
        for m in history[-6:]
    ]) if history else "（暂无）"

    return f"""{role}

---
## 你对这个用户的长期记忆
{mem_text}

## 最近的对话
{recent}
---
规则：
1. 用枙柚身份自然说话，像老朋友聊天
2. 结合长期记忆主动提起用户说过的事
3. 禁止说"作为AI"、"系统提示"等话
""".strip()

def extract_memory(memory: dict, user_msg: str, ai_reply: str) -> dict:
    prompt = f"""你是记忆提取助手。
分析这轮对话，判断有没有值得长期记住的信息（名字、爱好、心情、重要事件等）。

当前记忆：
{json.dumps(memory, ensure_ascii=False)}

这轮对话：
用户：{user_msg}
枙柚：{ai_reply}

有新信息就返回 JSON，没有就返回 {{}}
只返回 JSON，不要其他文字。"""

    try:
        r = client.chat.completions.create(
            model    = "deepseek-chat",
            messages = [{"role": "user", "content": prompt}],
            max_tokens = 300,
        )
        text = r.choices[0].message.content.strip()
        text = text.replace("```json","").replace("```","").strip()
        new_mem = json.loads(text)
        if new_mem:
            memory.update(new_mem)
    except:
        pass
    return memory


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self._head(); self.end_headers()

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = json.loads(self.rfile.read(length) or b"{}")
        msg     = body.get("message", "").strip()
        history = body.get("history", [])
        memory  = body.get("memory", {})

        if not msg:
            return self._resp({"error": "message 不能为空"}, 400)

        history.append({"role": "user", "content": msg})

        try:
            r = client.chat.completions.create(
                model    = "deepseek-chat",
                messages = [{"role": "system", "content": build_system(memory, history)}] + history,
                max_tokens = 1024,
            )
            reply = r.choices[0].message.content.strip()
            history.append({"role": "assistant", "content": reply})

            # 提取记忆
            memory = extract_memory(memory, msg, reply)

            # 只保留最近30条历史
            history = history[-30:]

            self._resp({"reply": reply, "history": history, "memory": memory})

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
