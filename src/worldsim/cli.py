"""CLI utilities for worldsim."""

import webbrowser
import time
import uvicorn
import sys


def run_server():
    """Start the worldsim server and open in browser."""
    host = "127.0.0.1"
    port = 8000
    url = f"http://{host}:{port}"
    
    print(f"Starting Worldsim server at {url}")
    print("Press Ctrl+C to stop the server")
    print()
    
    # Schedule browser opening after a short delay to let server start
    def open_browser():
        time.sleep(1.5)
        print(f"Opening {url} in browser...")
        webbrowser.open(url)
    
    import threading
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    try:
        uvicorn.run(
            "worldsim.server:app",
            host=host,
            port=port,
            reload=True,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)


if __name__ == "__main__":
    run_server()
