from http.server import BaseHTTPRequestHandler, HTTPServer
import json

from engine_logic import start_quiz, apply_answer

HOST = "127.0.0.1"
PORT = 5055

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")

        try:
            payload = json.loads(raw) if raw else {}
        except:
            return self._send_json(400, {"error": "Invalid JSON"})

        # Route: POST /quiz/start
        if self.path == "/quiz/start":
            cards = payload.get("cards", [])
            if not isinstance(cards, list) or len(cards) == 0:
                return self._send_json(400, {"error": "cards must be a non-empty list"})
            state = start_quiz(cards)
            return self._send_json(200, {"state": state})

        # Route: POST /quiz/answer
        if self.path == "/quiz/answer":
            cards = payload.get("cards", [])
            state = payload.get("state", {})
            user_answer = payload.get("user_answer", "")

            if not isinstance(cards, list):
                return self._send_json(400, {"error": "cards must be a list"})
            if not isinstance(state, dict):
                return self._send_json(400, {"error": "state must be an object"})

            result = apply_answer(cards, state, str(user_answer))
            return self._send_json(200, result)

        return self._send_json(404, {"error": "Not found"})

def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Engine server running on http://{HOST}:{PORT}")
    server.serve_forever()

if __name__ == "__main__":
    main()
