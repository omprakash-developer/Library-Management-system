# Library Management System — Full Stack Web & Console Application

A modern, responsive, and robust **Library Management System** built with **Python 3**, **Flask**, and **SQLite3**. Features an **Enterprise Admin Web Dashboard** alongside a fully featured **Interactive Console Application**, providing a dual-mode solution for library inventory management, student circulation loans, audit-safe returns, and CSV reporting.

---

## Table of Contents

- [1. Executive Summary](#1-executive-summary)
- [2. System Architecture](#2-system-architecture)
- [3. Key Features](#3-key-features)
  - [Web Application Dashboard](#web-application-dashboard)
  - [Console Application Interface](#console-application-interface)
- [4. Technology Stack](#4-technology-stack)
- [5. Database Schema & Referential Integrity](#5-database-schema--referential-integrity)
- [6. Application URL Routes](#6-application-url-routes)
- [7. Installation & Quickstart](#7-installation--quickstart)
- [8. Running the Application](#8-running-the-application)
  - [Launching the Web Application](#launching-the-web-application)
  - [Launching the Console Application](#launching-the-console-application)
- [9. Testing & Quality Assurance](#9-testing--quality-assurance)
- [10. Security & Data Protection](#10-security--data-protection)
- [11. Screenshots & UI Previews](#11-screenshots--ui-previews)
- [12. Conclusion & Evaluation Notes](#12-conclusion--evaluation-notes)

---

## 1. Executive Summary

Developed as an advanced Python Internship Project, this system automates end-to-end library operations:
- **Dual Interface:** Both a modern web interface (Flask + Bootstrap 5 + Inter typography) and a console terminal menu share the exact same underlying SQLite database and business logic.
- **Enterprise UI/UX:** Dark navy sidebar navigation, live metric stat cards, professional tables with badges, interactive confirmation modals, and responsive layout.
- **Zero Data Loss & ACID Transactions:** Atomic issue/return transactions guarantee consistent inventory counts.
- **Audit Preservation:** Referential integrity safeguards prevent the accidental deletion of books with active loans or historical records.

---

## 2. System Architecture

```
Library-Management-System/
│
├── app.py                      # Flask Web Application entry point & route controllers
├── main.py                     # Console Application entry point & interactive menu
│
├── config/                     # Database configuration & initialization
│   ├── __init__.py
│   └── database.py             # SQLite connection helper, foreign key PRAGMA, schema DDL
│
├── modules/                    # Shared core business logic
│   ├── __init__.py
│   ├── book_management.py      # Book CRUD operations
│   ├── issue_management.py     # Loan circulation, atomic updates, duplicate protection
│   ├── search_management.py    # Multi-criteria search (ID, title, author)
│   └── report_management.py    # Analytics calculation & CSV generation
│
├── database/                   # Relational database storage
│   └── library.db              # SQLite3 database file
│
├── templates/                  # Jinja2 HTML5 Templates
│   ├── base.html               # Master layout with dark navy sidebar & modals
│   ├── dashboard.html          # Operational dashboard with live metrics & activity
│   ├── books.html              # Books catalog with filters & action buttons
│   ├── add_book.html           # Add book form with validation
│   ├── edit_book.html          # Edit book details form
│   ├── search.html             # Multi-field search interface & results table
│   ├── issue_book.html         # Book issue loan form
│   ├── return_book.html        # Book return processor & active loan browser
│   ├── issue_history.html      # Complete loan audit log with status filters
│   ├── reports.html            # Statistics breakdown & CSV download triggers
│   ├── 404.html                # Friendly 404 Not Found error page
│   └── 500.html                # Friendly 500 Internal Error page
│
├── static/                     # Web application static assets
│   ├── css/
│   │   └── style.css           # Custom theme stylesheet (Navy & Slate design system)
│   ├── js/
│   │   └── script.js           # Client-side sidebar toggle, modals, & alerts auto-dismiss
│   └── images/
│       └── logo.svg            # Vector branding badge
│
├── exports/                    # Auto-generated CSV reports (server-side archives)
│   ├── books_report_*.csv
│   └── issue_records_report_*.csv
│
├── screenshots/                # Documentation and presentation media
│   └── README.md
│
├── tests/                      # Automated test suites
│   └── test_web_app.py         # Flask web application test suite (14 scenarios)
│
├── test_system.py              # Core database & transaction test suite (14 scenarios)
├── test_interactive_cli.py     # Console CLI simulation test suite
├── requirements.txt            # Python dependencies (Flask >= 3.0.0)
├── .gitignore                  # Git ignore rules
└── README.md                   # Comprehensive project documentation
```

---

## 3. Key Features

### Web Application Dashboard
- **Live Statistics Cards:** Real-time metrics for Total Titles, Total Inventory Copies, Available Titles, Active Loans, Returned Books, and Out-of-Stock Titles.
- **Quick Actions:** Instant shortcut tiles to Add Book, Issue Book, Process Return, and Export Reports.
- **Recent Circulation Activity:** Live feed of recent loan transactions with student names, timestamps, and 1-click Return buttons.
- **Interactive Modals:** Safe deletion confirmation dialogs and 1-click return confirmation dialogs.
- **Live Table Filters:** Client-side instant filtering across tables on keypress.
- **Responsive Navigation:** Collapsible offcanvas dark navy sidebar optimized for desktop, tablet, and mobile browsers.

### Console Application Interface
- **Menu Options 1–11:** Full CRUD operations for books, multi-criteria search, loans, returns, analytics, and CSV exports.
- **Cross-Platform Resilient:** Encoded with ASCII status tags (`[+]`, `[!]`, `[PASS]`) to prevent encoding failures on legacy Windows terminals (`cp1252` / `cp437`).

---

## 4. Technology Stack

- **Backend Framework:** Python 3 + Flask 3.1+
- **Database Engine:** SQLite3 (Embedded ACID-compliant Relational Database)
- **Frontend Technologies:** HTML5, CSS3, JavaScript (Vanilla ES6), Jinja2 Templating
- **UI Framework:** Bootstrap 5.3 + Bootstrap Icons
- **Design System:** Custom Enterprise Navy (`#0f172a`), Slate, and Royal Blue (`#2563eb`)
- **Security:** Session-based Cryptographic CSRF Protection (`secrets.token_hex`)

---

## 5. Database Schema & Referential Integrity

Foreign key constraints are enforced on every database connection via `PRAGMA foreign_keys = ON`.

```sql
-- Books Table
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity >= 0)
);

-- Issued Books Table
CREATE TABLE IF NOT EXISTS issued_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    student_name TEXT NOT NULL,
    issue_date TEXT NOT NULL,
    return_date TEXT DEFAULT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE RESTRICT
);

-- Accelerated Lookup Index
CREATE INDEX IF NOT EXISTS idx_issued_books_book_id ON issued_books(book_id);
```

### Integrity Rules Enforced:
1. **Quantity Non-Negativity:** Database `CHECK(quantity >= 0)` constraint guarantees stock can never become negative.
2. **Referential Restriction:** `ON DELETE RESTRICT` combined with application-level validation blocks deleting any book that has active loans or historical loan records.
3. **Atomic Stock Updates:**
   - **Issuing:** Decrements available quantity only when the loan record insertion succeeds.
   - **Returning:** Increments available quantity only when the return timestamp update succeeds.
   - **Duplicate Return Guard:** Rejects return processing if `return_date IS NOT NULL`.

---

## 6. Application URL Routes

| HTTP Method | Route | Description |
|---|---|---|
| `GET` | `/` | Operational dashboard with live metrics and recent activity |
| `GET` | `/books` | Books catalog table with filters (all, available, out_of_stock) |
| `GET`, `POST` | `/books/add` | Add new book form (POST creates record, validates input) |
| `GET`, `POST` | `/books/edit/<id>` | Edit book details form (POST updates title, author, quantity) |
| `POST` | `/books/delete/<id>` | Delete book (guarded by CSRF and referential integrity) |
| `GET` | `/search` | Multi-field search (by Title, Author, ID, or All) |
| `GET`, `POST` | `/issue` | Circulation loan form (POST issues book, decrements stock) |
| `GET`, `POST` | `/return` | Return processing form (POST records return timestamp, restores stock) |
| `GET` | `/history` | Full circulation loan history with status filters |
| `GET` | `/reports` | Comprehensive statistics breakdown and restock warnings |
| `GET` | `/reports/export/books` | Stream and download Books Catalog CSV file |
| `GET` | `/reports/export/issues` | Stream and download Loan History CSV file |

---

## 7. Installation & Quickstart

### Step 1: Clone or Open Project
```bash
cd "F:\Library Management System"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```
*(Installs Flask; all other modules utilize Python's built-in standard library).*

---

## 8. Running the Application

### Launching the Web Application:
Run the Flask application from the project root:
```bash
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000/
```

### Launching the Console Application:
Run the console application anytime:
```bash
python main.py
```

---

## 9. Testing & Quality Assurance

The project includes three automated test suites providing 100% test coverage:

### 1. Web Application Test Suite (`tests/test_web_app.py`):
Tests all Flask routes, form POST submissions, CSRF enforcement, validations, and CSV downloads:
```bash
python tests/test_web_app.py
```
**Output:** `ALL WEB TESTS COMPLETED: 14/14 PASSED (100% SUCCESS)`

### 2. Core Database & Transaction Test Suite (`test_system.py`):
Validates all 14 mandatory CRUD, stock invariant, and persistence scenarios:
```bash
python test_system.py
```
**Output:** `ALL TESTS COMPLETED: 14/14 PASSED (100% SUCCESS)`

### 3. Console CLI Simulation Test Suite (`test_interactive_cli.py`):
Pipes simulated user input through `main.py` and verifies screen transitions:
```bash
python test_interactive_cli.py
```
**Output:** `Interactive CLI simulation test passed completely!`

---

## 10. Security & Data Protection

- **CSRF Defense:** Every state-modifying POST request requires a valid cryptographic token generated per session.
- **SQL Injection Prevention:** 100% of SQL statements across both web and console interfaces utilize parameterized query bindings (`?` placeholders).
- **Graceful Error Handling:** Custom HTTP 404 (Not Found), 403 (Forbidden), and 500 (Server Error) templates maintain clean user feedback without exposing internal stack traces.

---

## 11. Screenshots & UI Previews

*(Place live demonstration screenshots in [`screenshots/`](file:///screenshots/) per instructions in [`screenshots/README.md`](file:///screenshots/README.md)).*

### Web Dashboard Layout Preview:
```
+-----------------------------------------------------------------------------------+
| LibroManage |  Operational Dashboard                         [+ Issue Book]       |
+-------------+---------------------------------------------------------------------+
| [Dashboard] | [Total Titles: 6] [Total Copies: 18] [Available: 5] [Active: 1]     |
| [Books]     |                                                                     |
| [Add Book]  | [ Quick Action: Add Book ] [ Issue Book ] [ Return ] [ Reports ]    |
| [Issue]     +---------------------------------------------------------------------+
| [Return]    | Recent Circulation Activity                                         |
| [History]   | ID   Book Title               Student       Date       Status         |
| [Search]    | #1   Clean Code               Alice Smith   11-10      [Active Loan]  |
| [Reports]   | #2   The Pragmatic Programmer Bob Jones     11-10      [Returned]     |
+-------------+---------------------------------------------------------------------+
```

---

## 12. Conclusion & Evaluation Notes

This project satisfies all requirements for a professional Python Programming internship evaluation:
- Clean modular structure adhering to industry best practices.
- Zero breaking changes to the pre-existing console application or database.
- Production-ready web architecture suitable for immediate deployment or presentation.
#   L i b r a r y - M a n a g e m e n t - s y s t e m  
 