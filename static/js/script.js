/**
 * Library Management System - Client Side JavaScript
 * Provides responsive sidebar toggle, modal bindings, search filtering, and alerts auto-dismiss.
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const wrapper = document.getElementById('wrapper');
    
    if (sidebarToggleBtn && wrapper) {
        sidebarToggleBtn.addEventListener('click', function (e) {
            e.preventDefault();
            wrapper.classList.toggle('toggled');
        });
    }

    // 2. Auto-dismiss Bootstrap Alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (err) {
                alert.style.display = 'none';
            }
        }, 5000);
    });

    // 3. Delete Book Confirmation Modal Dynamic Population
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const bookId = button.getAttribute('data-book-id');
            const bookTitle = button.getAttribute('data-book-title');
            
            const modalTitleEl = deleteModal.querySelector('#deleteBookTitle');
            const deleteForm = deleteModal.querySelector('#deleteBookForm');
            
            if (modalTitleEl) {
                modalTitleEl.textContent = bookTitle || `Book #${bookId}`;
            }
            if (deleteForm) {
                deleteForm.action = `/books/delete/${bookId}`;
            }
        });
    }

    // 4. Quick Return Confirmation Modal Dynamic Population
    const returnModal = document.getElementById('returnConfirmModal');
    if (returnModal) {
        returnModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const issueId = button.getAttribute('data-issue-id');
            const bookTitle = button.getAttribute('data-book-title');
            const studentName = button.getAttribute('data-student-name');
            
            const modalIssueIdEl = returnModal.querySelector('#returnIssueId');
            const modalBookTitleEl = returnModal.querySelector('#returnBookTitle');
            const modalStudentNameEl = returnModal.querySelector('#returnStudentName');
            const modalIssueIdInput = returnModal.querySelector('#modalIssueIdInput');
            
            if (modalIssueIdEl) modalIssueIdEl.textContent = `#${issueId}`;
            if (modalBookTitleEl) modalBookTitleEl.textContent = bookTitle || 'Unknown Book';
            if (modalStudentNameEl) modalStudentNameEl.textContent = studentName || 'Unknown Student';
            if (modalIssueIdInput) modalIssueIdInput.value = issueId;
        });
    }

    // 5. Client-side Live Table Filter (for fast search on current page)
    const tableSearchInput = document.getElementById('tableSearchInput');
    if (tableSearchInput) {
        tableSearchInput.addEventListener('input', function () {
            const query = this.value.toLowerCase().trim();
            const tableRows = document.querySelectorAll('.filterable-table tbody tr');
            
            tableRows.forEach(function (row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

