/**
 * Toast Auto-Initialization
 * Automatically shows all .toast elements on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toast').forEach(function(toastEl) {
        new bootstrap.Toast(toastEl).show();
    });
});
