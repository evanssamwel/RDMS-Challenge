#!/usr/bin/env python3
"""
SimpleSQLDB - Entry Point
Demonstrates clean separation between RDBMS engine and web application

The RDBMS is completely independent - it can be used via:
1. Interactive CLI/REPL (see repl/cli.py)
2. Web Application (see web_demo/app_studio.py)
3. Direct API (import core.engine directly)

This design proves the RDBMS is reusable across different interfaces.
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)


def show_menu():
    """Display main menu"""
    print("\n" + "="*60)
    print("  SimpleSQLDB - Database Management System")
    print("="*60)
    print("\nChoose how you'd like to interact with SimpleSQLDB:\n")
    print("  1. Interactive CLI/REPL Mode")
    print("     └─ Command-line interface for direct SQL execution")
    print("     └─ Try: .sys_tables, .sys_indexes, .explain")
    print()
    print("  2. Professional Web Studio")
    print("     └─ Modern dashboard with CRUD + Analytics")
    print("     └─ URL: http://127.0.0.1:5000")
    print()
    print("  3. View Documentation")
    print()
    print("  4. Run Tests")
    print()
    print("  0. Exit")
    print("\n" + "-"*60)
    return input("Enter your choice (0-4): ").strip()


def run_cli():
    """Launch interactive CLI mode"""
    print("\n🚀 Starting SimpleSQLDB CLI...")
    print("   The RDBMS engine operates independently in this mode.")
    print("   Try: .help for available commands\n")
    
    from repl.cli import SimpleSQLDBREPL
    repl = SimpleSQLDBREPL()
    repl.run()


def run_web():
    """Launch web studio"""
    print("\n🌐 Starting SimpleSQLDB Web Studio...")
    print("   The web app is a consumer of the independent RDBMS engine.")
    print("   Separation of Concerns: Engine ← Web Framework")
    print("   Opening browser to http://127.0.0.1:5000\n")
    
    import webbrowser
    from web_demo.app_studio import app
    
    # Open browser after a short delay
    webbrowser.open('http://127.0.0.1:5000', delay=2)
    
    # Start Flask
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)


def show_documentation():
    """Show documentation links"""
    print("\n" + "="*60)
    print("  Documentation")
    print("="*60)
    print("""
📖 Key Documentation Files:

  README.md
    └─ Project overview and quick start

  QUICKSTART.md
    └─ Get running in 5 minutes

  ADVANCED_FEATURES.md
    └─ Aggregates, GROUP BY, HAVING, Foreign Keys

  FINISHING_TOUCHES.md
    └─ Atomic writes, system tables, .explain command

  STUDIO_GUIDE.md
    └─ Web studio usage guide

  ARCHITECTURE.md
    └─ Separation of Concerns design

🏗️  Architecture Overview:

  core/              ← RDBMS Engine (Independent)
    ├─ engine.py       # Public API for all operations
    ├─ parser.py       # SQL parsing
    ├─ storage.py      # Data persistence
    ├─ index.py        # B-Tree indexing
    └─ aggregates.py   # Aggregate functions

  repl/              ← CLI Interface (Uses 'core')
    └─ cli.py

  web_demo/          ← Web Application (Uses 'core')
    ├─ app_studio.py   # Flask app
    └─ templates/      # HTML templates

  tests/             ← Unit Tests (Tests 'core')
""")
    input("\nPress Enter to return to menu...")


def run_tests():
    """Run pytest"""
    print("\n🧪 Running Tests...")
    import subprocess
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], cwd=PROJECT_ROOT)
    sys.exit(result.returncode)


def main():
    """Main entry point"""
    while True:
        choice = show_menu()
        
        if choice == "1":
            try:
                run_cli()
            except KeyboardInterrupt:
                print("\n\n👋 Exiting CLI mode...")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")
        
        elif choice == "2":
            try:
                run_web()
            except KeyboardInterrupt:
                print("\n\n👋 Exiting Web Studio...")
            except Exception as e:
                print(f"\n❌ Error: {e}")
                input("Press Enter to continue...")
        
        elif choice == "3":
            show_documentation()
        
        elif choice == "4":
            run_tests()
        
        elif choice == "0":
            print("\n👋 Thank you for using SimpleSQLDB!\n")
            sys.exit(0)
        
        else:
            print("\n❌ Invalid choice. Please try again.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
