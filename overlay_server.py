import os
import json
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer
import socketserver

OVERLAY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "overlay")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True


class OverlayState:
    def __init__(self):
        self.clients = []
        self._lock = threading.Lock()
        self.last_state = {
            "blink_count": 0,
            "boss_interval": 25,
            "last_action": "",
            "is_blink": False,
            "is_boss": False,
            "is_paused": False
        }

    def add_client(self, client):
        with self._lock:
            self.clients.append(client)

    def remove_client(self, client):
        with self._lock:
            if client in self.clients:
                self.clients.remove(client)

    def broadcast(self, blink_count: int, boss_interval: int, last_action: str = "", is_blink: bool = False, is_boss: bool = False, is_paused: bool = False):
        payload = {
            "blink_count": blink_count,
            "boss_interval": boss_interval,
            "last_action": last_action,
            "is_blink": is_blink,
            "is_boss": is_boss,
            "is_paused": is_paused
        }
        with self._lock:
            self.last_state = payload
            msg = f"data: {json.dumps(payload)}\n\n"
            dead_clients = []
            for client in self.clients:
                try:
                    client.wfile.write(msg.encode('utf-8'))
                    client.wfile.flush()
                except Exception:
                    dead_clients.append(client)

            for d in dead_clients:
                if d in self.clients:
                    self.clients.remove(d)


overlay_state = OverlayState()


class OverlayRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OVERLAY_DIR, **kwargs)

    def do_GET(self):
        if self.path == '/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            initial_msg = f"data: {json.dumps(overlay_state.last_state)}\n\n"
            self.wfile.write(initial_msg.encode('utf-8'))
            self.wfile.flush()

            overlay_state.add_client(self)

            try:
                while True:
                    threading.Event().wait(10.0)
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
            except Exception:
                overlay_state.remove_client(self)
        elif self.path in ('/', '/index.html'):
            self.path = '/overlay.html'
            return super().do_GET()
        else:
            return super().do_GET()

    def log_message(self, format, *args):
        pass


def start_overlay_server(port: int = 8765):
    server = ThreadedHTTPServer(('0.0.0.0', port), OverlayRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[Overlay] OBS Browser Source ready at: http://localhost:{port}/")
    return server
