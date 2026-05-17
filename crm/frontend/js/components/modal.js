/**
 * Streamux CRM — Modal Manager
 * Handles opening, closing, and forms within modals.
 */
const StreamuxModal = (() => {
    function open(modalId, setupCallback = null) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        // Clear previous errors
        const errs = modal.querySelectorAll('.form-error');
        errs.forEach(e => e.remove());
        
        if (setupCallback) setupCallback(modal);
        
        modal.classList.add('active');
        
        // Focus first input
        setTimeout(() => {
            const firstInput = modal.querySelector('input:not([type="hidden"]), textarea, select');
            if(firstInput) firstInput.focus();
        }, 100);
    }

    function close(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.remove('active');
    }

    function showError(formId, fieldName, message) {
        const form = document.getElementById(formId);
        if(!form) return;
        
        let input = form.querySelector(`[name="${fieldName}"]`) || form.querySelector(`#${fieldName}`);
        if(input) {
            input.style.borderColor = 'var(--danger-color)';
            let err = input.parentElement.querySelector('.form-error');
            if(!err) {
                err = document.createElement('div');
                err.className = 'form-error text-sm mt-1';
                err.style.color = 'var(--danger-color)';
                input.parentElement.appendChild(err);
            }
            err.textContent = message;
            
            // Clear on typing
            input.addEventListener('input', function onInput() {
                input.style.borderColor = '';
                if(err.parentElement) err.remove();
                input.removeEventListener('input', onInput);
            });
        } else {
            StreamuxToast.error(message);
        }
    }

    // Attach global close handlers
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.close-btn, .btn-outline[onclick^="closeModal"]').forEach(btn => {
            const action = btn.getAttribute('onclick');
            if (action && action.includes('closeModal')) {
                // We'll override the inline onclick with event listeners eventually
                // but for now we leave it for compatibility or handle it via JS
            }
        });
    });

    return {
        open,
        close,
        showError
    };
})();

// Global wrapper for inline onclick compatibility
window.closeModal = StreamuxModal.close;
