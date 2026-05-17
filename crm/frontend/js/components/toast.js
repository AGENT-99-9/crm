/**
 * Streamux CRM — Toast Notification System
 * Handles non-blocking user feedback.
 */
const StreamuxToast = (() => {
    let container = null;

    function init() {
        if (container) return;
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    function show(message, type = 'info', duration = 3000) {
        if (!container) init();

        const toast = document.createElement('div');
        
        let bgColor = 'var(--surface-color)';
        let icon = '<i class="fas fa-info-circle" style="color: var(--primary-color);"></i>';
        let borderLeft = '4px solid var(--primary-color)';

        if (type === 'success') {
            icon = '<i class="fas fa-check-circle" style="color: var(--success-color);"></i>';
            borderLeft = '4px solid var(--success-color)';
        } else if (type === 'error') {
            icon = '<i class="fas fa-exclamation-circle" style="color: var(--danger-color);"></i>';
            borderLeft = '4px solid var(--danger-color)';
        } else if (type === 'warning') {
            icon = '<i class="fas fa-exclamation-triangle" style="color: var(--warning-color);"></i>';
            borderLeft = '4px solid var(--warning-color)';
        }

        toast.style.cssText = `
            background: ${bgColor};
            color: var(--text-primary);
            padding: 1rem 1.5rem;
            border-radius: var(--radius-md);
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            border: 1px solid var(--border-color);
            border-left: ${borderLeft};
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.9rem;
            pointer-events: auto;
            transform: translateX(120%);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        `;

        toast.innerHTML = `
            ${icon}
            <span style="flex:1">${escapeHTML(message)}</span>
            <button style="background:none;border:none;color:var(--text-muted);cursor:pointer;padding:0;">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Close button
        const btn = toast.querySelector('button');
        btn.onclick = () => remove(toast);

        container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0)';
            toast.style.opacity = '1';
        });

        // Auto remove
        if (duration > 0) {
            setTimeout(() => remove(toast), duration);
        }
    }

    function remove(toast) {
        toast.style.transform = 'translateX(120%)';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (toast.parentElement) toast.remove();
        }, 300);
    }

    // Helper to prevent XSS
    function escapeHTML(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    return {
        init,
        success: (msg, d) => show(msg, 'success', d),
        error: (msg, d) => show(msg, 'error', d),
        warning: (msg, d) => show(msg, 'warning', d),
        info: (msg, d) => show(msg, 'info', d)
    };
})();
