#!/usr/bin/env python3
"""
Simple HTTP server to serve the frontend pages
"""
import http.server
import socketserver
import os
import webbrowser

PORT = 3000
DIRECTORY = "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("Frontend server started successfully!")
        print(f"Directory: {os.path.abspath(DIRECTORY)}")
        print(f"Address: http://localhost:{PORT}")
        print(f"Home: http://localhost:{PORT}/index.html")
        print(f"Login: http://localhost:{PORT}/login.html")
        print(f"\nTips: Press Ctrl+C to stop server")

        # Auto open browser
        webbrowser.open(f'http://localhost:{PORT}/index.html')

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped")
            httpd.shutdown()

if __name__ == "__main__":
    main()
