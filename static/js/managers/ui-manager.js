// static/js/managers/ui-manager.js

/**
 * UI Manager - Gestiona toda la interfaz de usuario
 * 
 * Responsabilidades:
 * - Sidebar (expandir/colapsar)
 * - Toasts (notificaciones)
 * - Loading overlays
 * - Dropdowns
 * - Modals
 */
class UIManager {
    constructor(eventBus, utils) {
        this.eventBus = eventBus;
        this.utils = utils;
        
        this.state = {
            sidebarExpanded: false,
            mobileMenuOpen: false,
            activeDropdown: null,
            activeModal: null
        };
        
        this.init();
    }
    
    // ===== INITIALIZATION =====
    
    init() {
        this.initSidebar();
        this.initDropdowns();
        this.initKeyboardShortcuts();
        this.initResponsive();
    }
    
    // ===== SIDEBAR =====
    
    initSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        
        // Hover expansion (desktop)
        sidebar.addEventListener('mouseenter', () => {
            if (window.innerWidth >= 1024) {
                this.expandSidebar();
            }
        });
        
        sidebar.addEventListener('mouseleave', () => {
            if (window.innerWidth >= 1024) {
                this.collapseSidebar();
            }
        });
    }
    
    expandSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.add('expanded');
            this.state.sidebarExpanded = true;
            this.eventBus.emit('sidebar:expanded');
        }
    }
    
    collapseSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('expanded');
            this.state.sidebarExpanded = false;
            this.eventBus.emit('sidebar:collapsed');
        }
    }
    
    toggleMobileSidebar() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) return;
        
        this.state.mobileMenuOpen = !this.state.mobileMenuOpen;
        
        if (this.state.mobileMenuOpen) {
            sidebar.classList.add('mobile-open');
            this.eventBus.emit('sidebar:mobile-opened');
        } else {
            sidebar.classList.remove('mobile-open');
            this.eventBus.emit('sidebar:mobile-closed');
        }
    }
    
    // ===== DROPDOWNS =====
    
    initDropdowns() {
        // Click outside to close
        document.addEventListener('click', (event) => {
            if (this.state.activeDropdown && !event.target.closest('[data-component="dropdown"]')) {
                this.closeAllDropdowns();
            }
        });
    }
    
    toggleDropdown(dropdownId) {
        const dropdown = document.getElementById(dropdownId);
        if (!dropdown) return;
        
        const wasOpen = this.state.activeDropdown === dropdownId;
        
        this.closeAllDropdowns();
        
        if (!wasOpen) {
            dropdown.classList.remove('hidden');
            this.state.activeDropdown = dropdownId;
            this.eventBus.emit('dropdown:opened', { id: dropdownId });
        }
    }
    
    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('[id$="-menu"]');
        dropdowns.forEach(dropdown => {
            dropdown.classList.add('hidden');
        });
        this.state.activeDropdown = null;
    }
    
    // ===== TOASTS =====
    
    showToast(message, type = 'info', duration = 5000) {
        let container = document.getElementById('toast-container');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
        
        const toast = this.createToast(message, type);
        container.appendChild(toast);
        
        // Animar entrada
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full');
        });
        
        // Auto-remover
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        }
        
        this.eventBus.emit('toast:shown', { message, type });
        
        return toast;
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} bg-white border border-gray-200 rounded-lg shadow-lg p-4 min-w-80 transform transition-all duration-300 translate-x-full`;
        
        const config = this.getToastConfig(type);
        
        toast.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="flex-shrink-0">
                    ${config.icon}
                </div>
                <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900">${this.utils.escapeHtml(message)}</p>
                </div>
                <button class="toast-close flex-shrink-0 text-gray-400 hover:text-gray-600">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `;
        
        // Close button handler
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => this.removeToast(toast));
        
        return toast;
    }
    
    getToastConfig(type) {
        const configs = {
            success: {
                icon: `<svg class="w-5 h-5 text-success-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>`,
                color: 'success'
            },
            error: {
                icon: `<svg class="w-5 h-5 text-error-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>`,
                color: 'error'
            },
            warning: {
                icon: `<svg class="w-5 h-5 text-warning-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                </svg>`,
                color: 'warning'
            },
            info: {
                icon: `<svg class="w-5 h-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>`,
                color: 'brand'
            }
        };
        
        return configs[type] || configs.info;
    }
    
    removeToast(toast) {
        toast.classList.add('translate-x-full');
        
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 300);
    }
    
    // ===== LOADING =====
    
    showLoading(show = true) {
        let overlay = document.getElementById('loading-overlay');
        
        if (!overlay && show) {
            overlay = this.createLoadingOverlay();
            document.body.appendChild(overlay);
        }
        
        if (overlay) {
            if (show) {
                overlay.classList.remove('hidden');
                this.eventBus.emit('loading:shown');
            } else {
                overlay.classList.add('hidden');
                this.eventBus.emit('loading:hidden');
            }
        }
    }
    
    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 hidden';
        
        overlay.innerHTML = `
            <div class="bg-white rounded-lg p-6 flex flex-col items-center gap-4">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-600"></div>
                <p class="text-gray-600">Loading...</p>
            </div>
        `;
        
        return overlay;
    }
    
    // ===== MODALS =====
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;
        
        modal.classList.remove('hidden');
        this.state.activeModal = modalId;
        
        // Focus trap
        const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
        
        this.eventBus.emit('modal:opened', { id: modalId });
    }
    
    closeModal(modalId) {
        const modal = modalId ? document.getElementById(modalId) : document.getElementById(this.state.activeModal);
        if (!modal) return;
        
        modal.classList.add('hidden');
        this.state.activeModal = null;
        
        this.eventBus.emit('modal:closed', { id: modalId });
    }
    
    closeAllModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.classList.add('hidden');
        });
        this.state.activeModal = null;
    }
    
    // ===== KEYBOARD SHORTCUTS =====
    
    initKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            // Cmd/Ctrl + K for search
            if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
                event.preventDefault();
                this.focusSearch();
            }
            
            // Escape to close modals/dropdowns
            if (event.key === 'Escape') {
                this.closeAllDropdowns();
                this.closeAllModals();
            }
        });
    }
    
    focusSearch() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.focus();
            this.eventBus.emit('search:focused');
        }
    }
    
    // ===== RESPONSIVE =====
    
    initResponsive() {
        const mediaQuery = window.matchMedia('(max-width: 1024px)');
        
        const handleMediaChange = (e) => {
            const toggleButton = document.querySelector('.sidebar-toggle');
            
            if (e.matches) {
                // Mobile
                if (toggleButton) {
                    toggleButton.classList.remove('hidden');
                }
                this.collapseSidebar();
            } else {
                // Desktop
                if (toggleButton) {
                    toggleButton.classList.add('hidden');
                }
                if (this.state.mobileMenuOpen) {
                    this.toggleMobileSidebar();
                }
            }
            
            this.eventBus.emit('responsive:changed', { isMobile: e.matches });
        };
        
        handleMediaChange(mediaQuery);
        
        if (mediaQuery.addEventListener) {
            mediaQuery.addEventListener('change', handleMediaChange);
        } else {
            // Fallback para navegadores antiguos
            mediaQuery.addListener(handleMediaChange);
        }
    }
    
    // ===== UTILITIES =====
    
    getState() {
        return { ...this.state };
    }
    
    destroy() {
        this.closeAllDropdowns();
        this.closeAllModals();
        
        const container = document.getElementById('toast-container');
        if (container) {
            container.remove();
        }
        
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIManager;
} else {
    window.UIManager = UIManager;
}
