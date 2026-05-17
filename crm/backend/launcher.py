import os
import sys
import time
import threading
import webbrowser
from app import create_app

def start_server(app, port):
    """Run the Flask app on the specified port."""
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Determine absolute path for DB to avoid creating it in weird locations when packaged
    try:
        # If running as executable, store database in user's AppData or Home directory
        if getattr(sys, 'frozen', False):
            home_dir = os.path.expanduser("~")
            db_dir = os.path.join(home_dir, '.nexus_crm')
            os.makedirs(db_dir, exist_ok=True)
            os.environ['DATABASE_PATH'] = os.path.join(db_dir, 'crm.db')
    except Exception as e:
        print(f"Error configuring paths: {e}")

    # Create the Flask application
    app = create_app()
    PORT = 5000
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=start_server, args=(app, PORT), daemon=True)
    server_thread.start()
    
    # Wait for the server to start accepting requests
    time.sleep(1.5)
    
    # Open the default web browser to the local application
    print(f"Opening Nexus CRM in your web browser at http://127.0.0.1:{PORT}")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    
    # Keep the main thread alive so the server continues running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down Nexus CRM.")
