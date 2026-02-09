/**
 * Shadcn-style Web Components for Django Invoice Generator
 * These components follow the shadcn/ui design system with Tailwind CSS
 */

// Button Component
class CButton extends HTMLElement {
    connectedCallback() {
        const variant = this.getAttribute('variant') || 'default';
        const size = this.getAttribute('size') || 'default';
        const type = this.getAttribute('type') || 'button';
        const className = this.getAttribute('class') || '';

        const baseClasses = 'inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';

        const variantClasses = {
            default: 'bg-primary text-primary-foreground hover:bg-primary/90',
            destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
            outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
            secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
            ghost: 'hover:bg-accent hover:text-accent-foreground',
            link: 'text-primary underline-offset-4 hover:underline'
        };

        const sizeClasses = {
            default: 'h-10 px-4 py-2',
            sm: 'h-9 rounded-md px-3',
            lg: 'h-11 rounded-md px-8',
            icon: 'h-10 w-10'
        };

        const button = document.createElement('button');
        button.type = type;
        button.className = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
        button.innerHTML = this.innerHTML;

        // Copy all other attributes
        Array.from(this.attributes).forEach(attr => {
            if (!['variant', 'size', 'type', 'class'].includes(attr.name)) {
                button.setAttribute(attr.name, attr.value);
            }
        });

        this.replaceWith(button);
    }
}

// Card Component
class CCard extends HTMLElement {
    connectedCallback() {
        const title = this.getAttribute('title');
        const description = this.getAttribute('description');
        const className = this.getAttribute('class') || '';

        const card = document.createElement('div');
        card.className = `rounded-lg border border-border bg-card text-card-foreground shadow-lg border-t-4 border-t-olive transition-all duration-300 hover:shadow-xl hover:-translate-y-1 ${className}`;

        let headerHTML = '';
        if (title || description) {
            headerHTML = `
                <div class="flex flex-col space-y-1.5 p-6">
                    ${title ? `<h3 class="text-2xl font-semibold leading-none tracking-tight">${title}</h3>` : ''}
                    ${description ? `<p class="text-sm text-muted-foreground">${description}</p>` : ''}
                </div>
            `;
        }

        card.innerHTML = `
            ${headerHTML}
            <div class="p-6 pt-0">${this.innerHTML}</div>
        `;

        this.replaceWith(card);
    }
}

// Label Component
class CLabel extends HTMLElement {
    connectedCallback() {
        const htmlFor = this.getAttribute('for');
        const className = this.getAttribute('class') || '';

        const label = document.createElement('label');
        if (htmlFor) label.htmlFor = htmlFor;
        label.className = `text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 ${className}`;
        label.innerHTML = this.innerHTML;

        this.replaceWith(label);
    }
}

// Input Component
class CInput extends HTMLElement {
    connectedCallback() {
        const type = this.getAttribute('type') || 'text';
        const name = this.getAttribute('name');
        const id = this.getAttribute('id');
        const value = this.getAttribute('value') || '';
        const placeholder = this.getAttribute('placeholder') || '';
        const className = this.getAttribute('class') || '';
        const step = this.getAttribute('step');
        const required = this.hasAttribute('required');

        const input = document.createElement('input');
        input.type = type;
        if (name) input.name = name;
        if (id) input.id = id;
        if (value) input.value = value;
        if (placeholder) input.placeholder = placeholder;
        if (step) input.step = step;
        if (required) input.required = true;

        // Added placeholder:text-muted-foreground/50 for lighter placeholder text
        input.className = `flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`;

        // Copy all other attributes
        Array.from(this.attributes).forEach(attr => {
            if (!['type', 'name', 'id', 'value', 'placeholder', 'class', 'step', 'required'].includes(attr.name)) {
                input.setAttribute(attr.name, attr.value);
            }
        });

        this.replaceWith(input);
    }
}

// Textarea Component
class CTextarea extends HTMLElement {
    connectedCallback() {
        const name = this.getAttribute('name');
        const id = this.getAttribute('id');
        const rows = this.getAttribute('rows') || '3';
        const placeholder = this.getAttribute('placeholder') || '';
        const className = this.getAttribute('class') || '';
        const required = this.hasAttribute('required');

        const textarea = document.createElement('textarea');
        if (name) textarea.name = name;
        if (id) textarea.id = id;
        textarea.rows = rows;
        if (placeholder) textarea.placeholder = placeholder;
        if (required) textarea.required = true;
        textarea.value = this.textContent.trim();

        // Added placeholder:text-muted-foreground/50
        textarea.className = `flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`;

        // Copy all other attributes
        Array.from(this.attributes).forEach(attr => {
            if (!['name', 'id', 'rows', 'placeholder', 'class', 'required'].includes(attr.name)) {
                textarea.setAttribute(attr.name, attr.value);
            }
        });

        this.replaceWith(textarea);
    }
}

// Checkbox Component
class CCheckbox extends HTMLElement {
    connectedCallback() {
        const name = this.getAttribute('name');
        const id = this.getAttribute('id');
        const checked = this.hasAttribute('checked');
        const label = this.getAttribute('label');
        const className = this.getAttribute('class') || '';

        const wrapper = document.createElement('div');
        wrapper.className = `flex items-center space-x-2 ${className}`;

        // Hidden input for form submission
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.className = 'hidden';
        if (name) input.name = name;
        if (id) input.id = id;
        if (checked) input.checked = true;

        // Custom styled checkbox
        const visualCheckbox = document.createElement('button');
        visualCheckbox.type = 'button';
        visualCheckbox.className = `peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${checked ? 'bg-primary text-primary-foreground' : 'bg-background'}`;
        visualCheckbox.setAttribute('role', 'checkbox');
        visualCheckbox.setAttribute('aria-checked', checked);

        // Checkmark icon
        visualCheckbox.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="h-3 w-3 ${checked ? '' : 'hidden'}"><polyline points="20 6 9 17 4 12"></polyline></svg>
        `;

        // Toggle logic
        const toggle = () => {
            input.checked = !input.checked;
            visualCheckbox.setAttribute('aria-checked', input.checked);
            const icon = visualCheckbox.querySelector('svg');
            if (input.checked) {
                visualCheckbox.classList.remove('bg-background');
                visualCheckbox.classList.add('bg-primary', 'text-primary-foreground');
                icon.classList.remove('hidden');
            } else {
                visualCheckbox.classList.add('bg-background');
                visualCheckbox.classList.remove('bg-primary', 'text-primary-foreground');
                icon.classList.add('hidden');
            }
        };

        visualCheckbox.addEventListener('click', toggle);

        wrapper.appendChild(input);
        wrapper.appendChild(visualCheckbox);

        if (label) {
            const labelEl = document.createElement('label');
            labelEl.className = 'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer';
            labelEl.textContent = label;
            labelEl.addEventListener('click', toggle);
            wrapper.appendChild(labelEl);
        }

        this.replaceWith(wrapper);
    }
}

// Select Component
class CSelect extends HTMLElement {
    connectedCallback() {
        const name = this.getAttribute('name');
        const id = this.getAttribute('id');
        const className = this.getAttribute('class') || '';
        const required = this.hasAttribute('required');

        const select = document.createElement('select');
        if (name) select.name = name;
        if (id) select.id = id;
        if (required) select.required = true;
        select.innerHTML = this.innerHTML;

        select.className = `flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`;

        // Copy all other attributes
        Array.from(this.attributes).forEach(attr => {
            if (!['name', 'id', 'class', 'required'].includes(attr.name)) {
                select.setAttribute(attr.name, attr.value);
            }
        });

        this.replaceWith(select);
    }
}



// Register all components
customElements.define('c-button', CButton);
customElements.define('c-card', CCard);
customElements.define('c-label', CLabel);
customElements.define('c-input', CInput);
customElements.define('c-select', CSelect);
customElements.define('c-textarea', CTextarea);
customElements.define('c-checkbox', CCheckbox);
