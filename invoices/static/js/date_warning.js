(function () {
    'use strict';

    // Only run on add/change pages, not on the list view
    const body = document.body;
    const isChangeForm = body.classList.contains('change-form') || body.classList.contains('add-form');

    if (!isChangeForm) {
        // Exit early if we're on the list view
        return;
    }

    function checkDate() {
        const dateField = document.querySelector('#id_date');
        if (!dateField) return;

        const selectedDateStr = dateField.value;
        if (!selectedDateStr) {
            removeWarning();
            return;
        }

        const selectedDate = new Date(selectedDateStr);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (selectedDate < today) {
            showWarning(`⚠️ CAUTION: You have selected a date in the past! (${selectedDateStr})`);
        } else {
            removeWarning();
        }
    }

    function showWarning(message) {
        let warningDiv = document.querySelector('#past-date-warning');
        if (!warningDiv) {
            warningDiv = document.createElement('div');
            warningDiv.id = 'past-date-warning';
            warningDiv.className = 'px-4 py-3 mb-4 rounded-md border font-bold text-lg text-center animate-bounce';
            // Styling for "Scream" effect: Red background, white text, bold
            warningDiv.style.backgroundColor = '#fee2e2'; // red-100
            warningDiv.style.borderColor = '#ef4444'; // red-500
            warningDiv.style.color = '#b91c1c'; // red-700
            warningDiv.style.zIndex = '1000';
            warningDiv.style.position = 'sticky';
            warningDiv.style.top = '1rem';

            const container = document.querySelector('#content-main') || document.querySelector('form');
            if (container) {
                container.prepend(warningDiv);
            }
        }
        warningDiv.textContent = message;
    }

    function removeWarning() {
        const warningDiv = document.querySelector('#past-date-warning');
        if (warningDiv) {
            warningDiv.remove();
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        const dateField = document.querySelector('#id_date');
        if (dateField) {
            dateField.addEventListener('change', checkDate);
            // Initial check
            checkDate();

            // Unfold might use a custom date picker that doesn't trigger 'change' on the input immediately
            // Let's also listen for input events or mutations if needed.
            dateField.addEventListener('input', checkDate);

            // Watch for changes via MutationObserver as a fallback for some JS pickers
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                        checkDate();
                    }
                });
            });
            observer.observe(dateField, { attributes: true });
        }
    });

    // Special handling for Unfold/Flatpickr if we can detect it
    // Often we can wrap the check in a interval or listen on document for any change
    setInterval(checkDate, 1000); // Polling as a fallback for the "Scream" effect to be reliable

})();
