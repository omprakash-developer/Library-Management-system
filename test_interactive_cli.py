"""
Interactive CLI Simulation Test
Pipes simulated user inputs into main.py and verifies menu flow and screen outputs.
"""

import subprocess
import sys

def test_cli():
    # Sequence of commands:
    # 2 -> View All Books
    # 5 -> Search Books -> 2 -> "clean" -> 4 (Back)
    # 9 -> Generate Reports -> 1 (Summary) -> 7 (Back)
    # 10 -> Export CSV -> 3 (Both) -> 4 (Back)
    # 11 -> Exit
    inputs = "\n".join([
        "2",          # View All Books
        "5",          # Search Books
        "2",          # Search by Title
        "clean",      # keyword
        "4",          # Back to Main Menu
        "9",          # Generate Reports
        "1",          # Summary Overview
        "7",          # Back to Main Menu
        "10",         # Export CSV Report
        "3",          # Export Both
        "4",          # Back to Main Menu
        "11"          # Exit
    ]) + "\n"

    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stdout, stderr = proc.communicate(input=inputs)

    print("CLI Output length:", len(stdout))
    print("Stderr:", stderr)
    assert "LIBRARY MANAGEMENT SYSTEM" in stdout
    assert "ALL LIBRARY BOOKS" in stdout
    assert "SEARCH RESULTS" in stdout
    assert "LIBRARY SUMMARY OVERVIEW" in stdout
    assert "Books catalog successfully exported" in stdout
    assert "Thank you for using the Library Management System! Goodbye." in stdout
    print("Interactive CLI simulation test passed completely!")

if __name__ == "__main__":
    test_cli()

