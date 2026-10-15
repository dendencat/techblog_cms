document.addEventListener('DOMContentLoaded', () => {
    // Changing "items per page" applies immediately.
    document.querySelectorAll('[data-autosubmit]').forEach((select) => {
        select.addEventListener('change', () => select.form.requestSubmit());
    });

    // Delete confirmation in a native <dialog> (Esc / focus handling for free).
    // Without JS the trash link falls back to the confirmation page.
    const dialog = document.getElementById('delete-dialog');
    if (!dialog || typeof dialog.showModal !== 'function') {
        return;
    }
    const form = document.getElementById('delete-form');
    const titleEl = dialog.querySelector('[data-delete-title]');

    document.querySelectorAll('[data-delete-article]').forEach((link) => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            form.action = link.dataset.action;
            titleEl.textContent = link.dataset.title;
            dialog.showModal();
        });
    });

    dialog.querySelectorAll('[data-close-dialog]').forEach((button) => {
        button.addEventListener('click', () => dialog.close());
    });
    // Clicking the backdrop closes the dialog.
    dialog.addEventListener('click', (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });
});
