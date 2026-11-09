
from config.database import get_connection


# 1. Add New Book
def add_book():

    print("\n===== ADD NEW BOOK =====")

    title = input("Enter book title: ").strip()
    author = input("Enter author name: ").strip()

    if not title or not author:
        print("Title and author cannot be empty!")
        return

    try:
        quantity = int(input("Enter book quantity: "))

        if quantity <= 0:
            print("Quantity must be greater than zero!")
            return

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO books (title, author, quantity)
            VALUES (?, ?, ?)
        """, (title, author, quantity))

        conn.commit()
        conn.close()

        print("Book added successfully!")

    except ValueError:
        print("Please enter a valid number!")

    except Exception as error:
        print("Error adding book:", error)


# 2. View All Books
def view_books():

    print("\n===== ALL LIBRARY BOOKS =====")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books ORDER BY id")

    books = cursor.fetchall()
    conn.close()

    if not books:
        print("No books available in the library.")
        return

    print("-" * 75)
    print(f"{'ID':<8}{'TITLE':<30}{'AUTHOR':<25}{'QUANTITY':<10}")
    print("-" * 75)

    for book in books:
        print(
            f"{book[0]:<8}"
            f"{book[1]:<30}"
            f"{book[2]:<25}"
            f"{book[3]:<10}"
        )

    print("-" * 75)


# 3. Update Book Details
def update_book():

    print("\n===== UPDATE BOOK =====")

    try:
        book_id = int(input("Enter book ID to update: "))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if book is None:
            print("Book not found!")
            conn.close()
            return

        print("\nCurrent Book Details:")
        print("Title:", book[1])
        print("Author:", book[2])
        print("Quantity:", book[3])

        title = input("Enter new title: ").strip()
        author = input("Enter new author: ").strip()
        quantity = int(input("Enter new quantity: "))

        if not title or not author or quantity < 0:
            print("Invalid book details!")
            conn.close()
            return

        cursor.execute("""
            UPDATE books
            SET title = ?, author = ?, quantity = ?
            WHERE id = ?
        """, (title, author, quantity, book_id))

        conn.commit()
        conn.close()

        print("Book updated successfully!")

    except ValueError:
        print("Please enter valid information!")

    except Exception as error:
        print("Error updating book:", error)


# 4. Delete Book
def delete_book():

    print("\n===== DELETE BOOK =====")

    try:
        book_id = int(input("Enter book ID to delete: "))

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT title FROM books WHERE id = ?",
            (book_id,)
        )

        book = cursor.fetchone()

        if book is None:
            print("Book not found!")
            conn.close()
            return

        # Check whether the book is currently issued
        cursor.execute("""
            SELECT COUNT(*)
            FROM issued_books
            WHERE book_id = ? AND return_date IS NULL
        """, (book_id,))

        active_issues = cursor.fetchone()[0]

        if active_issues > 0:
            print("Cannot delete! This book is currently issued.")
            conn.close()
            return

        confirmation = input(
            f"Delete '{book[0]}'? (yes/no): "
        ).strip().lower()

        if confirmation != "yes":
            print("Deletion cancelled.")
            conn.close()
            return

        cursor.execute(
            "DELETE FROM books WHERE id = ?",
            (book_id,)
        )

        conn.commit()
        conn.close()

        print("Book deleted successfully!")

    except ValueError:
        print("Please enter a valid book ID!")

    except Exception as error:
        print("Error deleting book:", error)
