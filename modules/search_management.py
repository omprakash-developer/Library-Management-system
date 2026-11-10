"""
Search Management Module
Provides multi-criteria search capabilities: by ID, title, and author.
Supports partial and case-insensitive matching with formatted results.
"""

import sqlite3
from config.database import get_connection
from utils.validators import (
    validate_string,
    validate_positive_integer,
)


def display_results(books, search_term=None):
    """
    Format and display search results in a clean table.
    """
    if not books:
        if search_term:
            print(f"\n[!] No matching books found for '{search_term}'.")
        else:
            print("\n[!] No matching books found.")
        return

    print("\n" + "=" * 75)
    print("                           SEARCH RESULTS")
    print("=" * 75)

    print(f"{'ID':<8}{'TITLE':<32}{'AUTHOR':<24}{'QUANTITY':<10}")
    print("-" * 75)

    for book in books:
        book_id, title, author, quantity = book
        disp_title = (title[:29] + "...") if len(title) > 32 else title
        disp_author = (author[:21] + "...") if len(author) > 24 else author
        print(f"{book_id:<8}{disp_title:<32}{disp_author:<24}{quantity:<10}")

    print("-" * 75)
    print(f"Total Matches Found: {len(books)}")


def search_by_id():
    """
    Search for a specific book by its primary key ID.
    """
    print("\n" + "=" * 30)
    print("     SEARCH BY BOOK ID")
    print("=" * 30)

    raw_id = input("Enter book ID: ").strip()
    book_id = validate_positive_integer(raw_id, allow_zero=False)

    if book_id is None:
        print("[!] Error: Please enter a valid positive numeric ID!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, title, author, quantity FROM books WHERE id = ?",
            (book_id,),
        )
        books = cursor.fetchall()
        display_results(books, search_term=f"ID #{book_id}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def search_by_title():
    """
    Search for books whose titles contain the search string (case-insensitive partial match).
    """
    print("\n" + "=" * 30)
    print("    SEARCH BY BOOK TITLE")
    print("=" * 30)

    raw_title = input("Enter book title or keyword: ")
    title = validate_string(raw_title)

    if not title:
        print("[!] Error: Book title cannot be empty!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, author, quantity FROM books
            WHERE title LIKE ? COLLATE NOCASE
            ORDER BY title ASC
            """,
            (f"%{title}%",),
        )
        books = cursor.fetchall()
        display_results(books, search_term=title)

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def search_by_author():
    """
    Search for books whose author name contains the search string (case-insensitive partial match).
    """
    print("\n" + "=" * 30)
    print("      SEARCH BY AUTHOR")
    print("=" * 30)

    raw_author = input("Enter author name or keyword: ")
    author = validate_string(raw_author)

    if not author:
        print("[!] Error: Author name cannot be empty!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, author, quantity FROM books
            WHERE author LIKE ? COLLATE NOCASE
            ORDER BY author ASC
            """,
            (f"%{author}%",),
        )
        books = cursor.fetchall()
        display_results(books, search_term=author)

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def search_books():
    """
    Interactive sub-menu for book search operations.
    """
    while True:
        print("\n" + "=" * 30)
        print("      BOOK SEARCH MENU")
        print("=" * 30)
        print("1. Search by Book ID")
        print("2. Search by Book Title")
        print("3. Search by Author")
        print("4. Back to Main Menu")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            search_by_id()
        elif choice == "2":
            search_by_title()
        elif choice == "3":
            search_by_author()
        elif choice == "4":
            break
        else:
            print("[!] Invalid choice! Please select 1 to 4.")
