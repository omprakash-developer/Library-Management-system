
import sqlite3
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database directory and file
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)

DATABASE_PATH = DATABASE_DIR / "library.db"


# Database connection function
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)

    # Enable foreign key support
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# Create database tables
def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # Books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0)
        )
    """)

    # Issued books table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issued_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            return_date TEXT DEFAULT NULL,

            FOREIGN KEY (book_id)
            REFERENCES books(id)
            ON DELETE RESTRICT
        )
    """)

    # Index for faster issue record searching
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_issued_books_book_id
        ON issued_books(book_id)
    """)

    conn.commit()
    conn.close()

    print("Database and tables created successfully!")


# Test database connection
def test_connection():

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]

        print("Database connection successful!")
        print("SQLite Version:", version)
        print("Database Location:", DATABASE_PATH)

        conn.close()

    except sqlite3.Error as error:
        print("Database Error:", error)


# Run database setup
if __name__ == "__main__":
    test_connection()
    create_tables()
