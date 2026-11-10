"""
Report Management Module
Generates analytical reports, inventory statistics, and CSV data exports.
Uses Python Standard Library (sqlite3, csv, datetime, pathlib).
"""

import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from config.database import get_connection

# Directory for exported reports
BASE_DIR = Path(__file__).resolve().parent.parent
EXPORTS_DIR = BASE_DIR / "exports"


def generate_reports():
    """
    Interactive sub-menu for various library reports and analytics.
    """
    while True:
        print("\n" + "=" * 40)
        print("          LIBRARY REPORTS")
        print("=" * 40)
        print("1. Library Summary Overview (Statistics)")
        print("2. View Available Books (In Stock)")
        print("3. View Out of Stock Books")
        print("4. View Currently Issued Books (Active)")
        print("5. View Returned Books History")
        print("6. View All Historical Issue Records")
        print("7. Back to Main Menu")

        choice = input("\nEnter your choice (1-7): ").strip()

        if choice == "1":
            display_summary_report()
        elif choice == "2":
            display_available_books()
        elif choice == "3":
            display_out_of_stock_books()
        elif choice == "4":
            display_currently_issued_books()
        elif choice == "5":
            display_returned_books()
        elif choice == "6":
            display_all_issued_records()
        elif choice == "7":
            break
        else:
            print("[!] Invalid choice! Please select 1 to 7.")


def display_summary_report():
    """
    Calculate and display high-level statistical overview of the library.
    """
    print("\n" + "=" * 55)
    print("           LIBRARY SUMMARY OVERVIEW")
    print("=" * 55)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Total titles & inventory
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0) FROM books")
        total_titles, total_inventory = cursor.fetchone()

        # In-stock vs out-of-stock titles
        cursor.execute("SELECT COUNT(*) FROM books WHERE quantity > 0")
        in_stock_titles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM books WHERE quantity = 0")
        out_of_stock_titles = cursor.fetchone()[0]

        # Issues
        cursor.execute("SELECT COUNT(*) FROM issued_books")
        total_issues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NULL")
        currently_issued = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NOT NULL")
        returned_count = cursor.fetchone()[0]

        print(f"  Total Book Titles Registered : {total_titles}")
        print(f"  Total Copies in Stock        : {total_inventory}")
        print(f"  Titles In Stock (Qty > 0)    : {in_stock_titles}")
        print(f"  Titles Out of Stock (Qty = 0): {out_of_stock_titles}")
        print("-" * 55)
        print(f"  Total Issue Transactions     : {total_issues}")
        print(f"  Currently Issued (Active)    : {currently_issued}")
        print(f"  Successfully Returned        : {returned_count}")
        print("=" * 55)

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def display_available_books():
    """
    Display books that currently have copies available for borrowing (quantity > 0).
    """
    print("\n" + "=" * 75)
    print("                       AVAILABLE BOOKS (IN STOCK)")
    print("=" * 75)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, author, quantity
            FROM books
            WHERE quantity > 0
            ORDER BY title ASC
            """
        )
        books = cursor.fetchall()

        if not books:
            print("No books are currently available in stock.")
            print("-" * 75)
            return

        print(f"{'ID':<8}{'TITLE':<32}{'AUTHOR':<24}{'AVAILABLE':<10}")
        print("-" * 75)

        for book in books:
            book_id, title, author, quantity = book
            disp_title = (title[:29] + "...") if len(title) > 32 else title
            disp_author = (author[:21] + "...") if len(author) > 24 else author
            print(f"{book_id:<8}{disp_title:<32}{disp_author:<24}{quantity:<10}")

        print("-" * 75)
        print(f"Total Available Titles: {len(books)}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def display_out_of_stock_books():
    """
    Display books that currently have 0 copies available.
    """
    print("\n" + "=" * 75)
    print("                       OUT OF STOCK BOOKS (QTY = 0)")
    print("=" * 75)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, title, author, quantity
            FROM books
            WHERE quantity = 0
            ORDER BY title ASC
            """
        )
        books = cursor.fetchall()

        if not books:
            print("Great news! There are currently no out-of-stock books.")
            print("-" * 75)
            return

        print(f"{'ID':<8}{'TITLE':<32}{'AUTHOR':<24}{'QUANTITY':<10}")
        print("-" * 75)

        for book in books:
            book_id, title, author, quantity = book
            disp_title = (title[:29] + "...") if len(title) > 32 else title
            disp_author = (author[:21] + "...") if len(author) > 24 else author
            print(f"{book_id:<8}{disp_title:<32}{disp_author:<24}{quantity:<10}")

        print("-" * 75)
        print(f"Total Out-of-Stock Titles: {len(books)}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def display_currently_issued_books():
    """
    Display all books currently checked out by students (return_date IS NULL).
    """
    print("\n" + "=" * 105)
    print("                     CURRENTLY ISSUED BOOKS (PENDING RETURN)")
    print("=" * 105)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            WHERE i.return_date IS NULL
            ORDER BY i.issue_date DESC
            """
        )
        records = cursor.fetchall()

        if not records:
            print("No books are currently issued.")
            print("-" * 105)
            return

        print(
            f"{'ISSUE ID':<10}"
            f"{'BOOK ID':<9}"
            f"{'BOOK TITLE':<32}"
            f"{'STUDENT NAME':<24}"
            f"{'ISSUE DATE':<22}"
        )
        print("-" * 105)

        for rec in records:
            issue_id, book_id, title, student_name, issue_date = rec
            disp_title = (title[:29] + "...") if len(title) > 32 else title
            disp_student = (student_name[:21] + "...") if len(student_name) > 24 else student_name
            print(f"{issue_id:<10}{book_id:<9}{disp_title:<32}{disp_student:<24}{issue_date:<22}")

        print("-" * 105)
        print(f"Total Currently Issued: {len(records)}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def display_returned_books():
    """
    Display historical records of returned books (return_date IS NOT NULL).
    """
    print("\n" + "=" * 115)
    print("                             RETURNED BOOKS HISTORY")
    print("=" * 115)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            WHERE i.return_date IS NOT NULL
            ORDER BY i.return_date DESC
            """
        )
        records = cursor.fetchall()

        if not records:
            print("No books have been returned yet.")
            print("-" * 115)
            return

        print(
            f"{'ISSUE ID':<10}"
            f"{'BOOK ID':<9}"
            f"{'BOOK TITLE':<30}"
            f"{'STUDENT NAME':<20}"
            f"{'ISSUE DATE':<20}"
            f"{'RETURN DATE':<20}"
        )
        print("-" * 115)

        for rec in records:
            issue_id, book_id, title, student_name, issue_date, return_date = rec
            disp_title = (title[:27] + "...") if len(title) > 30 else title
            disp_student = (student_name[:17] + "...") if len(student_name) > 20 else student_name
            print(f"{issue_id:<10}{book_id:<9}{disp_title:<30}{disp_student:<20}{issue_date:<20}{return_date:<20}")

        print("-" * 115)
        print(f"Total Returned Records: {len(records)}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def display_all_issued_records():
    """
    Display all historical issue records, both active and returned.
    """
    print("\n" + "=" * 125)
    print("                            ALL HISTORICAL ISSUE RECORDS")
    print("=" * 125)

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            ORDER BY i.id DESC
            """
        )
        records = cursor.fetchall()

        if not records:
            print("No issue records found in the database.")
            print("-" * 125)
            return

        print(
            f"{'ISSUE ID':<10}"
            f"{'BOOK ID':<9}"
            f"{'BOOK TITLE':<28}"
            f"{'STUDENT NAME':<20}"
            f"{'ISSUE DATE':<20}"
            f"{'RETURN DATE':<20}"
            f"{'STATUS':<10}"
        )
        print("-" * 125)

        for rec in records:
            issue_id, book_id, title, student_name, issue_date, return_date = rec
            disp_title = (title[:25] + "...") if len(title) > 28 else title
            disp_student = (student_name[:17] + "...") if len(student_name) > 20 else student_name
            disp_return = return_date if return_date else "N/A"
            status = "RETURNED" if return_date else "ACTIVE"
            print(
                f"{issue_id:<10}"
                f"{book_id:<9}"
                f"{disp_title:<28}"
                f"{disp_student:<20}"
                f"{issue_date:<20}"
                f"{disp_return:<20}"
                f"{status:<10}"
            )

        print("-" * 125)
        print(f"Total Historical Records: {len(records)}")

    except sqlite3.Error as error:
        print(f"[!] Database Error: {error}")
    finally:
        if conn:
            conn.close()


def export_csv_report():
    """
    Export library records (books, issues, or both) to standard CSV files.
    """
    EXPORTS_DIR.mkdir(exist_ok=True)

    while True:
        print("\n" + "=" * 40)
        print("          EXPORT CSV REPORTS")
        print("=" * 40)
        print("1. Export Books Catalog to CSV")
        print("2. Export Issue Records to CSV")
        print("3. Export Complete Library Data (Both)")
        print("4. Back to Main Menu")

        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            _export_books_csv()
        elif choice == "2":
            _export_issues_csv()
        elif choice == "3":
            _export_books_csv()
            _export_issues_csv()
        elif choice == "4":
            break
        else:
            print("[!] Invalid choice! Please select 1 to 4.")


def _export_books_csv():
    """
    Export all books to a timestamped CSV file.
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = EXPORTS_DIR / f"books_report_{timestamp}.csv"

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, title, author, quantity FROM books ORDER BY id ASC")
        books = cursor.fetchall()

        with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Book ID", "Title", "Author", "Quantity"])
            writer.writerows(books)

        print(f"[+] Books catalog successfully exported ({len(books)} records)!")
        print(f"    File: {filepath.resolve()}")

    except sqlite3.Error as error:
        print(f"[!] Database Error while exporting books: {error}")
    except OSError as error:
        print(f"[!] File Write Error: {error}")
    finally:
        if conn:
            conn.close()


def _export_issues_csv():
    """
    Export all issue records to a timestamped CSV file.
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = EXPORTS_DIR / f"issue_records_report_{timestamp}.csv"

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date,
                   CASE WHEN i.return_date IS NULL THEN 'ACTIVE' ELSE 'RETURNED' END AS status
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            ORDER BY i.id ASC
            """
        )
        records = cursor.fetchall()

        with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "Issue ID",
                "Book ID",
                "Book Title",
                "Student Name",
                "Issue Date",
                "Return Date",
                "Status",
            ])
            writer.writerows(records)

        print(f"[+] Issue records successfully exported ({len(records)} records)!")
        print(f"    File: {filepath.resolve()}")

    except sqlite3.Error as error:
        print(f"[!] Database Error while exporting issue records: {error}")
    except OSError as error:
        print(f"[!] File Write Error: {error}")
    finally:
        if conn:
            conn.close()
