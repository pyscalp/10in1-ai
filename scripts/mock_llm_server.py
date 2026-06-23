"""Tiny OpenAI-compatible mock LLM server for local smoke tests."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/v1/models":
            self._send_json(200, {"data": [{"id": "mock-model"}]})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                req = json.loads(body)
            except json.JSONDecodeError:
                self._send_json(400, {"error": "invalid json"})
                return
            content = (
                "This is a mock answer from the local LLM server. "
                "Context received: "
                + req.get("messages", [{}])[-1].get("content", "")[:200]
            )
            self._send_json(
                200,
                {
                    "id": "mock-chatcmpl",
                    "object": "chat.completion",
                    "model": req.get("model", "mock-model"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                },
            )
        else:
            self._send_json(404, {"error": "not found"})


def main():
    host = os.getenv("MOCK_LLM_HOST", "127.0.0.1")
    port = int(os.getenv("MOCK_LLM_PORT", "8001"))
    server = HTTPServer((host, port), _Handler)
    print(f"Mock LLM server listening on http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
