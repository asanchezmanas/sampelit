// static/js/init.js

/**
 * Inicialización global de MABApp
 * 
 * Este archivo detecta la configuración de la página
 * e inicializa automáticamente la aplicación.
 */

(function() {
    'use strict';
    
    // Esperar a que el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApp);
    } else {
        initializeApp();
    }
    
    function initializeApp() {
        console.log('[MAB] Initializing...');
        
        // Buscar configuración en el HTML
        const configElement = document.getElementById('page-config');
        const initialDataElement = document.getElementById('initial-data');
        
        if (!configElement) {
            console.warn('[MAB] No configuration found, skipping initialization');
            return;
        }
        
        try {
            // Parse configuration
            const config = JSON.parse(configElement.textContent);
            const initialData = initialDataElement 
                ? JSON.parse(initialDataElement.textContent) 
                : {};
            
            // Crear instancia global de MABApp
            window.MAB = new MABApp({
                // User info
                user: config.user,
                
                // API config
                baseUrl: config.baseUrl || '',
                csrfToken: config.csrfToken || '',
                
                // Page info
                currentPage: config.page || window.location.pathname,
                
                // Initial data
                initialData: initialData,
                
                // Settings
                debug: config.debug || false,
                updateInterval: config.updateInterval || 30000
            });
            
            // Expose para debugging
            if (window.MAB.options.debug) {
                console.log('[MAB] Debug mode enabled');
                console.log('[MAB] Available as window.MAB');
                console.log('[MAB] Configuration:', config);
            }
            
            // Emit ready event
            document.dispatchEvent(new CustomEvent('mab:ready', {
                detail: { app: window.MAB }
            }));
            
            console.log('[MAB] ✅ Initialized successfully');
            
        } catch (error) {
            console.error('[MAB] Initialization failed:', error);
            
            // Mostrar error en UI si es posible
            showInitError(error);
        }
    }
    
    function showInitError(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg z-50 max-w-md';
        errorDiv.innerHTML = `
            <div class="flex items-start gap-3">
                <svg class="w-6 h-6 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                </svg>
                <div>
                    <p class="font-semibold">Initialization Error</p>
                    <p class="text-sm mt-1">${error.message || 'Failed to initialize application'}</p>
                    <button onclick="this.parentElement.parentElement.parentElement.remove()" class="text-sm underline mt-2">Dismiss</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 10000);
    }
    
})();
