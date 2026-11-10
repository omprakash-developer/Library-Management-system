"""
Modules package for Library Management System.
Includes book management, issue management, search management, and report management.
"""

from modules.book_management import (
    add_book,
    view_books,
    update_book,
    delete_book,
)
from modules.issue_management import (
    issue_book,
    return_book,
    view_issue_records,
)
from modules.search_management import (
    search_books,
    search_by_id,
    search_by_title,
    search_by_author,
)
from modules.report_management import (
    generate_reports,
    export_csv_report,
)

__all__ = [
    "add_book",
    "view_books",
    "update_book",
    "delete_book",
    "issue_book",
    "return_book",
    "view_issue_records",
    "search_books",
    "search_by_id",
    "search_by_title",
    "search_by_author",
    "generate_reports",
    "export_csv_report",
]

