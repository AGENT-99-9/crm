/**
 * Streamux CRM — Core Bootstrap & Router
 * Centralizes DOM manipulation and component orchestration.
 * Completely rewritten to prevent XSS and separate concerns.
 */

let currentClientId = null;
let reminderInterval = null;

// --- DOM UTILS (XSS SAFE) ---
function el(tag, attributes = {}, ...children) {
    const element = document.createElement(tag);
    for (const key in attributes) {
        if (key === 'className') element.className = attributes[key];
        else if (key === 'style' && typeof attributes[key] === 'object') {
            Object.assign(element.style, attributes[key]);
        }
        else if (key.startsWith('on') && typeof attributes[key] === 'function') {
            element.addEventListener(key.substring(2).toLowerCase(), attributes[key]);
        }
        else if (key === 'innerHTML') element.innerHTML = attributes[key];
        else element.setAttribute(key, attributes[key]);
    }
    children.forEach(child => {
        if (typeof child === 'string') element.appendChild(document.createTextNode(child));
        else if (child instanceof Node) element.appendChild(child);
    });
    return element;
}

function formatDate(isoString) {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString();
}

function clearDOM(elementId) {
    const el = document.getElementById(elementId);
    if(el) el.innerHTML = '';
    return el;
}

// --- BOOTSTRAP & ROUTING ---
const StreamuxApp = (() => {
    
    async function init() {
        StreamuxToast.init();
        setupNavigation();
        setupGlobalSearch();
        
        try {
            const user = await StreamuxAPI.me();
            handleSuccessfulLogin(user);
        } catch (e) {
            showLoginView();
        }
    }

    function setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                item.classList.add('active');
                
                const targetId = item.getAttribute('data-target');
                document.querySelectorAll('.page-section').forEach(page => {
                    page.style.display = 'none';
                });
                const targetEl = document.getElementById(targetId);
                if(targetEl) targetEl.style.display = 'block';
                
                if(targetId === 'dashboard-page') loadDashboard();
                if(targetId === 'clients-page') loadAllClients();
                if(targetId === 'appointments-page') loadAppointments();
                if(targetId === 'followups-page') loadFollowups();
                if(targetId === 'settings-page') loadSettings();
            });
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', async () => {
            await StreamuxAPI.logout();
            showLoginView();
            StreamuxToast.success("Logged out successfully");
        });

        // Login
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            try {
                const res = await StreamuxAPI.login(u, p);
                handleSuccessfulLogin(res.user);
                StreamuxToast.success("Welcome back!");
            } catch (err) {
                const errorEl = document.getElementById('login-error');
                errorEl.textContent = err.message || "Invalid credentials";
                errorEl.style.display = 'block';
            }
        });

        // Register
        document.getElementById('register-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('reg-username').value;
            const p = document.getElementById('reg-password').value;
            try {
                const res = await StreamuxAPI.register(u, p);
                handleSuccessfulLogin(res.user);
                StreamuxToast.success("Account created successfully!");
            } catch (err) {
                const errorEl = document.getElementById('register-error');
                errorEl.textContent = err.message || "Failed to register";
                errorEl.style.display = 'block';
            }
        });
    }

    function toggleAuth(mode) {
        document.getElementById('login-form').style.display = mode === 'login' ? 'block' : 'none';
        document.getElementById('register-form').style.display = mode === 'register' ? 'block' : 'none';
        document.getElementById('auth-subtitle').textContent = mode === 'login' ? 'Executive Dashboard' : 'Create an Account';
        document.getElementById('login-error').style.display = 'none';
        document.getElementById('register-error').style.display = 'none';
    }

    function handleSuccessfulLogin(user) {
        window.currentUserRole = user.role;
        document.getElementById('user-display-name').textContent = user.display_name || user.username;
        const avatarEl = document.querySelector('.avatar');
        if (avatarEl) avatarEl.textContent = (user.display_name || user.username).charAt(0).toUpperCase();
        
        showMainView();
        loadSettings();
    }

    function showMainView() {
        document.getElementById('login-view').style.display = 'none';
        document.getElementById('main-view').style.display = 'flex';
        loadDashboard();
        startReminders();
    }

    function showLoginView() {
        document.getElementById('main-view').style.display = 'none';
        document.getElementById('login-view').style.display = 'flex';
        if(reminderInterval) clearInterval(reminderInterval);
    }

    return { init, showLoginView, toggleAuth };
})();

window.toggleAuth = StreamuxApp.toggleAuth;

// --- DASHBOARD CONTROLLER ---
async function loadDashboard() {
    try {
        const data = await StreamuxAPI.dashboard();
        
        // Render Stats
        if (data.stats) {
            document.getElementById('stat-total-clients').textContent = data.stats.total_clients || 0;
            document.getElementById('stat-active').textContent = data.stats.active_appointments || 0;
            document.getElementById('stat-pending').textContent = data.stats.pending_followups || 0;
            document.getElementById('stat-completion-rate').textContent = (data.stats.completion_rate || 0) + '%';
        }
        
        // Render simple lists using our XSS safe builder
        renderSimpleList('today-meetings-list', data.today_meetings, 'appointment_datetime');
        renderSimpleList('today-followups-list', data.today_followups, 'followup_date');
        renderSimpleList('overdue-followups-list', data.overdue_followups, 'followup_date', true);
        
        // Recent Clients table
        const tbody = document.querySelector('#recent-clients-table tbody');
        if (tbody) tbody.innerHTML = '';
        
        if (data.recent_clients && tbody) {
            data.recent_clients.forEach(c => {
            const tr = el('tr', { style: { borderBottom: '1px solid var(--border-color)', cursor: 'pointer' }, onClick: () => viewClient(c.id) },
                el('td', { style: { padding: '0.75rem' } }, c.name),
                el('td', { style: { padding: '0.75rem' } }, c.company || '-'),
                el('td', { style: { padding: '0.75rem' } }, el('span', { className: 'badge badge-active' }, c.interested_product || '-')),
                el('td', { style: { padding: '0.75rem' } }, c.status)
            );
            tbody.appendChild(tr);
        });
        }

    } catch (e) {
        StreamuxToast.error("Failed to load dashboard data");
    }
}

function renderSimpleList(containerId, items, dateField, isOverdue = false) {
    const container = clearDOM(containerId);
    if (!items || items.length === 0) {
        container.appendChild(el('p', { className: 'text-secondary text-sm' }, "No items"));
        return;
    }
    
    items.forEach(item => {
        const title = item.name || item.title || item.followup_type;
        const subtitle = item.company || item.client_name || '-';
        
        const row = el('div', { 
            className: 'item-card',
            style: { padding: '1rem', cursor: 'pointer', marginBottom: '0.75rem' },
            onClick: () => viewClient(item.client_id || item.id) // Try to view client context
        },
            el('div', { className: 'd-flex justify-between mb-1' },
                el('span', { className: 'font-bold', style: { color: isOverdue ? 'var(--danger-color)' : 'inherit' } }, title),
                el('span', { className: 'text-sm text-secondary' }, formatDate(item[dateField]))
            ),
            el('div', { className: 'text-sm text-secondary d-flex align-center gap-2' }, 
                el('i', { className: 'fas fa-user-circle', style: { color: 'var(--primary-color)' } }), subtitle
            )
        );
        container.appendChild(row);
    });
}

// --- CLIENT CONTROLLER ---
async function loadAllClients(query = '') {
    try {
        const clients = query.length >= 2 ? await StreamuxAPI.searchClients(query) : await StreamuxAPI.getClients();
        const tbody = document.querySelector('#all-clients-table tbody');
        tbody.innerHTML = '';
        
        clients.forEach(c => {
            const actionsTd = el('td', { style: { padding: '0.75rem' } });
            if (window.currentUserRole === 'admin') {
                actionsTd.appendChild(
                    el('button', { 
                        className: 'btn-outline', 
                        onClick: (e) => { e.stopPropagation(); deleteClient(c.id); } 
                    }, el('i', { className: 'fas fa-trash text-danger' }))
                );
            }

            const tr = el('tr', { style: { borderBottom: '1px solid var(--border-color)', cursor: 'pointer' }, onClick: () => viewClient(c.id) },
                el('td', { style: { padding: '0.75rem' } }, c.name),
                el('td', { style: { padding: '0.75rem' } }, c.phone || '-'),
                el('td', { style: { padding: '0.75rem' } }, c.company || '-'),
                el('td', { style: { padding: '0.75rem' } }, formatDate(c.next_followup)),
                actionsTd
            );
            tbody.appendChild(tr);
        });
    } catch (e) {
        StreamuxToast.error("Failed to load clients");
    }
}

window.openClientModal = function(client = null) {
    StreamuxModal.open('client-modal', (modal) => {
        const form = document.getElementById('client-form');
        form.reset();
        document.getElementById('client-id').value = '';
        document.getElementById('client-modal-title').textContent = client ? 'Edit Client' : 'Add Client';
        
        if(client) {
            document.getElementById('client-id').value = client.id;
            ['name','phone','company','work_type'].forEach(k => {
                const el = document.getElementById('client-' + k.replace('_','-'));
                if(el) el.value = client[k] || '';
            });
            document.getElementById('client-product').value = client.interested_product || '';
            document.getElementById('client-custom-reqs').value = client.custom_requirements || '';
            document.getElementById('client-notes').value = client.notes || '';
        }
    });
}

document.getElementById('client-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    
    const id = document.getElementById('client-id').value;
    const data = {
        name: document.getElementById('client-name').value.trim(),
        phone: document.getElementById('client-phone').value.trim(),
        company: document.getElementById('client-company').value.trim(),
        work_type: document.getElementById('client-work-type').value.trim(),
        interested_product: document.getElementById('client-product').value.trim(),
        custom_requirements: document.getElementById('client-custom-reqs').value.trim(),
        notes: document.getElementById('client-notes').value.trim(),
        status: 'Active'
    };
    
    try {
        if (id) await StreamuxAPI.updateClient(id, data);
        else await StreamuxAPI.createClient(data);
        
        StreamuxModal.close('client-modal');
        StreamuxToast.success("Client saved successfully");
        loadDashboard();
        if(document.getElementById('clients-page').style.display !== 'none') loadAllClients();
    } catch (err) {
        if(err.field) StreamuxModal.showError('client-form', `client-${err.field.replace('_','-')}`, err.message);
        else StreamuxToast.error(err.message);
    } finally {
        btn.disabled = false;
    }
});

async function viewClient(id) {
    try {
        currentClientId = id;
        const client = await StreamuxAPI.getClient(id);
        
        document.getElementById('cv-name').textContent = client.name;
        document.getElementById('cv-phone').textContent = client.phone || '-';
        document.getElementById('cv-company').textContent = client.company || '-';
        document.getElementById('cv-product').textContent = client.interested_product || '-';
        document.getElementById('cv-reqs').textContent = client.custom_requirements || '-';
        document.getElementById('cv-notes').textContent = client.notes || '-';
        
        const fList = clearDOM('cv-followups');
        if (client.followups && client.followups.length > 0) {
            client.followups.forEach(f => {
                fList.appendChild(
                    el('div', { style: { padding: '0.5rem', borderLeft: '2px solid var(--primary-color)', marginBottom: '0.5rem', background: 'var(--bg-color)' } },
                        el('div', { className: 'd-flex justify-between text-sm' },
                            el('strong', {}, f.followup_type || 'Followup'),
                            el('span', {}, formatDate(f.followup_date))
                        ),
                        el('div', { className: 'text-sm' }, f.notes || '')
                    )
                );
            });
        } else {
            fList.appendChild(el('p', { className: 'text-sm text-secondary' }, 'No follow-ups recorded yet.'));
        }
        
        document.getElementById('cv-edit-btn').onclick = () => {
            StreamuxModal.close('client-view-modal');
            openClientModal(client);
        };
        
        StreamuxModal.open('client-view-modal');
    } catch (e) {
        StreamuxToast.error("Failed to load client details");
    }
}

async function deleteClient(id) {
    if(confirm("Are you sure you want to delete this client?")) {
        try {
            await StreamuxAPI.deleteClient(id);
            StreamuxToast.success("Client deleted");
            loadAllClients();
            loadDashboard();
        } catch(e) { StreamuxToast.error(e.message); }
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', StreamuxApp.init);

window.openAppointmentModalFromClient = async function() {
    if(!currentClientId) return;
    await openAppointmentModal();
    document.getElementById('appt-client-id').value = currentClientId;
}

window.openFollowupModalFromClient = async function() {
    if(!currentClientId) return;
    await openFollowupModal();
    document.getElementById('fu-client-id').value = currentClientId;
}

window.exportClientsCSV = async function() {
    try {
        const res = await fetch('/api/clients/export', { credentials: 'same-origin' });
        if(!res.ok) throw new Error("Export failed");
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'clients.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch(e) {
        StreamuxToast.error(e.message);
    }
}

// Export functions for HTML onclicks
window.viewClient = viewClient;
window.deleteClient = deleteClient;

// --- APPOINTMENTS CONTROLLER ---
window.loadAppointments = async function() {
    try {
        const appts = await StreamuxAPI.getAppointments();
        const list = clearDOM('appointments-list');
        if(appts.length === 0) {
            list.appendChild(el('p', { className: 'text-secondary', style: { padding: '1rem' } }, 'No appointments found.'));
            return;
        }
        
        appts.forEach(a => {
            const row = el('div', { className: 'item-card' },
                el('div', { className: 'd-flex justify-between align-center mb-1' },
                    el('h4', { className: 'font-bold' }, a.title),
                    el('span', { className: `badge badge-${a.status.toLowerCase()}` }, a.status)
                ),
                el('div', { className: 'text-sm text-secondary mb-1' },
                    el('i', { className: 'fas fa-user text-info', style: {color: 'var(--primary-color)'} }), ` ${a.client_name || 'General'} | `,
                    el('i', { className: 'fas fa-calendar', style: {color: 'var(--success-color)'} }), ` ${formatDate(a.appointment_datetime)} | `,
                    el('i', { className: 'fas fa-map-marker-alt text-danger' }), ` ${a.location || 'N/A'}`
                ),
                el('p', { className: 'text-sm' }, a.description || ''),
                el('div', { className: 'mt-2 d-flex gap-2' },
                    el('button', { className: 'btn-outline text-sm', onClick: () => editAppointment(a.id) }, el('i', { className: 'fas fa-edit' }), ' Edit'),
                    ...(window.currentUserRole === 'admin' ? [el('button', { className: 'btn-outline text-sm text-danger', style: { marginLeft: '0.5rem' }, onClick: () => deleteAppointment(a.id) }, el('i', { className: 'fas fa-trash' }), ' Delete')] : [])
                )
            );
            list.appendChild(row);
        });
    } catch(e) { StreamuxToast.error("Failed to load appointments"); }
}

window.openAppointmentModal = async function(appt = null) {
    // Preload clients into the select dropdown
    try {
        const clients = await StreamuxAPI.getClients();
        const selectEl = document.getElementById('appt-client-id');
        selectEl.innerHTML = '<option value="">-- General (No Client) --</option>';
        clients.forEach(c => {
            selectEl.appendChild(el('option', { value: c.id }, c.name));
        });
    } catch(e) { console.error("Failed to load clients for modal"); }

    StreamuxModal.open('appointment-modal', (modal) => {
        const form = document.getElementById('appointment-form');
        form.reset();
        document.getElementById('appt-id').value = '';
        document.getElementById('appt-modal-title').textContent = appt ? 'Edit Appointment' : 'Schedule Appointment';
        
        if(appt) {
            document.getElementById('appt-id').value = appt.id;
            document.getElementById('appt-client-id').value = appt.client_id || '';
            document.getElementById('appt-title').value = appt.title || '';
            document.getElementById('appt-datetime').value = appt.appointment_datetime || '';
            document.getElementById('appt-location').value = appt.location || '';
            document.getElementById('appt-description').value = appt.description || '';
            document.getElementById('appt-status').value = appt.status || 'Pending';
        }
    });
}

async function editAppointment(id) {
    try {
        const appt = await StreamuxAPI.getAppointment(id);
        openAppointmentModal(appt);
    } catch(e) { StreamuxToast.error("Could not load appointment"); }
}document.getElementById('appointment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    const id = document.getElementById('appt-id').value;
    const data = {
        client_id: document.getElementById('appt-client-id').value || null,
        title: document.getElementById('appt-title').value.trim(),
        appointment_datetime: document.getElementById('appt-datetime').value,
        location: document.getElementById('appt-location').value.trim(),
        description: document.getElementById('appt-description').value.trim(),
        status: document.getElementById('appt-status').value
    };
    
    try {
        if(id) await StreamuxAPI.updateAppointment(id, data);
        else await StreamuxAPI.createAppointment(data);
        
        StreamuxModal.close('appointment-modal');
        StreamuxToast.success("Appointment saved");
        loadAppointments();
        loadDashboard();
    } catch(err) {
        if(err.field) StreamuxModal.showError('appointment-form', `appt-${err.field.replace('_','-')}`, err.message);
        else StreamuxToast.error(err.message);
    } finally {
        btn.disabled = false;
    }
});

async function deleteAppointment(id) {
    if(confirm("Delete this appointment?")) {
        try {
            await StreamuxAPI.deleteAppointment(id);
            StreamuxToast.success("Appointment deleted");
            loadAppointments();
            loadDashboard();
        } catch(e) { StreamuxToast.error(e.message); }
    }
}

// --- FOLLOWUPS CONTROLLER ---
window.loadFollowups = async function() {
    try {
        const fus = await StreamuxAPI.getFollowups();
        const list = clearDOM('all-followups-list');
        if(fus.length === 0) {
            list.appendChild(el('p', { className: 'text-secondary', style: { padding: '1rem' } }, 'No follow-ups found.'));
            return;
        }
        
        fus.forEach(f => {
            const row = el('div', { className: 'item-card' },
                el('div', { className: 'd-flex justify-between align-center mb-1' },
                    el('h4', { className: 'font-bold' }, `${f.followup_type} - ${f.client_name || 'Client'}`),
                    el('span', { className: `badge badge-${f.status.toLowerCase()}` }, f.status)
                ),
                el('div', { className: 'text-sm text-secondary mb-1' },
                    el('i', { className: 'fas fa-calendar', style: {color: 'var(--success-color)'} }), ` ${formatDate(f.followup_date)}`
                ),
                el('p', { className: 'text-sm' }, f.notes || ''),
                el('div', { className: 'mt-2 d-flex gap-2' },
                    el('button', { className: 'btn-outline text-sm', onClick: () => editFollowup(f.id) }, el('i', { className: 'fas fa-edit' }), ' Edit'),
                    ...(window.currentUserRole === 'admin' ? [el('button', { className: 'btn-outline text-sm text-danger', style: { marginLeft: '0.5rem' }, onClick: () => deleteFollowup(f.id) }, el('i', { className: 'fas fa-trash' }), ' Delete')] : [])
                )
            );
            list.appendChild(row);
        });
    } catch(e) { StreamuxToast.error("Failed to load follow-ups"); }
}

window.openFollowupModal = async function(fu = null) {
    // Preload clients into the select dropdown
    try {
        const clients = await StreamuxAPI.getClients();
        const selectEl = document.getElementById('fu-client-id');
        selectEl.innerHTML = '<option value="">-- General (No Client) --</option>';
        clients.forEach(c => {
            selectEl.appendChild(el('option', { value: c.id }, c.name));
        });
    } catch(e) { console.error("Failed to load clients for modal"); }

    StreamuxModal.open('followup-modal', (modal) => {
        const form = document.getElementById('followup-form');
        form.reset();
        document.getElementById('fu-modal-title').textContent = fu ? 'Edit Follow-Up' : 'Add Follow-Up';
        document.getElementById('fu-id').value = '';
        
        if (fu) {
            document.getElementById('fu-id').value = fu.id;
            document.getElementById('fu-client-id').value = fu.client_id;
            document.getElementById('fu-datetime').value = fu.followup_date || '';
            document.getElementById('fu-type').value = fu.followup_type || 'Call';
            document.getElementById('fu-notes').value = fu.notes || '';
            document.getElementById('fu-status').value = fu.status || 'Pending';
        }
    });
}

async function editFollowup(id) {
    try {
        const fu = await StreamuxAPI.getFollowup(id);
        openFollowupModal(fu);
    } catch(e) { StreamuxToast.error("Could not load follow-up"); }
}

document.getElementById('followup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    const id = document.getElementById('fu-id').value;
    const data = {
        client_id: document.getElementById('fu-client-id').value || null,
        followup_date: document.getElementById('fu-datetime').value,
        followup_type: document.getElementById('fu-type').value,
        notes: document.getElementById('fu-notes').value.trim(),
        status: document.getElementById('fu-status').value
    };
    
    try {
        if(id) await StreamuxAPI.updateFollowup(id, data);
        else await StreamuxAPI.createFollowup(data);
        
        StreamuxModal.close('followup-modal');
        StreamuxToast.success("Follow-up saved");
        loadFollowups();
        loadDashboard();
        if (document.getElementById('client-view-modal').classList.contains('active')) {
            viewClient(currentClientId); 
        }
    } catch(err) {
        if(err.field) StreamuxModal.showError('followup-form', `fu-${err.field.replace('_','-')}`, err.message);
        else StreamuxToast.error(err.message);
    } finally {
        btn.disabled = false;
    }
});

async function deleteFollowup(id) {
    if(confirm("Delete this follow-up?")) {
        try {
            await StreamuxAPI.deleteFollowup(id);
            StreamuxToast.success("Follow-up deleted");
            loadFollowups();
            loadDashboard();
        } catch(e) { StreamuxToast.error(e.message); }
    }
}

// --- SEARCH ---
let searchTimeout;
function setupGlobalSearch() {
    const searchInput = document.getElementById('global-search');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const q = e.target.value.trim();
        
        searchTimeout = setTimeout(() => {
            // Navigate to Clients page to show the filtered list
            if (document.getElementById('clients-page').style.display === 'none') {
                document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
                document.querySelector('.nav-item[data-target="clients-page"]').classList.add('active');
                
                document.querySelectorAll('.page-view').forEach(p => p.style.display = 'none');
                document.getElementById('clients-page').style.display = 'block';
            }
            
            // Filter the client list
            loadAllClients(q);
        }, 300); // Debounce
    });

    document.addEventListener('click', (e) => {
        if(!e.target.closest('.search-bar') && !e.target.closest('#search-results')) {
            searchResults.style.display = 'none';
        }
    });

    // Add Ctrl+K shortcut
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
    });
}

// --- SETTINGS & REMINDERS ---
window.loadSettings = async function() {
    try {
        const settings = await StreamuxAPI.getSettings();
        if(settings) {
            document.getElementById('setting-reminder-mins').value = settings.reminder_before_minutes || 15;
            document.getElementById('setting-dark-mode').value = settings.dark_mode === undefined ? 1 : settings.dark_mode;
            applyTheme(settings.dark_mode);
        }
    } catch(e) {}
}

document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const mins = document.getElementById('setting-reminder-mins').value;
    const dark = document.getElementById('setting-dark-mode').value;
    
    try {
        await StreamuxAPI.updateSettings({
            reminder_before_minutes: parseInt(mins), 
            dark_mode: parseInt(dark)
        });
        applyTheme(parseInt(dark));
        StreamuxToast.success("Settings saved!");
    } catch(err) {
        StreamuxToast.error("Failed to save settings");
    }
});

function applyTheme(isDark) {
    if(isDark == 1) document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
}

async function startReminders() {
    if(reminderInterval) clearInterval(reminderInterval);
    
    // Toggle dropdown
    const bellIcon = document.getElementById('bell-icon');
    const notifDropdown = document.getElementById('notif-dropdown');
    
    bellIcon.addEventListener('click', (e) => {
        // Prevent closing if clicking inside the dropdown
        if (e.target.closest('#notif-dropdown')) return;
        notifDropdown.style.display = notifDropdown.style.display === 'none' ? 'block' : 'none';
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('#bell-icon')) {
            notifDropdown.style.display = 'none';
        }
    });

    const check = async () => {
        try {
            const data = await StreamuxAPI.getReminders();
            let count = data.appointments.length + data.followups.length;
            const badge = document.getElementById('notif-count');
            const list = document.getElementById('notif-list');
            
            list.innerHTML = '';
            
            if(count > 0) {
                badge.textContent = count;
                badge.style.display = 'flex';
                
                // Native notification
                if ("Notification" in window && Notification.permission === "granted" && (!notifDropdown.dataset.lastNotified || notifDropdown.dataset.lastNotified !== data.appointments.length.toString())) {
                    new Notification("Upcoming CRM Events", { body: `You have ${count} upcoming events.`, icon: '/favicon.ico' });
                    notifDropdown.dataset.lastNotified = count.toString();
                }

                // Render lists in dropdown
                const allEvents = [...data.appointments, ...data.followups].sort((a,b) => new Date(a.appointment_datetime || a.followup_date) - new Date(b.appointment_datetime || b.followup_date));
                allEvents.forEach((r) => {
                    const isAppt = !!r.appointment_datetime;
                    list.appendChild(
                        el('div', { style: { padding: '0.75rem 0', borderBottom: '1px solid var(--border-color)' } },
                            el('div', { className: 'd-flex justify-between' },
                                el('strong', { style: { color: isAppt ? 'var(--primary-color)' : 'var(--success-color)' } }, isAppt ? r.title : `Follow-up: ${r.followup_type}`),
                                el('span', { className: 'text-sm text-secondary' }, formatDate(isAppt ? r.appointment_datetime : r.followup_date))
                            ),
                            el('div', { className: 'text-sm mt-1 text-secondary' }, r.client_name ? `Client: ${r.client_name}` : 'General')
                        )
                    );
                });
            } else {
                badge.style.display = 'none';
                list.innerHTML = '<p class="text-sm text-secondary">No upcoming reminders.</p>';
            }
        } catch(e) {}
    };
    
    check();
    reminderInterval = setInterval(check, 60000);
}

if ("Notification" in window && Notification.permission !== "granted" && Notification.permission !== "denied") {
    Notification.requestPermission();
}
