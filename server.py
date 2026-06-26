from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import socket

HOST = "0.0.0.0"
PORT = 8000
HTML_PATH = os.path.join(os.path.dirname(__file__), "tv.html")


def get_local_ip():
    try:
        host_name = socket.gethostname()
        host_ips = socket.gethostbyname_ex(host_name)[2]
        for ip in host_ips:
            if not ip.startswith("127.") and ":" not in ip:
                return ip
    except Exception:
        pass
    return "127.0.0.1"


class RemoteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/tv.html"):
            self._serve_file(HTML_PATH, "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send_json({"ok": True, "status": "ready", "message": "Backend is ready"})
        elif self.path == "/api/info":
            self._send_json({
                "ok": True,
                "host": HOST,
                "port": PORT,
                "localUrl": f"http://{get_local_ip()}:{PORT}/"
            })
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        if self.path != "/api/command":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(body or "{}")
        except json.JSONDecodeError:
            payload = {}

        command = payload.get("command", "")
        print(f"Received command: {command}")
        self._send_json({
            "ok": True,
            "command": command,
            "message": f"Command '{command}' received by backend"
        })

    def _serve_file(self, path, content_type):
        with open(path, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    local_ip = get_local_ip()
    print(f"Starting remote backend on http://{HOST}:{PORT}")
    print(f"Open on your phone at http://{local_ip}:{PORT}/")
    server = HTTPServer((HOST, PORT), RemoteHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping remote backend")
        server.server_close()
