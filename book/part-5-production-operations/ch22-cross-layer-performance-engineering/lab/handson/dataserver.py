#!/usr/bin/env python3
"""Ch 22 hands-on data server: serves raw training batches over HTTP/1.1 (keep-alive).

    python3 dataserver.py --bind 10.22.0.2 --port 8222 --bytes 4194304

GET /batch/<i> returns <bytes> bytes of deterministic pseudo-random data (16 distinct blobs, chosen by i);
GET /health returns "ok". Standard library only; run it inside the ch22-data network namespace.
"""
from __future__ import annotations

import argparse
import random
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bind", default="10.22.0.2")
    ap.add_argument("--port", type=int, default=8222)
    ap.add_argument("--bytes", type=int, default=4 * 1024 * 1024)
    a = ap.parse_args()
    rng = random.Random(22)
    blobs = [rng.randbytes(a.bytes) for _ in range(16)]

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def do_GET(self):  # noqa: N802
            if self.path == "/health":
                body = b"ok"
            elif self.path.startswith("/batch/"):
                try:
                    body = blobs[int(self.path.rsplit("/", 1)[1]) % len(blobs)]
                except ValueError:
                    self.send_error(400)
                    return
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer((a.bind, a.port), Handler)
    print(f"serving {len(blobs)} x {a.bytes} B on {a.bind}:{a.port}", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
