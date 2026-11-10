"""
Main Application Entry Point
Library Management System Using Python and SQLite3.
Provides a clean, interactive console interface for all library operations.
"""

import sys
from config.database import create_tables
from modules.book_management import (
    add_book,
    view_books,
    update_book,
    delete_book,
)
from modules.search_management import search_books
from modules.issue_management import (
    issue_book,
    return_book,
    view_issue_records,
)
from modules.report_management import (
    generate_reports,
    export_csv_report,
)


def print_menu():
    """
    Display the main application console menu.
    """
    print("\n" + "=" * 40)
    print("       LIBRARY MANAGEMENT SYSTEM")
    print("=" * 40)
    print("1. Add New Book")
    print("2. View All Books")
    print("3. Update Book")
    print("4. Delete Book")
    print("5. Search Books")
    print("6. Issue Book")
    print("7. Return Book")
    print("8. View Issue Records")
    print("9. Generate Reports")
    print("10. Export CSV Report")
    print("11. Exit")
    print("=" * 40)


def main():
    """
    Main loop initializing database and handling user menu selections.
    """
    # Configure stdout/stderr encoding to prevent charmap errors on Windows consoles
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Ensure database tables and indices exist
    create_tables()

    print("\nWelcome to the Library Management System!")

    while True:
        try:
            print_menu()
            choice = input("Select an option: ").strip()

            if choice == "1":
                add_book()

            elif choice == "2":
                view_books()

            elif choice == "3":
                update_book()

            elif choice == "4":
                delete_book()

            elif choice == "5":
                search_books()

            elif choice == "6":
                issue_book()

            elif choice == "7":
                return_book()

            elif choice == "8":
                view_issue_records()

            elif choice == "9":
                generate_reports()

            elif choice == "10":
                export_csv_report()

            elif choice == "11":
                print("\nThank you for using the Library Management System! Goodbye.")
                break

            else:
                print("\n[!] Invalid choice! Please select an option between 1 and 11.")

        except (KeyboardInterrupt, EOFError):
            print("\n\nOperation interrupted by user. Exiting application. Goodbye!")
            break
        except Exception as unexpected_error:
            print(f"\n[!] An unexpected error occurred: {unexpected_error}")
            print("    Returning to main menu...")


if __name__ == "__main__":
    main()
