document.addEventListener('DOMContentLoaded', function () {
    const addBtn = document.getElementById('add-item');
    const tableBody = document.querySelector('tbody');
    const totalForms = document.getElementById('id_items-TOTAL_FORMS');

    if (addBtn && tableBody && totalForms) {
        addBtn.addEventListener('click', function (e) {
            e.preventDefault();

            const currentFormCount = parseInt(totalForms.value);
            const emptyForm = tableBody.querySelector('tr:first-child').cloneNode(true);

            const regex = new RegExp(`items-0-`, 'g');
            emptyForm.innerHTML = emptyForm.innerHTML.replace(regex, `items-${currentFormCount}-`);

            // Clear values
            const inputs = emptyForm.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.type === 'checkbox') {
                    input.checked = false;
                } else {
                    input.value = '';
                }
            });

            tableBody.appendChild(emptyForm);
            totalForms.value = currentFormCount + 1;
        });
    }
});
