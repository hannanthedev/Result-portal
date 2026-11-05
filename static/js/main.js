(function () {
    'use strict';

    var form   = document.getElementById('resultForm');
    var input  = document.getElementById('roll');
    var hint   = document.getElementById('hint');
    var rollBar   = document.querySelector('.bar--roll');
    var searchBar = document.querySelector('.bar--search');
    var submitBtn = document.getElementById('submitBtn');
    var label  = submitBtn.querySelector('.btn-label');

    // Footer year
    var year = document.getElementById('year');
    if (year) year.textContent = new Date().getFullYear();

    function showError(msg) {
        hint.textContent = msg;
        rollBar.classList.add('is-invalid');
        input.setAttribute('aria-invalid', 'true');
    }

    function clearError() {
        hint.textContent = '';
        rollBar.classList.remove('is-invalid');
        input.removeAttribute('aria-invalid');
    }

    // Keep digits only (handles typing and pasting), clear error as the user edits
    input.addEventListener('input', function () {
        var cleaned = input.value.replace(/\D+/g, '');
        if (cleaned !== input.value) input.value = cleaned;
        clearError();
    });

    form.addEventListener('submit', function (e) {
        var value = input.value.trim();

        if (!value) {
            e.preventDefault();
            showError('Please enter your roll number.');
            input.focus();
            return;
        }

        // Loading state; also guards against double submits
        searchBar.classList.add('is-loading');
        submitBtn.disabled = true;
        label.textContent = 'Searching…';
    });

    // Restore the button when coming back via the browser's back button
    window.addEventListener('pageshow', function (e) {
        if (e.persisted) {
            searchBar.classList.remove('is-loading');
            submitBtn.disabled = false;
            label.textContent = 'Search result';
        }
    });
})();
