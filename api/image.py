from http.server import BaseHTTPRequestHandler
import json

# 未来：AI生成图片接口
# 可接入 Replicate / Stability AI / DALL-E 等

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "message": "图片生成功能即将上线 🎨",
            "status": "coming_soon"
        }, ensure_ascii=False).encode())

    def log_message(self, *args):
        pass
