// static/js/core/state.js

class StateManager {
    constructor(initialData = {}) {
        this.data = { ...initialData };
        this.listeners = new Map();
        this.history = [];
        this.maxHistorySize = 50;
    }
    
    // ===== CORE STATE METHODS =====
    
    get(key) {
        return this.getNestedValue(this.data, key);
    }
    
    set(key, value) {
        const oldValue = this.get(key);
        
        // Save to history
        this.addToHistory(key, oldValue, value);
        
        // Update value
        this.setNestedValue(this.data, key, value);
        
        // Notify listeners
        this.notifyListeners(key, value, oldValue);
        
        return this;
    }
    
    setData(newData) {
        this.data = { ...this.data, ...newData };
        this.notifyListeners('*', this.data);
        return this;
    }
    
    getAll() {
        return { ...this.data };
    }
    
    has(key) {
        return this.getNestedValue(this.data, key) !== undefined;
    }
    
    delete(key) {
        const oldValue = this.get(key);
        this.deleteNestedValue(this.data, key);
        this.notifyListeners(key, undefined, oldValue);
        return this;
    }
    
    clear() {
        const oldData = { ...this.data };
        this.data = {};
        this.notifyListeners('*', {}, oldData);
        return this;
    }
    
    // ===== NESTED OBJECT UTILITIES =====
    
    getNestedValue(obj, path) {
        if (!path) return obj;
        
        const keys = path.split('.');
        let current = obj;
        
        for (const key of keys) {
            if (current === null || current === undefined) {
                return undefined;
            }
            current = current[key];
        }
        
        return current;
    }
    
    setNestedValue(obj, path, value) {
        if (!path) return;
        
        const keys = path.split('.');
        let current = obj;
        
        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            
            if (current[key] === undefined || current[key] === null) {
                current[key] = {};
            }
            
            current = current[key];
        }
        
        current[keys[keys.length - 1]] = value;
    }
    
    deleteNestedValue(obj, path) {
        if (!path) return;
        
        const keys = path.split('.');
        let current = obj;
        
        for (let i = 0; i < keys.length - 1; i++) {
            const key = keys[i];
            
            if (current[key] === undefined || current[key] === null) {
                return;
            }
            
            current = current[key];
        }
        
        delete current[keys[keys.length - 1]];
    }
    
    // ===== LISTENERS & REACTIVITY =====
    
    subscribe(key, callback, options = {}) {
        const { immediate = false } = options;
        
        if (!this.listeners.has(key)) {
            this.listeners.set(key, []);
        }
        
        const listener = {
            callback,
            options,
            id: this.generateListenerId()
        };
        
        this.listeners.get(key).push(listener);
        
        // Call immediately with current value if requested
        if (immediate) {
            const currentValue = this.get(key);
            callback(currentValue, undefined);
        }
        
        // Return unsubscribe function
        return () => this.unsubscribe(key, listener.id);
    }
    
    unsubscribe(key, listenerId) {
        const listeners = this.listeners.get(key);
        if (!listeners) return false;
        
        const index = listeners.findIndex(l => l.id === listenerId);
        if (index !== -1) {
            listeners.splice(index, 1);
            return true;
        }
        
        return false;
    }
    
    notifyListeners(key, newValue, oldValue) {
        // Notify specific key listeners
        const keyListeners = this.listeners.get(key) || [];
        keyListeners.forEach(listener => {
            try {
                listener.callback(newValue, oldValue);
            } catch (error) {
                console.error('State listener error:', error);
            }
        });
        
        // Notify wildcard listeners for any change
        if (key !== '*') {
            const wildcardListeners = this.listeners.get('*') || [];
            wildcardListeners.forEach(listener => {
                try {
                    listener.callback(this.data, { [key]: oldValue });
                } catch (error) {
                    console.error('State wildcard listener error:', error);
                }
            });
        }
    }
    
    generateListenerId() {
        return Math.random().toString(36).substring(2, 9);
    }
    
    // ===== HISTORY MANAGEMENT =====
    
    addToHistory(key, oldValue, newValue) {
        this.history.push({
            timestamp: Date.now(),
            key,
            oldValue: JSON.parse(JSON.stringify(oldValue)),
            newValue: JSON.parse(JSON.stringify(newValue))
        });
        
        // Maintain history size limit
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }
    }
    
    getHistory(limit = 10) {
        return this.history.slice(-limit);
    }
    
    clearHistory() {
        this.history = [];
        return this;
    }
    
    // ===== UTILITY METHODS =====
    
    increment(key, amount = 1) {
        const current = this.get(key) || 0;
        this.set(key, current + amount);
        return this;
    }
    
    decrement(key, amount = 1) {
        const current = this.get(key) || 0;
        this.set(key, current - amount);
        return this;
    }
    
    toggle(key) {
        const current = this.get(key);
        this.set(key, !current);
        return this;
    }
    
    push(key, item) {
        const array = this.get(key) || [];
        if (!Array.isArray(array)) {
            throw new Error(`Value at key "${key}" is not an array`);
        }
        this.set(key, [...array, item]);
        return this;
    }
    
    pop(key) {
        const array = this.get(key) || [];
        if (!Array.isArray(array)) {
            throw new Error(`Value at key "${key}" is not an array`);
        }
        const popped = array[array.length - 1];
        this.set(key, array.slice(0, -1));
        return popped;
    }
    
    merge(key, obj) {
        const current = this.get(key) || {};
        if (typeof current !== 'object' || Array.isArray(current)) {
            throw new Error(`Value at key "${key}" is not an object`);
        }
        this.set(key, { ...current, ...obj });
        return this;
    }
    
    // ===== EXPERIMENT-SPECIFIC METHODS =====
    
    addExperiment(experiment) {
        const experiments = this.get('experiments') || [];
        this.set('experiments', [...experiments, experiment]);
        return this;
    }
    
    updateExperiment(experimentId, updates) {
        const experiments = this.get('experiments') || [];
        const index = experiments.findIndex(exp => exp.id === experimentId);
        
        if (index !== -1) {
            const updatedExperiments = [...experiments];
            updatedExperiments[index] = { ...updatedExperiments[index], ...updates };
            this.set('experiments', updatedExperiments);
        }
        
        return this;
    }
    
    removeExperiment(experimentId) {
        const experiments = this.get('experiments') || [];
        this.set('experiments', experiments.filter(exp => exp.id !== experimentId));
        return this;
    }
    
    getExperiment(experimentId) {
        const experiments = this.get('experiments') || [];
        return experiments.find(exp => exp.id === experimentId);
    }
    
    getActiveExperiments() {
        const experiments = this.get('experiments') || [];
        return experiments.filter(exp => exp.status === 'active');
    }
    
    updateStats(newStats) {
        const currentStats = this.get('stats') || {};
        this.set('stats', { ...currentStats, ...newStats });
        return this;
    }
    
    // ===== PERSISTENCE =====
    
    saveToLocalStorage(key = 'mab_state') {
        try {
            const serialized = JSON.stringify(this.data);
            localStorage.setItem(key, serialized);
            return true;
        } catch (error) {
            console.error('Failed to save state to localStorage:', error);
            return false;
        }
    }
    
    loadFromLocalStorage(key = 'mab_state') {
        try {
            const serialized = localStorage.getItem(key);
            if (serialized) {
                const data = JSON.parse(serialized);
                this.setData(data);
                return true;
            }
        } catch (error) {
            console.error('Failed to load state from localStorage:', error);
        }
        return false;
    }
    
    clearLocalStorage(key = 'mab_state') {
        localStorage.removeItem(key);
        return this;
    }
    
    // ===== COMPUTED VALUES =====
    
    computed(key, computeFn, dependencies = []) {
        // Set initial computed value
        const initialValue = computeFn();
        this.set(key, initialValue);
        
        // Subscribe to dependency changes
        const unsubscribers = dependencies.map(dep => 
            this.subscribe(dep, () => {
                const newValue = computeFn();
                this.set(key, newValue);
            })
        );
        
        // Return function to cleanup subscriptions
        return () => unsubscribers.forEach(unsub => unsub());
    }
    
    // ===== DEBUGGING =====
    
    debug() {
        console.group('State Manager Debug');
        console.log('Current State:', this.data);
        console.log('Active Listeners:', Object.fromEntries(this.listeners));
        console.log('History (last 5):', this.history.slice(-5));
        console.groupEnd();
        return this;
    }
    
    size() {
        return Object.keys(this.data).length;
    }
    
    keys() {
        return Object.keys(this.data);
    }
    
    values() {
        return Object.values(this.data);
    }
    
    entries() {
        return Object.entries(this.data);
    }
}
