"""
Simple static file server for the landing page.
Runs alongside the bot worker on Railway (separate PORT).
"""
import os
import http.server
import socketserver

PORT = int(os.environ.get("PORT", 8080))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="landing", **kwargs)

    def log_message(self, format, *args):
        pass  # suppress access logs in Railway output


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Landing page serving on port {PORT}")
        httpd.serve_forever()
