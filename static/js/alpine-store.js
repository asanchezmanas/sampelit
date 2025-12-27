/**
 * Alpine Data Store Initialization
 * 
 * Este archivo reemplaza a `MABApp` y `init.js` en la arquitectura V2.
 * Inicializa:
 * 1. API Client Global
 * 2. Servicios de Datos
 * 3. Alpine Stores (Estado Global)
 */

document.addEventListener('alpine:init', () => {
    console.log('[Alpine] Initializing Stores & Services...');

    // 1. Inicializar Core API
    const apiClient = new APIClient({
        baseUrl: '/api/v1',
        onError: (error) => {
            console.error('API Error:', error);
            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: error.message || 'Server Error', type: 'error' }
            }));
        }
    });

    // 2. Inicializar Servicios
    // Si la clase no existe (lazy load incompleto), evitamos error fatal con try/catch o condicional, 
    // pero idealmente asumimos scripts cargados.
    const experimentService = window.ExperimentService ? new ExperimentService(apiClient) : null;
    const metricsService = window.MetricsService ? new MetricsService(apiClient) : null;
    const teamService = window.TeamService ? new TeamService(apiClient) : null;
    const authService = window.AuthService ? new AuthService(apiClient) : null;

    // 3. Definir Stores 

    // --- EXPERIMENTS STORE ---
    Alpine.store('experiments', {
        list: [],
        active: [],
        current: null,
        loading: false,

        async fetchAll(filters = {}) {
            if (!experimentService) return;
            this.loading = true;
            try {
                this.list = await experimentService.list(filters);
                this.active = this.list.filter(e => e.status === 'active');
            } catch (err) { console.error(err); }
            finally { this.loading = false; }
        },

        async fetchOne(id) {
            if (!experimentService) return;
            this.loading = true;
            try {
                this.current = await experimentService.get(id);
                return this.current;
            } catch (err) { console.error(err); }
            finally { this.loading = false; }
        },

        async create(data) {
            if (!experimentService) return;
            this.loading = true;
            try {
                const newExp = await experimentService.create(data);
                this.list.push(newExp);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Experiment created', type: 'success' } }));
                return newExp;
            } catch (err) { throw err; }
            finally { this.loading = false; }
        },

        async delete(id) {
            if (!experimentService) return;
            if (!confirm('Are you sure?')) return;

            // SOTA: Optimistic Update
            // 1. Snapshot state
            const previousList = [...this.list];

            // 2. Update UI immediately
            this.list = this.list.filter(e => e.id !== id);

            // 3. Perform Async Operation
            try {
                await experimentService.delete(id);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Experiment deleted', type: 'success' } }));
            } catch (e) {
                // 4. Revert on failure
                console.error(e);
                this.list = previousList;
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Failed to delete experiment', type: 'error' } }));
            }
        },

        async start(id) {
            if (!experimentService) return;
            this.loading = true;
            try {
                const updated = await experimentService.start(id);
                this.updateLocal(id, updated);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Experiment started 🚀', type: 'success' } }));
            } finally { this.loading = false; }
        },

        async pause(id) {
            if (!experimentService) return;
            this.loading = true;
            try {
                const updated = await experimentService.pause(id);
                this.updateLocal(id, updated);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Experiment paused', type: 'warning' } }));
            } finally { this.loading = false; }
        },

        async stop(id) {
            if (!experimentService) return;
            if (!confirm('Stop test?')) return;
            this.loading = true;
            try {
                const updated = await experimentService.stop(id);
                this.updateLocal(id, updated);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Experiment stopped', type: 'info' } }));
            } finally { this.loading = false; }
        },

        updateLocal(id, data) {
            const index = this.list.findIndex(e => e.id === id);
            if (index !== -1) this.list[index] = { ...this.list[index], ...data };
            if (this.current && this.current.id === id) this.current = { ...this.current, ...data };
        }
    });

    // --- ANALYTICS STORE ---
    Alpine.store('analytics', {
        global: { total_visitors: 0, trend: 0 },
        traffic: [],
        devices: { desktop: 0, mobile: 0, tablet: 0 },
        pages: [],
        loading: false,

        async fetchOverview(period = '30d') {
            if (!metricsService) return;
            this.loading = true;
            try {
                const [global, traffic, devices, pages] = await Promise.all([
                    metricsService.getGlobalMetrics(period),
                    metricsService.getTrafficSources(period),
                    metricsService.getDeviceStats(period),
                    metricsService.getPagePerformance(period)
                ]);
                this.global = global;
                this.traffic = Array.isArray(traffic) ? traffic : [];
                this.devices = devices || { desktop: 0, mobile: 0, tablet: 0 };
                this.pages = Array.isArray(pages) ? pages : [];
            } catch (err) {
                console.error(err);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Failed to load analytics', type: 'error' } }));
            } finally { this.loading = false; }
        }
    });

    // --- TEAM STORE ---
    Alpine.store('team', {
        members: [],
        organization: null,
        loading: false,

        async fetchAll() {
            if (!teamService) return;
            this.loading = true;
            try {
                const [members, org] = await Promise.all([
                    teamService.listMembers(),
                    teamService.getOrganization()
                ]);
                this.members = members || [];
                this.organization = org;
            } catch (err) { console.error(err); }
            finally { this.loading = false; }
        },

        async invite(email, role) {
            if (!teamService) return;
            this.loading = true;
            try {
                await teamService.inviteMember(email, role);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: `Invite sent to ${email}`, type: 'success' } }));
                await this.fetchAll();
            } finally { this.loading = false; }
        },

        async updateRole(id, role) {
            if (!teamService) return;
            try {
                await teamService.updateRole(id, role);
                const member = this.members.find(m => m.id === id);
                if (member) member.role = role;
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Role updated', type: 'success' } }));
            } catch (err) {
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Failed update', type: 'error' } }));
            }
        },

        async removeMember(id) {
            if (!teamService) return;
            if (!confirm('Remove member?')) return;
            try {
                await teamService.removeMember(id);
                this.members = this.members.filter(m => m.id !== id);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Member removed', type: 'info' } }));
            } catch (err) { console.error(err); }
        }
    });

    // --- AUTH STORE ---
    Alpine.store('auth', {
        user: null, // { first_name, last_name, email, company, plan, ... }
        loading: false,

        async init() {
            if (authService) await this.fetchUser();
        },

        async fetchUser() {
            if (!authService) return;
            this.loading = true;
            try {
                this.user = await authService.getProfile();
            } catch (err) { console.error(err); }
            finally { this.loading = false; }
        },

        async updateProfile(data) {
            if (!authService) return;
            this.loading = true;
            try {
                const updated = await authService.updateProfile(data);
                this.user = { ...this.user, ...updated };
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Profile updated', type: 'success' } }));
            } catch (err) {
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Profile update failed', type: 'error' } }));
            } finally { this.loading = false; }
        },

        async updatePassword(current, newPass) {
            if (!authService) return;
            this.loading = true;
            try {
                await authService.updatePassword(current, newPass);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Password changed', type: 'success' } }));
            } catch (err) {
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Password update failed', type: 'error' } }));
            } finally { this.loading = false; }
        },

        get fullName() {
            return this.user ? `${this.user.first_name} ${this.user.last_name}`.trim() : 'Guest';
        },

        get initials() {
            if (!this.user) return '??';
            return ((this.user.first_name?.[0] || '') + (this.user.last_name?.[0] || '')).toUpperCase();
        }
    });

    // --- UI STORE ---
    Alpine.store('ui', {
        sidebarOpen: false,
        darkMode: localStorage.getItem('darkMode') === 'true',

        toggleSidebar() {
            this.sidebarOpen = !this.sidebarOpen;
        },

        toggleTheme() {
            this.darkMode = !this.darkMode;
            localStorage.setItem('darkMode', this.darkMode);
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        }
    });

    console.log('[Alpine] Stores Initialized ✅');
});
