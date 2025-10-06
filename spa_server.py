"""
Simple HTTP server for Single Page Applications (SPA).
Serves index.html for all routes that don't match static files.
"""
import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


class SPAHandler(SimpleHTTPRequestHandler):
    """HTTP request handler that serves index.html for SPA routes."""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.spa_directory = directory
        super().__init__(*args, directory=directory, **kwargs)
    
    def do_GET(self):
        """Handle GET requests with SPA routing support."""
        # Get the requested path
        path = self.translate_path(self.path)
        
        # If the path exists and is a file, serve it normally
        if os.path.isfile(path):
            return super().do_GET()
        
        # If the path is a directory and has an index.html, serve it
        if os.path.isdir(path):
            index_path = os.path.join(path, 'index.html')
            if os.path.isfile(index_path):
                return super().do_GET()
        
        # For all other routes (SPA routes), serve index.html
        # This allows React Router to handle the routing
        self.path = '/index.html'
        return super().do_GET()
    
    def log_message(self, format, *args):
        """Override to add custom logging prefix."""
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))
        sys.stdout.flush()


def run_spa_server(port=3000, directory=None):
    """Run the SPA server on the specified port."""
    if directory is None:
        directory = os.getcwd()
    
    directory = str(Path(directory).resolve())
    
    # Create handler with directory
    handler = lambda *args, **kwargs: SPAHandler(*args, directory=directory, **kwargs)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    
    print(f"Serving SPA from {directory}")
    print(f"Server running on http://127.0.0.1:{port}/")
    print("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        return 0
    
    return 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='SPA HTTP Server')
    parser.add_argument('port', type=int, nargs='?', default=3000,
                        help='Port to serve on (default: 3000)')
    parser.add_argument('-d', '--directory', type=str, default=None,
                        help='Directory to serve (default: current directory)')
    
    args = parser.parse_args()
    
    sys.exit(run_spa_server(port=args.port, directory=args.directory))

