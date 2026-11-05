(function () {
    'use strict';

    // Footer year
    var year = document.getElementById('year');
    if (year) year.textContent = new Date().getFullYear();

    // Print button
    var printBtn = document.getElementById('printBtn');
    if (printBtn) {
        printBtn.addEventListener('click', function () {
            window.print();
        });
    }
})();
