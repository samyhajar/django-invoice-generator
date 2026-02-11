document.addEventListener('DOMContentLoaded', function () {
    const addButtons = document.querySelectorAll('.add-item-btn');
    const totalForms = document.getElementById('id_items-TOTAL_FORMS');
    const templateRow = document.getElementById('item-row-template');

    // Get company profile mileage rates from data attributes
    const container = document.querySelector('[data-mileage-base-rate]');
    const mileageBaseRate = parseFloat(container?.dataset.mileageBaseRate || '0.42');
    const mileageExtraRate = parseFloat(container?.dataset.mileageExtraRate || '0.05');

    if (addButtons.length > 0 && totalForms && templateRow) {
        addButtons.forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.preventDefault();

                const itemType = this.getAttribute('data-type');
                const tableId = this.getAttribute('data-table');
                const tableBody = document.getElementById(tableId).querySelector('tbody');
                const currentFormCount = parseInt(totalForms.value);

                // Clone the template and replace __prefix__ with the current form count
                const newRowHtml = templateRow.innerHTML.replace(/__prefix__/g, currentFormCount);

                // Create a temporary element to parse the HTML string
                const temp = document.createElement('tbody');
                temp.innerHTML = newRowHtml;
                const newRow = temp.firstElementChild;

                // Set the correct item type in the hidden field
                const typeInput = newRow.querySelector('.item-type-select');
                if (typeInput) {
                    typeInput.value = itemType;
                }

                // Show/hide the "Number of People" field based on item type
                const peopleField = newRow.querySelector('.mileage-people-field');
                const spacer = newRow.querySelector('.mileage-spacer');
                if (itemType === 'mileage') {
                    if (peopleField) peopleField.style.display = 'block';
                    if (spacer) spacer.style.display = 'none';
                } else {
                    if (peopleField) peopleField.style.display = 'none';
                    if (spacer) spacer.style.display = 'block';
                }

                tableBody.appendChild(newRow);
                totalForms.value = currentFormCount + 1;

                // Attach event listeners to the new row
                attachCalculationListeners(newRow);
            });
        });
    }

    // Function to calculate and update total for a row
    function updateRowTotal(row) {
        const quantityInput = row.querySelector('.item-quantity');
        const priceInput = row.querySelector('.item-price');
        const peopleInput = row.querySelector('.mileage-people');
        const totalDisplay = row.querySelector('.item-total');
        const typeInput = row.querySelector('.item-type-select');

        if (!quantityInput || !totalDisplay) return;

        const quantity = parseFloat(quantityInput.value) || 0;
        let unitPrice = 0;

        // For mileage, calculate price based on distance and number of people
        if (typeInput && typeInput.value === 'mileage' && peopleInput) {
            const numPeople = parseInt(peopleInput.value) || 1;
            const extraPeople = Math.max(0, numPeople - 1);
            unitPrice = mileageBaseRate + (extraPeople * mileageExtraRate);

            // Update the price input to show the calculated price
            if (priceInput) {
                priceInput.value = unitPrice.toFixed(2);
            }
        } else if (priceInput) {
            unitPrice = parseFloat(priceInput.value) || 0;
        }

        const total = quantity * unitPrice;
        totalDisplay.textContent = `€${total.toFixed(2)}`;
    }

    // Function to attach calculation listeners to a row
    function attachCalculationListeners(row) {
        const inputs = row.querySelectorAll('.item-quantity, .item-price, .mileage-people');
        inputs.forEach(input => {
            input.addEventListener('input', () => updateRowTotal(row));
            input.addEventListener('change', () => updateRowTotal(row));
        });

        // Initial calculation
        updateRowTotal(row);
    }

    // Attach listeners to existing rows on page load
    document.querySelectorAll('tr[data-row-id]').forEach(row => {
        attachCalculationListeners(row);
    });
});
