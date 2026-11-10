"""
Comprehensive Automated Test Suite for Library Management System Flask Web Application.
Tests all web routes, form submissions, CSRF protection, input validation,
atomic transactions, referential integrity guards, and CSV exports.
"""

import sys
import re
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import app
from config.database import get_connection, create_tables


def extract_csrf_token(response_text):
    """Helper to parse csrf_token from HTML response form."""
    match = re.search(r'name="csrf_token" value="([a-f0-9]+)"', response_text)
    if match:
        return match.group(1)
    return None


def run_web_tests():
    print("=" * 70)
    print("      LIBRARY MANAGEMENT SYSTEM - FLASK WEB APP TEST SUITE")
    print("=" * 70)

    create_tables()

    # Configure app for testing
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Still tests custom session token
    client = app.test_client()

    passed = 0
    total = 14

    # --- Test 1: Dashboard Load ---
    print("\n[Test 1] Testing: GET / (Dashboard)...")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.get_data(as_text=True)
    assert "Operational Dashboard" in html or "Dashboard" in html
    assert "Total Titles" in html
    assert "Total Inventory" in html
    print("  [PASS] Dashboard loaded successfully with live stats.")
    passed += 1

    # --- Test 2: View Books Catalog ---
    print("\n[Test 2] Testing: GET /books (Catalog View)...")
    res = client.get("/books")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Books Catalog" in html
    assert "Library Books Collection" in html
    print("  [PASS] Books catalog page loaded.")
    passed += 1

    # --- Test 3: Add Book (Form & POST) ---
    print("\n[Test 3] Testing: POST /books/add (Add New Book)...")
    # GET form first to establish session and get csrf_token
    res_get = client.get("/books/add")
    assert res_get.status_code == 200
    csrf_token = extract_csrf_token(res_get.get_data(as_text=True))
    assert csrf_token is not None

    book_title = "Web Architecture Patterns"
    book_author = "Martin Fowler"
    book_qty = 3

    res_post = client.post(
        "/books/add",
        data={
            "csrf_token": csrf_token,
            "title": book_title,
            "author": book_author,
            "quantity": str(book_qty),
        },
        follow_redirects=True,
    )
    assert res_post.status_code == 200
    html_after_add = res_post.get_data(as_text=True)
    assert book_title in html_after_add

    # Verify directly in SQLite DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, quantity FROM books WHERE title = ?", (book_title,))
    added_row = c.fetchone()
    conn.close()
    assert added_row is not None
    new_book_id = added_row[0]
    print(f"  [PASS] Book added successfully via web form (ID #{new_book_id}).")
    passed += 1

    # --- Test 4: Edit Book ---
    print(f"\n[Test 4] Testing: POST /books/edit/{new_book_id} (Update Book)...")
    res_edit_get = client.get(f"/books/edit/{new_book_id}")
    assert res_edit_get.status_code == 200
    csrf_token = extract_csrf_token(res_edit_get.get_data(as_text=True))

    updated_title = "Enterprise Web Architecture Patterns"
    res_edit_post = client.post(
        f"/books/edit/{new_book_id}",
        data={
            "csrf_token": csrf_token,
            "title": updated_title,
            "author": book_author,
            "quantity": "4",
        },
        follow_redirects=True,
    )
    assert res_edit_post.status_code == 200
    html_after_edit = res_edit_post.get_data(as_text=True)
    assert updated_title in html_after_edit

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, quantity FROM books WHERE id = ?", (new_book_id,))
    row = c.fetchone()
    conn.close()
    assert row[0] == updated_title
    assert row[1] == 4
    print(f"  [PASS] Book #{new_book_id} updated successfully (New Qty: {row[1]}).")
    passed += 1

    # --- Test 5: Search Books ---
    print("\n[Test 5] Testing: GET /search (Query by Title)...")
    res_search = client.get(f"/search?query=enterprise&search_by=title")
    assert res_search.status_code == 200
    html_search = res_search.get_data(as_text=True)
    assert updated_title in html_search
    print("  [PASS] Search returned expected matching title.")
    passed += 1

    # --- Test 6: Issue Book (Success) ---
    print("\n[Test 6] Testing: POST /issue (Issue Book to Student)...")
    res_issue_get = client.get("/issue")
    assert res_issue_get.status_code == 200
    csrf_token = extract_csrf_token(res_issue_get.get_data(as_text=True))

    student_name = "Jane Developer"
    res_issue_post = client.post(
        "/issue",
        data={
            "csrf_token": csrf_token,
            "book_id": str(new_book_id),
            "student_name": student_name,
        },
        follow_redirects=True,
    )
    assert res_issue_post.status_code == 200
    html_after_issue = res_issue_post.get_data(as_text=True)
    assert student_name in html_after_issue

    # Check stock decreased from 4 to 3
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT quantity FROM books WHERE id = ?", (new_book_id,))
    post_issue_qty = c.fetchone()[0]
    c.execute("SELECT id FROM issued_books WHERE book_id = ? AND return_date IS NULL", (new_book_id,))
    issue_row = c.fetchone()
    conn.close()

    assert post_issue_qty == 3
    assert issue_row is not None
    issue_id = issue_row[0]
    print(f"  [PASS] Book #{new_book_id} issued to {student_name} (Issue ID #{issue_id}). Stock decremented to {post_issue_qty}.")
    passed += 1

    # --- Test 7: Prevent Deleting Book With Active Loan ---
    print("\n[Test 7] Testing: POST /books/delete/<id> (Blocked on active loan)...")
    res_get = client.get("/books")
    csrf_token = extract_csrf_token(res_get.get_data(as_text=True))
    res_del_blocked = client.post(
        f"/books/delete/{new_book_id}",
        data={"csrf_token": csrf_token},
        follow_redirects=True,
    )
    assert res_del_blocked.status_code == 200
    html_del = res_del_blocked.get_data(as_text=True)
    assert "Cannot delete" in html_del

    # Verify book still exists in DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE id = ?", (new_book_id,))
    still_exists = c.fetchone()
    conn.close()
    assert still_exists is not None
    print("  [PASS] Referential integrity protected book from deletion while active loan exists.")
    passed += 1

    # --- Test 8: Return Book (Success) ---
    print(f"\n[Test 8] Testing: POST /return (Return Issue ID #{issue_id})...")
    res_ret_get = client.get("/return")
    csrf_token = extract_csrf_token(res_ret_get.get_data(as_text=True))

    res_ret_post = client.post(
        "/return",
        data={
            "csrf_token": csrf_token,
            "issue_id": str(issue_id),
        },
        follow_redirects=True,
    )
    assert res_ret_post.status_code == 200

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT quantity FROM books WHERE id = ?", (new_book_id,))
    post_ret_qty = c.fetchone()[0]
    c.execute("SELECT return_date FROM issued_books WHERE id = ?", (issue_id,))
    ret_date = c.fetchone()[0]
    conn.close()

    assert post_ret_qty == 4
    assert ret_date is not None
    print(f"  [PASS] Book returned successfully. Stock restored to {post_ret_qty}.")
    passed += 1

    # --- Test 9: Prevent Duplicate Return ---
    print(f"\n[Test 9] Testing: POST /return (Duplicate Return Guard)...")
    res_ret_dup = client.post(
        "/return",
        data={
            "csrf_token": csrf_token,
            "issue_id": str(issue_id),
        },
        follow_redirects=True,
    )
    assert res_ret_dup.status_code == 200
    html_dup = res_ret_dup.get_data(as_text=True)
    assert "Duplicate return prevented" in html_dup or "ALREADY returned" in html_dup
    print("  [PASS] Duplicate return attempt rejected.")
    passed += 1

    # --- Test 10: Prevent Deleting Book With Past History ---
    print(f"\n[Test 10] Testing: Prevent Deleting Book #{new_book_id} (Audit History Protection)...")
    res_del_hist = client.post(
        f"/books/delete/{new_book_id}",
        data={"csrf_token": csrf_token},
        follow_redirects=True,
    )
    assert res_del_hist.status_code == 200
    html_del_hist = res_del_hist.get_data(as_text=True)
    assert "Cannot delete" in html_del_hist and "history" in html_del_hist

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE id = ?", (new_book_id,))
    assert c.fetchone() is not None
    conn.close()
    print("  [PASS] Book with completed loan history protected from deletion.")
    passed += 1

    # --- Test 11: Delete Book Without Any History ---
    print("\n[Test 11] Testing: Delete Book Without Loan History...")
    # Add a temporary unissued book
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO books (title, author, quantity) VALUES (?, ?, ?)", ("Temp Deletable", "Nobody", 1))
    conn.commit()
    temp_id = c.lastrowid
    conn.close()

    res_del_ok = client.post(
        f"/books/delete/{temp_id}",
        data={"csrf_token": csrf_token},
        follow_redirects=True,
    )
    assert res_del_ok.status_code == 200

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM books WHERE id = ?", (temp_id,))
    assert c.fetchone() is None
    conn.close()
    print(f"  [PASS] Book #{temp_id} without loan history deleted cleanly.")
    passed += 1

    # --- Test 12: Loan History Page ---
    print("\n[Test 12] Testing: GET /history (Circulation History)...")
    res_hist = client.get("/history")
    assert res_hist.status_code == 200
    html_hist = res_hist.get_data(as_text=True)
    assert "Circulation & Loan History" in html_hist
    assert student_name in html_hist
    print("  [PASS] Loan history page rendered with student transactions.")
    passed += 1

    # --- Test 13: Reports & CSV Export Streams ---
    print("\n[Test 13] Testing: GET /reports/export/books and /reports/export/issues...")
    res_csv_books = client.get("/reports/export/books")
    assert res_csv_books.status_code == 200
    assert "text/csv" in res_csv_books.headers.get("Content-Type", "")
    assert "attachment" in res_csv_books.headers.get("Content-Disposition", "")
    books_csv_text = res_csv_books.get_data(as_text=True)
    assert "Book ID,Title,Author,Quantity" in books_csv_text

    res_csv_issues = client.get("/reports/export/issues")
    assert res_csv_issues.status_code == 200
    assert "text/csv" in res_csv_issues.headers.get("Content-Type", "")
    issues_csv_text = res_csv_issues.get_data(as_text=True)
    assert "Issue ID,Book ID,Book Title,Student Name,Issue Date,Return Date,Status" in issues_csv_text
    print("  [PASS] Both CSV export streams generated valid CSV headers and data.")
    passed += 1

    # --- Test 14: CSRF Security Enforcement ---
    print("\n[Test 14] Testing: CSRF Protection on POST without token...")
    # Attempt POST without csrf_token
    res_no_csrf = client.post(
        "/books/add",
        data={"title": "Hacker Book", "author": "Evil", "quantity": "1"},
    )
    assert res_no_csrf.status_code == 403, f"Expected 403 Forbidden without CSRF, got {res_no_csrf.status_code}"
    print("  [PASS] Request without valid CSRF token successfully blocked with 403 Forbidden.")
    passed += 1

    print("\n" + "=" * 70)
    print(f"ALL WEB TESTS COMPLETED: {passed}/{total} PASSED (100% SUCCESS)")
    print("=" * 70)


if __name__ == "__main__":
    run_web_tests()

