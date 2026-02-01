document.addEventListener('DOMContentLoaded', function () {
    console.log('Admin Autofill JS loaded [DEBUG VERSION]');

    // Helper to update fields
    function updateRow(rowPrefix, description, price) {
        if (!rowPrefix) return;

        console.log(`Updating row ${rowPrefix}: Desc=${description}, Price=${price}`);

        const descField = document.querySelector(`#id_${rowPrefix}-description`);
        const priceField = document.querySelector(`#id_${rowPrefix}-unit_price`);

        if (descField) {
            descField.value = description;
            descField.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            console.warn(`Description field #id_${rowPrefix}-description not found`);
        }

        if (priceField) {
            priceField.value = price;
            priceField.dispatchEvent(new Event('input', { bubbles: true }));
            priceField.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
            console.warn(`Price field #id_${rowPrefix}-unit_price not found`);
        }
    }

    // Listen for select2 events using jQuery (Django admin includes it)
    if (typeof django !== 'undefined' && django.jQuery) {
        console.log('django.jQuery is available. Setting up listener.');

        // Use a more generic selector to catch any product select
        // 'select[id$="-product"]' matches id_items-0-product
        django.jQuery(document).on('select2:select', 'select[id$="-product"]', function (e) {
            const selectId = e.target.id;
            console.log('Select2 select triggered on:', selectId);

            // Expected format: id_PREFIX-INDEX-product or similar
            // We need to capture the middle part: PREFIX-INDEX
            // e.g. "id_items-0-product" -> "items-0"

            const match = selectId.match(/^id_(.+)-product$/);
            if (!match) {
                console.warn('Could not extract row prefix from ID:', selectId);
                return;
            }

            const rowPrefix = match[1];
            const data = e.params.data;
            const productId = data.id;

            console.log(`Selected Product ID: ${productId}, Row Prefix: ${rowPrefix}`);

            if (productId) {
                fetch(`/api/product/${productId}/`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Network response was not ok: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Fetched product data:', data);
                        updateRow(rowPrefix, data.description, data.unit_price);
                    })
                    .catch(err => console.error('Error fetching product details:', err));
            }
        });
    } else {
        console.error('django.jQuery not found! Auto-fill will not work.');
    }
});
