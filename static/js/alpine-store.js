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
        baseUrl: '/api/v1', // Ajustar según config real si es necesario
        onError: (error) => {
            console.error('API Error:', error);
            // Dispatch evento global para que el Toast lo capture
            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: error.message || 'Server Error', type: 'error' }
            }));
        }
    });

    // 2. Inicializar Servicios
    const experimentService = new ExperimentService(apiClient);
    // const authService = new AuthService(apiClient); // Future TODO

    // 3. Definir Stores 

    // --- EXPERIMENTS STORE ---
    Alpine.store('experiments', {
        list: [],
        active: [],
        current: null,
        loading: false,
        lastUpdated: null,

        // Inicialización
        init() {
            // Cargar caché si existe (opcional)
        },

        // Acciones CRUD
        async fetchAll(filters = {}) {
            this.loading = true;
            try {
                this.list = await experimentService.list(filters);
                this.active = this.list.filter(e => e.status === 'active');
                this.lastUpdated = new Date();
            } catch (err) {
                console.error('Failed to fetch experiments', err);
            } finally {
                this.loading = false;
            }
        },

        async fetchOne(id) {
            this.loading = true;
            try {
                this.current = await experimentService.get(id);
                return this.current;
            } catch (err) {
                console.error('Failed to get experiment', err);
            } finally {
                this.loading = false;
            }
        },

        async create(data) {
            this.loading = true;
            try {
                const newExp = await experimentService.create(data);
                this.list.push(newExp); // Optimistic UI or wait for fetch

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Experiment created successfully', type: 'success' }
                }));

                return newExp;
            } catch (err) {
                throw err; // Relanzar para que el componente maneje errores específicos si quiere
            } finally {
                this.loading = false;
            }
        },

        async delete(id) {
            if (!confirm('Are you sure?')) return;

            this.loading = true;
            try {
                await experimentService.delete(id);
                this.list = this.list.filter(e => e.id !== id);

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Experiment deleted', type: 'success' }
                }));
            } catch (err) {
                throw err;
            } finally {
                this.loading = false;
            }
        },

        // Acciones de Estado
        async start(id) {
            this.loading = true;
            try {
                const updated = await experimentService.start(id);
                this.updateLocal(id, updated);
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Experiment started 🚀', type: 'success' }
                }));
            } finally { this.loading = false; }
        },

        async pause(id) {
            this.loading = true;
            try {
                const updated = await experimentService.pause(id);
                this.updateLocal(id, updated);
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Experiment paused ⏸️', type: 'warning' }
                }));
            } finally { this.loading = false; }
        },

        async stop(id) {
            if (!confirm('Stop this test? This cannot be undone.')) return;

            this.loading = true;
            try {
                const updated = await experimentService.stop(id);
                this.updateLocal(id, updated);
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Experiment stopped 🛑', type: 'info' }
                }));
            } finally { this.loading = false; }
        },

        // Helpers
        updateLocal(id, data) {
            // Actualizar en la lista general
            const index = this.list.findIndex(e => e.id === id);
            if (index !== -1) {
                this.list[index] = { ...this.list[index], ...data };
            }
            // Actualizar current si es el mismo
            if (this.current && this.current.id === id) {
                this.current = { ...this.current, ...data };
            }
        }
    });

    // --- UI STORE (Global Helpers) ---
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
