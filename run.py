"""
SheRise Startup Launcher
Initializes the database and starts the HTTP REST & static server.
"""

import sys
import os

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import server

if __name__ == "__main__":
    print("=" * 60)
    print("🌸 SheRise — Empowering Women Entrepreneurs Platform")
    print("=" * 60)
    database.init_db()
    server.run_server()
