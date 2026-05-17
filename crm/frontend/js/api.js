/**
 * Nexus CRM — Centralized API Client
 * Handles all HTTP communication with the backend.
 * Provides consistent error handling, auth redirect, and response parsing.
 */
const NexusAPI = (() => {
    const BASE = '/api';

    async function request(url, options = {}) {
        options.credentials = 'same-origin';
        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            options.headers = { 'Content-Type': 'application/json', ...options.headers };
            options.body = JSON.stringify(options.body);
        }

        try {
            const res = await fetch(BASE + url, options);

            if (res.status === 401) {
                NexusApp.showLoginView();
                throw new Error('Unauthorized');
            }

            const data = await res.json();

            if (!res.ok) {
                const err = new Error(data.error || `Request failed (${res.status})`);
                err.field = data.field || null;
                err.status = res.status;
                throw err;
            }

            return data;
        } catch (err) {
            if (err.message === 'Unauthorized') throw err;
            if (err.status) throw err;   // Re-throw API errors
            console.error(`API Error [${url}]:`, err);
            throw new Error('Network error. Please check your connection.');
        }
    }

    return {
        get: (url) => request(url),
        post: (url, body) => request(url, { method: 'POST', body }),
        put: (url, body) => request(url, { method: 'PUT', body }),
        delete: (url) => request(url, { method: 'DELETE' }),

        // Auth
        login: (username, password) => request('/auth/login', {
            method: 'POST', body: { username, password }
        }),
        register: (username, password) => request('/auth/register', {
            method: 'POST', body: { username, password }
        }),
        logout: () => request('/auth/logout', { method: 'POST' }),
        me: () => request('/auth/me'),

        // Dashboard
        dashboard: () => request('/dashboard/'),

        // Clients
        getClients: () => request('/clients/'),
        getClient: (id) => request(`/clients/${id}`),
        createClient: (data) => request('/clients/', { method: 'POST', body: data }),
        updateClient: (id, data) => request(`/clients/${id}`, { method: 'PUT', body: data }),
        deleteClient: (id) => request(`/clients/${id}`, { method: 'DELETE' }),
        searchClients: (q) => request(`/clients/search?q=${encodeURIComponent(q)}`),

        // Appointments
        getAppointments: () => request('/appointments/'),
        getAppointment: (id) => request(`/appointments/${id}`),
        createAppointment: (data) => request('/appointments/', { method: 'POST', body: data }),
        updateAppointment: (id, data) => request(`/appointments/${id}`, { method: 'PUT', body: data }),
        deleteAppointment: (id) => request(`/appointments/${id}`, { method: 'DELETE' }),

        // Follow-ups
        getFollowups: () => request('/followups/'),
        getFollowup: (id) => request(`/followups/${id}`),
        createFollowup: (data) => request('/followups/', { method: 'POST', body: data }),
        updateFollowup: (id, data) => request(`/followups/${id}`, { method: 'PUT', body: data }),
        deleteFollowup: (id) => request(`/followups/${id}`, { method: 'DELETE' }),

        // Settings
        getSettings: () => request('/settings/'),
        updateSettings: (data) => request('/settings/', { method: 'PUT', body: data }),

        // Reminders
        getReminders: () => request('/reminders/'),
    };
})();
