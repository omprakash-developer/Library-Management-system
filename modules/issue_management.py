"""
Issue Management Module
Handles book issuing, returning, and issue record tracking.
Ensures database integrity and atomic transactions.
"""

import sqlite3
from datetime import datetime
from config.database import get_connection
from utils.validators import (
    validate_string,
    validate_positive_integer,
)


def issue_book():
    """
    Issue an available book to a student.
    Validates book existence and stock availability (> 0).
    Atomically decreases book quantity and records the issue transaction.
    """
    print("\n" + "=" * 35)
    print("          ISSUE BOOK")
    print("=" * 35)

    raw_book_id = input("Enter Book ID to issue: ").strip()
    book_id = validate_positive_integer(raw_book_id, allow_zero=False)

    if book_id is None:
        print("[!] Error: Please enter a valid numeric Book ID!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if the book exists and inspect current available quantity
        cursor.execute("SELECT id, title, author, quantity FROM books WHERE id = ?", (book_id,))
        book = cursor.fetchone()

        if book is None:
            print(f"[!] Error: Book ID #{book_id} not found in the library!")
            return

        book_id, title, author, quantity = book

        print(f"\nBook Selected: '{title}' by {author}")
        print(f"Available Quantity: {quantity}")

        # Check availability
        if quantity <= 0:
            print(f"[!] Error: Book '{title}' (ID #{book_id}) is currently OUT OF STOCK!")
            print("    No copies are currently available for issuing.")
            return

        # Prompt for student name
        raw_student = input("\nEnter student name: ")
        student_name = validate_string(raw_student)

        if not student_name:
            print("[!] Error: Student name cannot be empty!")
            return

        # Record current date & time
        issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Atomic transaction: Insert issue record & decrement quantity
        cursor.execute(
            """
            INSERT INTO issued_books (book_id, student_name, issue_date, return_date)
            VALUES (?, ?, ?, NULL)
            """,
            (book_id, student_name, issue_date),
        )
        issue_id = cursor.lastrowid

        cursor.execute(
            """
            UPDATE books
            SET quantity = quantity - 1
            WHERE id = ?
            """,
            (book_id,),
        )

        conn.commit()

        remaining_qty = quantity - 1
        print("\n" + "-" * 45)
        print("[+] BOOK ISSUED SUCCESSFULLY!")
        print(f"  Issue ID           : #{issue_id}")
        print(f"  Book ID            : #{book_id}")
        print(f"  Book Title         : {title}")
        print(f"  Issued To          : {student_name}")
        print(f"  Issue Date & Time  : {issue_date}")
        print(f"  Remaining Stock    : {remaining_qty}")
        print("-" * 45)

    except sqlite3.Error as error:
        print(f"[!] Database Error while issuing book: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def return_book():
    """
    Process book return from a student by Issue ID.
    Validates that the issue record exists and has not already been returned.
    Atomically updates return_date and increments available book quantity.
    """
    print("\n" + "=" * 35)
    print("          RETURN BOOK")
    print("=" * 35)

    raw_issue_id = input("Enter Issue ID: ").strip()
    issue_id = validate_positive_integer(raw_issue_id, allow_zero=False)

    if issue_id is None:
        print("[!] Error: Please enter a valid numeric Issue ID!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Fetch issue record along with book details
        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date, b.quantity
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            WHERE i.id = ?
            """,
            (issue_id,),
        )
        record = cursor.fetchone()

        if record is None:
            print(f"[!] Error: Issue record ID #{issue_id} not found!")
            return

        issue_id, book_id, title, student_name, issue_date, return_date, current_qty = record

        print(f"\nIssue Details:")
        print(f"  Issue ID   : #{issue_id}")
        print(f"  Book Title : {title} (Book ID #{book_id})")
        print(f"  Student    : {student_name}")
        print(f"  Issue Date : {issue_date}")

        # Check if already returned
        if return_date is not None:
            print(f"\n[!] Notice: This book has ALREADY been returned on {return_date}!")
            print("    Duplicate return operations are prevented.")
            return

        # Record return timestamp
        return_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Atomic transaction: Mark return date and increment quantity
        cursor.execute(
            """
            UPDATE issued_books
            SET return_date = ?
            WHERE id = ?
            """,
            (return_timestamp, issue_id),
        )

        cursor.execute(
            """
            UPDATE books
            SET quantity = quantity + 1
            WHERE id = ?
            """,
            (book_id,),
        )

        conn.commit()

        updated_qty = current_qty + 1
        print("\n" + "-" * 45)
        print("[+] BOOK RETURNED SUCCESSFULLY!")
        print(f"  Issue ID           : #{issue_id}")
        print(f"  Book Title         : {title}")
        print(f"  Student            : {student_name}")
        print(f"  Returned At        : {return_timestamp}")
        print(f"  Updated Stock Qty  : {updated_qty}")
        print("-" * 45)

    except sqlite3.Error as error:
        print(f"[!] Database Error while returning book: {error}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def display_issue_records_table(records, title="ISSUE RECORDS"):
    """
    Helper function to render a list of issue records in a formatted table.
    """
    print("\n" + "=" * 105)
    print(f"{title:^105}")
    print("=" * 105)

    if not records:
        print("No matching issue records found.")
        print("-" * 105)
        return

    print(
        f"{'ISSUE ID':<10}"
        f"{'BOOK ID':<9}"
        f"{'BOOK TITLE':<28}"
        f"{'STUDENT NAME':<20}"
        f"{'ISSUE DATE':<20}"
        f"{'RETURN DATE':<20}"
    )
    print("-" * 105)

    for rec in records:
        issue_id, book_id, book_title, student_name, issue_date, return_date = rec
        disp_title = (book_title[:25] + "...") if len(book_title) > 28 else book_title
        disp_student = (student_name[:17] + "...") if len(student_name) > 20 else student_name
        disp_return = return_date if return_date else "PENDING (Issued)"
        print(
            f"{issue_id:<10}"
            f"{book_id:<9}"
            f"{disp_title:<28}"
            f"{disp_student:<20}"
            f"{issue_date:<20}"
            f"{disp_return:<20}"
        )

    print("-" * 105)
    print(f"Total Records: {len(records)}")


def view_issue_records():
    """
    Menu to view all issue records, active issues, returned books, or search by ID.
    """
    while True:
        print("\n" + "=" * 35)
        print("       VIEW ISSUE RECORDS")
        print("=" * 35)
        print("1. View All Issue Records")
        print("2. View Currently Issued (Active)")
        print("3. View Returned Books History")
        print("4. Search Issue Record by Issue ID")
        print("5. Back to Main Menu")

        choice = input("\nEnter your choice (1-5): ").strip()

        if choice == "1":
            _fetch_and_display_records(None, "ALL ISSUE RECORDS")
        elif choice == "2":
            _fetch_and_display_records("WHERE i.return_date IS NULL", "CURRENTLY ISSUED BOOKS (PENDING RETURN)")
        elif choice == "3":
            _fetch_and_display_records("WHERE i.return_date IS NOT NULL", "RETURNED BOOKS HISTORY")
        elif choice == "4":
            _search_record_by_id()
        elif choice == "5":
            break
        else:
            print("[!] Invalid choice! Please select 1 to 5.")


def _fetch_and_display_records(where_clause, header_title):
    """
    Query and display records with an optional WHERE clause.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql = f"""
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            {where_clause or ''}
            ORDER BY i.id DESC
        """
        cursor.execute(sql)
        records = cursor.fetchall()
        display_issue_records_table(records, header_title)

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def _search_record_by_id():
    """
    Search and display a single issue record by Issue ID.
    """
    raw_id = input("Enter Issue ID to search: ").strip()
    issue_id = validate_positive_integer(raw_id, allow_zero=False)

    if issue_id is None:
        print("[!] Error: Please enter a valid numeric Issue ID!")
        return

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            WHERE i.id = ?
            """,
            (issue_id,),
        )
        record = cursor.fetchall()
        display_issue_records_table(record, f"SEARCH RESULT FOR ISSUE ID #{issue_id}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()

