"""
Library Management System - Flask Web Application Backend
Provides RESTful and form-driven routes for modern web-based library management.
Reuses existing SQLite3 database, schemas, and validation utilities.
"""

import csv
import io
import os
import secrets
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config.database import create_tables, get_connection
from utils.validators import validate_positive_integer, validate_string

# Initialize Flask application
app = Flask(__name__)
# Cryptographically secure secret key for session and CSRF management
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Ensure database tables exist upon server startup
create_tables()

# Directory for server-side exported CSV copies
BASE_DIR = Path(__file__).resolve().parent
EXPORTS_DIR = BASE_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# CSRF Protection & Template Context Processors
# ==============================================================================

def generate_csrf_token():
    """Generate or retrieve a cryptographically secure CSRF token for the session."""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


@app.context_processor
def inject_csrf_token():
    """Make csrf_token() helper available in all Jinja templates."""
    return dict(csrf_token=generate_csrf_token)


@app.before_request
def csrf_protect():
    """
    Enforce CSRF token validation on all state-modifying requests (POST, PUT, DELETE).
    """
    if request.method in ("POST", "PUT", "DELETE"):
        # Retrieve token from form data or headers
        token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        expected = session.get("_csrf_token")
        if not expected or not token or not secrets.compare_digest(token, expected):
            app.logger.warning("CSRF validation failure on %s", request.path)
            flash("Security check failed (invalid or expired CSRF token). Please try again.", "error")
            # For POST forms, abort with 403 or redirect safely
            abort(403, description="CSRF token validation failed.")


# ==============================================================================
# Routes: Dashboard
# ==============================================================================

@app.route("/")
def dashboard():
    """
    Operational Dashboard showing key inventory metrics and recent loan activities.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Aggregate metrics
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0) FROM books")
        total_titles, total_inventory = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM books WHERE quantity > 0")
        in_stock_titles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM books WHERE quantity = 0")
        out_of_stock_titles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books")
        total_issues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NULL")
        currently_issued = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NOT NULL")
        returned_count = cursor.fetchone()[0]

        stats = {
            "total_titles": total_titles,
            "total_inventory": total_inventory,
            "in_stock_titles": in_stock_titles,
            "out_of_stock_titles": out_of_stock_titles,
            "total_issues": total_issues,
            "currently_issued": currently_issued,
            "returned_count": returned_count,
        }

        # Recent 8 circulation transactions
        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            ORDER BY i.id DESC
            LIMIT 8
            """
        )
        recent_rows = cursor.fetchall()
        recent_issues = [
            {
                "id": row[0],
                "book_id": row[1],
                "title": row[2],
                "student_name": row[3],
                "issue_date": row[4],
                "return_date": row[5],
            }
            for row in recent_rows
        ]

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            stats=stats,
            recent_issues=recent_issues,
        )

    finally:
        conn.close()


# ==============================================================================
# Routes: Book Management
# ==============================================================================

@app.route("/books")
def view_books_page():
    """
    Catalog view of all registered books with filter and issue count annotations.
    """
    current_filter = request.args.get("filter", "").strip().lower()

    conn = get_connection()
    try:
        cursor = conn.cursor()

        where_clause = ""
        if current_filter == "available":
            where_clause = "WHERE b.quantity > 0"
        elif current_filter == "out_of_stock":
            where_clause = "WHERE b.quantity = 0"

        query = f"""
            SELECT b.id, b.title, b.author, b.quantity,
                   (SELECT COUNT(*) FROM issued_books i WHERE i.book_id = b.id) AS issue_count,
                   (SELECT COUNT(*) FROM issued_books i WHERE i.book_id = b.id AND i.return_date IS NULL) AS active_loans
            FROM books b
            {where_clause}
            ORDER BY b.id ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        books = [
            {
                "id": r[0],
                "title": r[1],
                "author": r[2],
                "quantity": r[3],
                "issue_count": r[4],
                "active_loans": r[5],
            }
            for r in rows
        ]

        return render_template(
            "books.html",
            active_page="books",
            books=books,
            current_filter=current_filter,
        )
    finally:
        conn.close()


@app.route("/books/add", methods=["GET", "POST"])
def add_book_page():
    """
    Add a new book to the library inventory.
    """
    if request.method == "POST":
        raw_title = request.form.get("title")
        raw_author = request.form.get("author")
        raw_quantity = request.form.get("quantity")

        title = validate_string(raw_title)
        author = validate_string(raw_author)
        quantity = validate_positive_integer(raw_quantity, allow_zero=False)

        if not title or not author:
            flash("Book title and author name cannot be empty.", "error")
            return render_template("add_book.html", active_page="add_book")

        if quantity is None:
            flash("Quantity must be a valid positive whole number (> 0).", "error")
            return render_template("add_book.html", active_page="add_book")

        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)",
                (title, author, quantity),
            )
            conn.commit()
            new_id = cursor.lastrowid
            flash(f"Book '{title}' added successfully with ID #{new_id} (Quantity: {quantity})!", "success")
            return redirect(url_for("view_books_page"))
        except sqlite3.Error as e:
            conn.rollback()
            flash(f"Database error while adding book: {e}", "error")
            return render_template("add_book.html", active_page="add_book")
        finally:
            conn.close()

    return render_template("add_book.html", active_page="add_book")


@app.route("/books/edit/<int:id>", methods=["GET", "POST"])
def edit_book_page(id):
    """
    Edit title, author, and in-stock quantity of an existing book.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, quantity FROM books WHERE id = ?", (id,))
        row = cursor.fetchone()

        if not row:
            flash(f"Book with ID #{id} not found.", "error")
            return redirect(url_for("view_books_page"))

        book = {"id": row[0], "title": row[1], "author": row[2], "quantity": row[3]}

        if request.method == "POST":
            raw_title = request.form.get("title")
            raw_author = request.form.get("author")
            raw_quantity = request.form.get("quantity")

            title = validate_string(raw_title)
            author = validate_string(raw_author)
            quantity = validate_positive_integer(raw_quantity, allow_zero=True)

            if not title or not author:
                flash("Book title and author cannot be empty.", "error")
                return render_template("edit_book.html", active_page="books", book=book)

            if quantity is None:
                flash("Quantity must be a non-negative integer (>= 0).", "error")
                return render_template("edit_book.html", active_page="books", book=book)

            cursor.execute(
                "UPDATE books SET title = ?, author = ?, quantity = ? WHERE id = ?",
                (title, author, quantity, id),
            )
            conn.commit()
            flash(f"Book #{id} ('{title}') details updated successfully!", "success")
            return redirect(url_for("view_books_page"))

        return render_template("edit_book.html", active_page="books", book=book)

    finally:
        conn.close()


@app.route("/books/delete/<int:id>", methods=["POST"])
def delete_book_route(id):
    """
    Delete a book from inventory. Enforces referential integrity:
    1. Blocks deletion if book is currently issued.
    2. Blocks deletion if book has any historical issue records.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title FROM books WHERE id = ?", (id,))
        book = cursor.fetchone()

        if not book:
            flash(f"Book with ID #{id} was not found.", "error")
            return redirect(url_for("view_books_page"))

        title = book[1]

        # 1. Check for active loans
        cursor.execute(
            "SELECT COUNT(*) FROM issued_books WHERE book_id = ? AND return_date IS NULL",
            (id,),
        )
        active_loans = cursor.fetchone()[0]
        if active_loans > 0:
            flash(
                f"Cannot delete '{title}'! This book is currently issued to {active_loans} student(s).",
                "error",
            )
            return redirect(url_for("view_books_page"))

        # 2. Check for any issue history (audit preservation)
        cursor.execute(
            "SELECT COUNT(*) FROM issued_books WHERE book_id = ?",
            (id,),
        )
        total_history = cursor.fetchone()[0]
        if total_history > 0:
            flash(
                f"Cannot delete '{title}'! This book has {total_history} historical loan record(s). "
                "Books with loan history cannot be deleted to preserve audit logs.",
                "error",
            )
            return redirect(url_for("view_books_page"))

        # Delete safe
        cursor.execute("DELETE FROM books WHERE id = ?", (id,))
        conn.commit()
        flash(f"Book '{title}' (ID #{id}) was permanently deleted from the library.", "success")
        return redirect(url_for("view_books_page"))

    except sqlite3.IntegrityError as e:
        conn.rollback()
        flash(f"Cannot delete book due to database constraint: {e}", "error")
        return redirect(url_for("view_books_page"))
    finally:
        conn.close()


# ==============================================================================
# Routes: Book Search
# ==============================================================================

@app.route("/search")
def search_page():
    """
    Search books across ID, title, and author with partial case-insensitive matching.
    """
    query = request.args.get("query", "").strip()
    search_by = request.args.get("search_by", "all").strip().lower()

    results = None

    if query:
        conn = get_connection()
        try:
            cursor = conn.cursor()

            if search_by == "id":
                try:
                    num_id = int(query)
                    cursor.execute(
                        "SELECT id, title, author, quantity FROM books WHERE id = ?",
                        (num_id,),
                    )
                except ValueError:
                    results = []
                    return render_template(
                        "search.html",
                        active_page="search",
                        query=query,
                        search_by=search_by,
                        results=results,
                    )
            elif search_by == "title":
                cursor.execute(
                    """
                    SELECT id, title, author, quantity FROM books
                    WHERE title LIKE ? COLLATE NOCASE
                    ORDER BY title ASC
                    """,
                    (f"%{query}%",),
                )
            elif search_by == "author":
                cursor.execute(
                    """
                    SELECT id, title, author, quantity FROM books
                    WHERE author LIKE ? COLLATE NOCASE
                    ORDER BY author ASC
                    """,
                    (f"%{query}%",),
                )
            else:  # 'all'
                cursor.execute(
                    """
                    SELECT id, title, author, quantity FROM books
                    WHERE title LIKE ? COLLATE NOCASE
                       OR author LIKE ? COLLATE NOCASE
                       OR CAST(id AS TEXT) = ?
                    ORDER BY id ASC
                    """,
                    (f"%{query}%", f"%{query}%", query),
                )

            rows = cursor.fetchall()
            results = [
                {"id": r[0], "title": r[1], "author": r[2], "quantity": r[3]}
                for r in rows
            ]
        finally:
            conn.close()

    return render_template(
        "search.html",
        active_page="search",
        query=query,
        search_by=search_by,
        results=results,
    )


# ==============================================================================
# Routes: Circulation (Issue & Return)
# ==============================================================================

@app.route("/issue", methods=["GET", "POST"])
def issue_book_page():
    """
    Issue an available book to a student.
    Atomically decreases book stock and creates an issue record.
    """
    selected_book_id = request.args.get("book_id", type=int)

    conn = get_connection()
    try:
        cursor = conn.cursor()

        if request.method == "POST":
            raw_book_id = request.form.get("book_id")
            raw_student_name = request.form.get("student_name")

            book_id = validate_positive_integer(raw_book_id, allow_zero=False)
            student_name = validate_string(raw_student_name)

            if not book_id:
                flash("Please select a valid book to issue.", "error")
                return redirect(url_for("issue_book_page"))

            if not student_name:
                flash("Student full name cannot be empty.", "error")
                return redirect(url_for("issue_book_page", book_id=book_id))

            # Fetch book and verify stock availability
            cursor.execute("SELECT id, title, quantity FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()

            if not book:
                flash(f"Book ID #{book_id} was not found in the library.", "error")
                return redirect(url_for("issue_book_page"))

            book_id, title, quantity = book

            if quantity <= 0:
                flash(f"Book '{title}' is currently OUT OF STOCK. Cannot issue.", "error")
                return redirect(url_for("issue_book_page"))

            # Atomic transaction
            issue_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                """
                INSERT INTO issued_books (book_id, student_name, issue_date, return_date)
                VALUES (?, ?, ?, NULL)
                """,
                (book_id, student_name, issue_date),
            )
            issue_id = cursor.lastrowid

            cursor.execute(
                "UPDATE books SET quantity = quantity - 1 WHERE id = ?",
                (book_id,),
            )

            conn.commit()
            flash(
                f"Book '{title}' (ID #{book_id}) successfully issued to {student_name}! "
                f"Issue ID #{issue_id}. Remaining stock: {quantity - 1}.",
                "success",
            )
            return redirect(url_for("history_page"))

        # GET: Fetch all books currently in stock
        cursor.execute("SELECT id, title, author, quantity FROM books WHERE quantity > 0 ORDER BY title ASC")
        available_books = [
            {"id": r[0], "title": r[1], "author": r[2], "quantity": r[3]}
            for r in cursor.fetchall()
        ]

        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return render_template(
            "issue_book.html",
            active_page="issue",
            available_books=available_books,
            selected_book_id=selected_book_id,
            current_timestamp=current_timestamp,
        )

    except sqlite3.Error as e:
        conn.rollback()
        flash(f"Database error during book issue: {e}", "error")
        return redirect(url_for("issue_book_page"))
    finally:
        conn.close()


@app.route("/return", methods=["GET", "POST"])
def return_book_page():
    """
    Process book returns by Issue ID.
    Atomically updates return_date and restores book stock.
    Prevents duplicate returns.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if request.method == "POST":
            raw_issue_id = request.form.get("issue_id")
            issue_id = validate_positive_integer(raw_issue_id, allow_zero=False)

            if not issue_id:
                flash("Please enter a valid numeric Issue ID.", "error")
                return redirect(url_for("return_book_page"))

            # Inspect issue record and joined book title
            cursor.execute(
                """
                SELECT i.id, i.book_id, b.title, i.student_name, i.return_date, b.quantity
                FROM issued_books i
                JOIN books b ON i.book_id = b.id
                WHERE i.id = ?
                """,
                (issue_id,),
            )
            record = cursor.fetchone()

            if not record:
                flash(f"Issue record ID #{issue_id} not found in the database.", "error")
                return redirect(url_for("return_book_page"))

            issue_id, book_id, title, student_name, return_date, current_qty = record

            # Duplicate return guard
            if return_date is not None:
                flash(
                    f"Book '{title}' was ALREADY returned on {return_date}. Duplicate return prevented.",
                    "warning",
                )
                return redirect(url_for("return_book_page"))

            # Atomic transaction
            return_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "UPDATE issued_books SET return_date = ? WHERE id = ?",
                (return_timestamp, issue_id),
            )
            cursor.execute(
                "UPDATE books SET quantity = quantity + 1 WHERE id = ?",
                (book_id,),
            )
            conn.commit()

            flash(
                f"Book '{title}' successfully returned by {student_name} at {return_timestamp}! "
                f"Updated in-stock inventory: {current_qty + 1}.",
                "success",
            )
            return redirect(url_for("return_book_page"))

        # GET: Display all currently unreturned active loans
        cursor.execute(
            """
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            WHERE i.return_date IS NULL
            ORDER BY i.id DESC
            """
        )
        active_issues = [
            {
                "id": r[0],
                "book_id": r[1],
                "title": r[2],
                "student_name": r[3],
                "issue_date": r[4],
            }
            for r in cursor.fetchall()
        ]

        return render_template(
            "return_book.html",
            active_page="return",
            active_issues=active_issues,
        )

    except sqlite3.Error as e:
        conn.rollback()
        flash(f"Database error during return: {e}", "error")
        return redirect(url_for("return_book_page"))
    finally:
        conn.close()


@app.route("/history")
def history_page():
    """
    Display full circulation history with status filters (all, active, returned).
    """
    current_status = request.args.get("status", "").strip().lower()

    conn = get_connection()
    try:
        cursor = conn.cursor()

        where_clause = ""
        if current_status == "active":
            where_clause = "WHERE i.return_date IS NULL"
        elif current_status == "returned":
            where_clause = "WHERE i.return_date IS NOT NULL"

        query = f"""
            SELECT i.id, i.book_id, b.title, i.student_name, i.issue_date, i.return_date
            FROM issued_books i
            JOIN books b ON i.book_id = b.id
            {where_clause}
            ORDER BY i.id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        history = [
            {
                "id": r[0],
                "book_id": r[1],
                "title": r[2],
                "student_name": r[3],
                "issue_date": r[4],
                "return_date": r[5],
            }
            for r in rows
        ]

        return render_template(
            "issue_history.html",
            active_page="history",
            history=history,
            current_status=current_status,
        )
    finally:
        conn.close()


# ==============================================================================
# Routes: Reports & CSV Export
# ==============================================================================

@app.route("/reports")
def reports_page():
    """
    Analytical reports dashboard with out-of-stock analysis and CSV downloads.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Aggregations
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity), 0) FROM books")
        total_titles, total_inventory = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM books WHERE quantity > 0")
        in_stock_titles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM books WHERE quantity = 0")
        out_of_stock_titles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books")
        total_issues = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NULL")
        currently_issued = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM issued_books WHERE return_date IS NOT NULL")
        returned_count = cursor.fetchone()[0]

        stats = {
            "total_titles": total_titles,
            "total_inventory": total_inventory,
            "in_stock_titles": in_stock_titles,
            "out_of_stock_titles": out_of_stock_titles,
            "total_issues": total_issues,
            "currently_issued": currently_issued,
            "returned_count": returned_count,
        }

        # Out of stock books list
        cursor.execute("SELECT id, title, author, quantity FROM books WHERE quantity = 0 ORDER BY title ASC")
        out_of_stock_books = [
            {"id": r[0], "title": r[1], "author": r[2], "quantity": r[3]}
            for r in cursor.fetchall()
        ]

        return render_template(
            "reports.html",
            active_page="reports",
            stats=stats,
            out_of_stock_books=out_of_stock_books,
        )
    finally:
        conn.close()


@app.route("/reports/export/books")
def export_books_csv_route():
    """
    Generate and stream Books Catalog CSV download. Also saves local server copy in exports/.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, author, quantity FROM books ORDER BY id ASC")
        books = cursor.fetchall()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"books_report_{timestamp}.csv"

        # Write to in-memory string buffer for streaming
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Book ID", "Title", "Author", "Quantity"])
        writer.writerows(books)

        csv_content = output.getvalue()
        output.close()

        # Also persist a server-side copy in exports/
        try:
            local_file = EXPORTS_DIR / filename
            with open(local_file, mode="w", newline="", encoding="utf-8") as f:
                f.write(csv_content)
        except OSError:
            pass

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )
    finally:
        conn.close()


@app.route("/reports/export/issues")
def export_issues_csv_route():
    """
    Generate and stream Loan History CSV download. Also saves local server copy in exports/.
    """
    conn = get_connection()
    try:
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

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"issue_records_report_{timestamp}.csv"

        output = io.StringIO()
        writer = csv.writer(output)
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

        csv_content = output.getvalue()
        output.close()

        # Save local copy in exports/
        try:
            local_file = EXPORTS_DIR / filename
            with open(local_file, mode="w", newline="", encoding="utf-8") as f:
                f.write(csv_content)
        except OSError:
            pass

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8",
            },
        )
    finally:
        conn.close()


# ==============================================================================
# Error Handlers
# ==============================================================================

@app.errorhandler(403)
def forbidden_error(error):
    return render_template("404.html"), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500


# ==============================================================================
# Development Server Launcher
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n[+] Starting Library Management Web Application...")
    print(f"[+] Local Server URL: http://127.0.0.1:{port}")
    print(f"[+] Press Ctrl+C to stop the web server.\n")
    app.run(host="127.0.0.1", port=port, debug=False)

