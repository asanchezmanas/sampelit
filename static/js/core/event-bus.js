// static/js/core/event-bus.js

/**
 * Event Bus - Sistema centralizado de eventos
 * 
 * Permite comunicación desacoplada entre módulos
 */
class EventBus {
    constructor() {
        this.events = new Map();
        this.wildcardListeners = [];
        this.debug = false;
    }
    
    /**
     * Suscribirse a un evento
     * @param {string} event - Nombre del evento
     * @param {Function} callback - Función a ejecutar
     * @param {Object} options - Opciones (once, priority)
     * @returns {Function} Función para desuscribirse
     */
    on(event, callback, options = {}) {
        if (!this.events.has(event)) {
            this.events.set(event, []);
        }
        
        const listener = { 
            callback,
            id: this.generateId(),
            once: options.once || false,
            priority: options.priority || 0
        };
        
        const listeners = this.events.get(event);
        listeners.push(listener);
        
        // Ordenar por prioridad (mayor primero)
        listeners.sort((a, b) => b.priority - a.priority);
        
        if (this.debug) {
            console.log(`[EventBus] Listener registered: ${event}`, listener.id);
        }
        
        // Retornar función para desuscribirse
        return () => this.off(event, listener.id);
    }
    
    /**
     * Suscribirse una sola vez
     */
    once(event, callback) {
        return this.on(event, callback, { once: true });
    }
    
    /**
     * Desuscribirse de un evento
     */
    off(event, listenerId) {
        const listeners = this.events.get(event);
        if (!listeners) return false;
        
        const index = listeners.findIndex(l => l.id === listenerId);
        if (index !== -1) {
            listeners.splice(index, 1);
            
            if (this.debug) {
                console.log(`[EventBus] Listener removed: ${event}`, listenerId);
            }
            
            return true;
        }
        return false;
    }
    
    /**
     * Emitir un evento
     */
    emit(event, data) {
        const listeners = this.events.get(event) || [];
        const toRemove = [];
        
        if (this.debug) {
            console.log(`[EventBus] Emitting: ${event}`, data);
        }
        
        // Ejecutar listeners específicos
        listeners.forEach((listener) => {
            try {
                listener.callback(data);
                
                if (listener.once) {
                    toRemove.push(listener.id);
                }
            } catch (error) {
                console.error(`[EventBus] Error in listener for ${event}:`, error);
            }
        });
        
        // Ejecutar wildcard listeners
        this.wildcardListeners.forEach((listener) => {
            try {
                listener.callback(event, data);
            } catch (error) {
                console.error(`[EventBus] Error in wildcard listener:`, error);
            }
        });
        
        // Remover listeners "once"
        toRemove.forEach(id => this.off(event, id));
    }
    
    /**
     * Suscribirse a todos los eventos (wildcard)
     */
    onAny(callback) {
        const listener = {
            callback,
            id: this.generateId()
        };
        
        this.wildcardListeners.push(listener);
        
        return () => {
            const index = this.wildcardListeners.findIndex(l => l.id === listener.id);
            if (index !== -1) {
                this.wildcardListeners.splice(index, 1);
            }
        };
    }
    
    /**
     * Remover todos los listeners de un evento
     */
    removeAllListeners(event) {
        if (event) {
            this.events.delete(event);
        } else {
            this.events.clear();
            this.wildcardListeners = [];
        }
    }
    
    /**
     * Obtener lista de eventos registrados
     */
    getEventNames() {
        return Array.from(this.events.keys());
    }
    
    /**
     * Obtener número de listeners para un evento
     */
    listenerCount(event) {
        const listeners = this.events.get(event);
        return listeners ? listeners.length : 0;
    }
    
    /**
     * Generar ID único
     */
    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Habilitar modo debug
     */
    enableDebug() {
        this.debug = true;
    }
    
    /**
     * Deshabilitar modo debug
     */
    disableDebug() {
        this.debug = false;
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EventBus;
} else {
    window.EventBus = EventBus;
}
