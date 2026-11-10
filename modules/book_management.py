"""
Book Management Module
Handles CRUD operations for books: Add, View, Update, and Delete.
"""

import sqlite3
from config.database import get_connection
from utils.validators import (
    validate_string,
    validate_positive_integer,
    get_confirmation,
)


def add_book():
    """
    Prompt user for title, author, and quantity to add a new book to the library.
    Validates all inputs before database insertion.
    """
    print("\n" + "=" * 30)
    print("        ADD NEW BOOK")
    print("=" * 30)

    raw_title = input("Enter book title: ")
    title = validate_string(raw_title)

    raw_author = input("Enter author name: ")
    author = validate_string(raw_author)

    if not title or not author:
        print("[!] Error: Book title and author name cannot be empty!")
        return

    raw_quantity = input("Enter book quantity: ")
    quantity = validate_positive_integer(raw_quantity, allow_zero=False)

    if quantity is None:
        print("[!] Error: Quantity must be a valid positive whole number (> 0)!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO books (title, author, quantity)
            VALUES (?, ?, ?)
            """,
            (title, author, quantity),
        )

        conn.commit()
        new_id = cursor.lastrowid
        print(f"[+] Book '{title}' added successfully with ID #{new_id} (Quantity: {quantity})!")

    except sqlite3.Error as error:
        print(f"[!] Database Error while adding book: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def view_books():
    """
    Display all books registered in the library inventory in a formatted table.
    """
    print("\n" + "=" * 75)
    print("                           ALL LIBRARY BOOKS")
    print("=" * 75)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, author, quantity FROM books ORDER BY id ASC")
        books = cursor.fetchall()

        if not books:
            print("No books available in the library database.")
            print("-" * 75)
            return

        print(f"{'ID':<8}{'TITLE':<32}{'AUTHOR':<24}{'QUANTITY':<10}")
        print("-" * 75)

        for book in books:
            book_id, title, author, quantity = book
            # Truncate overly long titles/authors for neat display
            disp_title = (title[:29] + "...") if len(title) > 32 else title
            disp_author = (author[:21] + "...") if len(author) > 24 else author
            print(f"{book_id:<8}{disp_title:<32}{disp_author:<24}{quantity:<10}")

        print("-" * 75)
        print(f"Total Books Listed: {len(books)}")

    except sqlite3.Error as error:
        print(f"[!] Database Error while fetching books: {error}")
    finally:
        if conn:
            conn.close()


def update_book():
    """
    Update title, author, and/or quantity of an existing book.
    Pressing Enter leaves the existing value unchanged.
    """
    print("\n" + "=" * 30)
    print("        UPDATE BOOK")
    print("=" * 30)

    raw_id = input("Enter book ID to update: ").strip()
    book_id = validate_positive_integer(raw_id, allow_zero=False)

    if book_id is None:
        print("[!] Error: Please enter a valid numeric Book ID!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, author, quantity FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        if book is None:
            print(f"[!] Error: Book with ID #{book_id} not found in the library!")
            return

        _, curr_title, curr_author, curr_quantity = book

        print("\nCurrent Book Details:")
        print(f"  ID       : {book_id}")
        print(f"  Title    : {curr_title}")
        print(f"  Author   : {curr_author}")
        print(f"  Quantity : {curr_quantity}")
        print("(Press Enter to keep current value)")

        new_title = input(f"Enter new title [{curr_title}]: ").strip()
        new_title = new_title if new_title else curr_title

        new_author = input(f"Enter new author [{curr_author}]: ").strip()
        new_author = new_author if new_author else curr_author

        raw_new_qty = input(f"Enter new quantity [{curr_quantity}]: ").strip()
        if raw_new_qty:
            new_quantity = validate_positive_integer(raw_new_qty, allow_zero=True)
            if new_quantity is None:
                print("[!] Error: Quantity must be a valid non-negative integer (>= 0)!")
                return
        else:
            new_quantity = curr_quantity

        cursor.execute(
            """
            UPDATE books
            SET title = ?, author = ?, quantity = ?
            WHERE id = ?
            """,
            (new_title, new_author, new_quantity, book_id),
        )

        conn.commit()
        print(f"[+] Book #{book_id} updated successfully!")

    except sqlite3.Error as error:
        print(f"[!] Database Error while updating book: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def delete_book():
    """
    Delete a book from the library database.
    Enforces referential integrity:
    1. Rejects deletion if book is currently issued.
    2. Rejects deletion if book has any issue history (to preserve library audit logs).
    Requires explicit user confirmation before deletion.
    """
    print("\n" + "=" * 30)
    print("        DELETE BOOK")
    print("=" * 30)

    raw_id = input("Enter book ID to delete: ").strip()
    book_id = validate_positive_integer(raw_id, allow_zero=False)

    if book_id is None:
        print("[!] Error: Please enter a valid numeric Book ID!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        if book is None:
            print(f"[!] Error: Book with ID #{book_id} not found!")
            return

        title = book[1]

        # 1. Check if the book is currently issued (active issue)
        cursor.execute(
            """
            SELECT COUNT(*) FROM issued_books
            WHERE book_id = ? AND return_date IS NULL
            """,
            (book_id,),
        )
        active_issues = cursor.fetchone()[0]

        if active_issues > 0:
            print(f"[!] Cannot delete book '{title}' (ID #{book_id})!")
            print(f"    This book is currently issued to {active_issues} student(s).")
            print("    Please ensure all issued copies are returned first.")
            return

        # 2. Check if the book has any historical issue records
        cursor.execute(
            """
            SELECT COUNT(*) FROM issued_books
            WHERE book_id = ?
            """,
            (book_id,),
        )
        total_history = cursor.fetchone()[0]

        if total_history > 0:
            print(f"[!] Cannot delete book '{title}' (ID #{book_id})!")
            print("    This book has historical issue/return records.")
            print("    To maintain database integrity and audit history, books with issue history cannot be deleted.")
            return

        # Ask for confirmation
        confirmed = get_confirmation(f"Are you sure you want to permanently delete '{title}'? (yes/no): ")
        if not confirmed:
            print("[*] Book deletion cancelled.")
            return

        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        print(f"[+] Book '{title}' (ID #{book_id}) deleted successfully!")

    except sqlite3.IntegrityError as error:
        print(f"[!] Cannot delete book due to database constraint: {error}")
        if conn:
            conn.rollback()
    except sqlite3.Error as error:
        print(f"[!] Database Error while deleting book: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
