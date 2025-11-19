// static/js/core/app.js
// Versión simplificada - Orquestador principal

/**
 * MABApp - Aplicación principal
 * 
 * Este es el orquestador que coordina todos los managers.
 * Ya no tiene lógica de negocio, solo inicialización y coordinación.
 */
class MABApp {
    constructor(options = {}) {
        this.options = {
            baseUrl: '',
            debug: false,
            autoOptimize: true,
            ...options
        };
        
        // Core systems (ya existen como archivos separados)
        this.utils = new Utils();
        this.state = new StateManager(this.options.initialData || {});
        this.eventBus = new EventBus();
        
        this.api = new APIClient({
            baseUrl: this.options.baseUrl,
            csrfToken: this.options.csrfToken
        });
        
        // Managers (nueva arquitectura modular)
        this.managers = {};
        
        this.initializeManagers();
        this.setupGlobalHandlers();
        this.log('MABApp initialized');
    }
    
    // ===== INITIALIZATION =====
    
    initializeManagers() {
        // UI Manager
        this.managers.ui = new UIManager(this.eventBus, this.utils);
        
        // Experiment Manager
        this.managers.experiments = new ExperimentManager(
            this.api,
            this.state,
            this.eventBus,
            this.managers.ui
        );
        
        // Metrics Manager (solo si hay usuario autenticado)
        if (this.options.user) {
            this.managers.metrics = new MetricsManager(this.api, this.eventBus, {
                interval: this.options.updateInterval || 30000
            });
            
            // Auto-start metrics
            this.managers.metrics.start();
        }
        
        this.log('All managers initialized');
    }
    
    // ===== GLOBAL HANDLERS =====
    
    setupGlobalHandlers() {
        // Global click handler para data-action
        document.addEventListener('click', (event) => {
            const button = event.target.closest('[data-action]');
            if (button) {
                event.preventDefault();
                this.handleAction(button);
            }
        });
        
        // Global form handler
        document.addEventListener('submit', (event) => {
            const form = event.target;
            const action = form.dataset.action;
            
            if (action) {
                event.preventDefault();
                this.handleFormSubmit(form, action);
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            this.handleKeyboardShortcut(event);
        });
    }
    
    handleAction(button) {
        const action = button.dataset.action;
        const target = button.dataset.target;
        
        this.log(`Action: ${action}`, { target });
        
        // Routing de acciones
        switch (action) {
            // Sidebar
            case 'toggle-mobile-sidebar':
                this.managers.ui.toggleMobileSidebar();
                break;
            
            // User menu
            case 'toggle-user-menu':
                this.managers.ui.toggleDropdown('user-menu');
                break;
            
            // Experiments
            case 'create-experiment':
                this.managers.experiments.navigateToCreate();
                break;
                
            case 'start-experiment':
                this.managers.experiments.startExperiment(target);
                break;
                
            case 'pause-experiment':
                this.managers.experiments.pauseExperiment(target);
                break;
                
            case 'stop-experiment':
                this.managers.experiments.stopExperiment(target);
                break;
                
            case 'view-experiment':
                this.managers.experiments.viewExperiment(target);
                break;
                
            case 'edit-experiment':
                this.managers.experiments.editExperiment(target);
                break;
                
            case 'delete-experiment':
                this.managers.experiments.deleteExperiment(target);
                break;
            
            // Auth
            case 'logout':
                this.logout();
                break;
            
            default:
                this.log(`Unknown action: ${action}`);
                this.eventBus.emit('action:unknown', { action, target });
        }
    }
    
    async handleFormSubmit(form, action) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        this.log(`Form submit: ${action}`, data);
        
        this.managers.ui.showLoading(true);
        
        try {
            let response;
            
            switch (action) {
                case 'login':
                    response = await this.api.post('/api/auth/login', data);
                    if (response.success) {
                        this.handleLoginSuccess(response.data);
                    }
                    break;
                    
                case 'register':
                    response = await this.api.post('/api/auth/register', data);
                    if (response.success) {
                        this.handleLoginSuccess(response.data);
                    }
                    break;
                    
                case 'create-experiment':
                    response = await this.managers.experiments.createExperiment(data);
                    if (response) {
                        // Redirect or stay
                        window.location.href = `/experiment/${response.id}`;
                    }
                    break;
                    
                default:
                    this.log(`Unknown form action: ${action}`);
                    this.eventBus.emit('form:unknown', { action, data });
            }
            
        } catch (error) {
            this.handleError(error);
        } finally {
            this.managers.ui.showLoading(false);
        }
    }
    
    handleKeyboardShortcut(event) {
        // Cmd/Ctrl + K for search
        if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
            event.preventDefault();
            this.managers.ui.focusSearch();
        }
        
        // Escape to close overlays
        if (event.key === 'Escape') {
            this.managers.ui.closeAllDropdowns();
            this.managers.ui.closeAllModals();
        }
    }
    
    // ===== AUTH =====
    
    handleLoginSuccess(data) {
        if (data.token) {
            localStorage.setItem('mab_token', data.token);
        }
        
        this.managers.ui.showToast('Welcome back!', 'success');
        
        setTimeout(() => {
            window.location.href = '/';
        }, 1000);
    }
    
    async logout() {
        if (!confirm('Are you sure you want to sign out?')) {
            return;
        }
        
        localStorage.removeItem('mab_token');
        this.managers.ui.showToast('Signed out successfully', 'success');
        
        setTimeout(() => {
            window.location.href = '/login';
        }, 1000);
    }
    
    // ===== ERROR HANDLING =====
    
    handleError(error) {
        this.error('Error:', error);
        
        let message = 'An error occurred. Please try again.';
        
        if (error.response) {
            if (error.response.status === 401) {
                message = 'Please sign in to continue.';
                setTimeout(() => {
                    window.location.href = '/login';
                }, 2000);
            } else if (error.response.data?.detail) {
                message = error.response.data.detail;
            }
        } else if (error.message) {
            message = error.message;
        }
        
        this.managers.ui.showToast(message, 'error');
    }
    
    // ===== PUBLIC API =====
    
    // Acceso directo a managers (convenience)
    get ui() {
        return this.managers.ui;
    }
    
    get experiments() {
        return this.managers.experiments;
    }
    
    get metrics() {
        return this.managers.metrics;
    }
    
    // State shortcuts
    getState(key) {
        return this.state.get(key);
    }
    
    setState(key, value) {
        return this.state.set(key, value);
    }
    
    // Refresh data
    async refresh() {
        const currentPage = this.options.currentPage || window.location.pathname;
        
        this.log(`Refreshing page: ${currentPage}`);
        
        if (currentPage === '/' || currentPage === '/dashboard') {
            await this.refreshDashboard();
        } else if (currentPage.startsWith('/experiment/')) {
            const experimentId = currentPage.split('/')[2];
            await this.managers.experiments.refreshExperiment(experimentId);
        }
        
        // Always refresh metrics
        if (this.managers.metrics) {
            await this.managers.metrics.forceUpdate();
        }
    }
    
    async refreshDashboard() {
        try {
            this.managers.ui.showLoading(true);
            
            const response = await this.api.get('/api/dashboard');
            
            if (response.success) {
                this.state.setData(response.data);
                this.eventBus.emit('dashboard:refreshed', response.data);
            }
            
        } catch (error) {
            this.handleError(error);
        } finally {
            this.managers.ui.showLoading(false);
        }
    }
    
    // ===== UTILITIES =====
    
    log(...args) {
        if (this.options.debug || window.location.hostname === 'localhost') {
            console.log('[MAB]', ...args);
        }
    }
    
    error(...args) {
        console.error('[MAB]', ...args);
    }
    
    // ===== CLEANUP =====
    
    destroy() {
        // Destroy all managers
        Object.values(this.managers).forEach(manager => {
            if (manager.destroy) {
                manager.destroy();
            }
        });
        
        // Clear state
        this.state.clear();
        
        // Remove all event listeners
        this.eventBus.removeAllListeners();
        
        this.log('MABApp destroyed');
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MABApp;
} else {
    window.MABApp = MABApp;
}
