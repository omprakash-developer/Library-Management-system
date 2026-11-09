
from config.database import create_tables

from modules.book_management import (
    add_book,
    view_books,
    update_book,
    delete_book
)


def main():

    create_tables()

    while True:

        print("\n================================")
        print("     LIBRARY MANAGEMENT SYSTEM")
        print("================================")

        print("1. Add New Book")
        print("2. View All Books")
        print("3. Update Book")
        print("4. Delete Book")
        print("5. Exit")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            add_book()

        elif choice == "2":
            view_books()

        elif choice == "3":
            update_book()

        elif choice == "4":
            delete_book()

        elif choice == "5":
            print("Thank you for using Library System!")
            break

        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()
