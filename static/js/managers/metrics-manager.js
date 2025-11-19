// static/js/managers/metrics-manager.js

/**
 * Metrics Manager - Gestiona métricas en tiempo real
 * 
 * Responsabilidades:
 * - Polling de métricas desde el backend
 * - Actualización de elementos con data-live-metric
 * - Retry logic con backoff exponencial
 * - Animaciones de cambios de valores
 */
class MetricsManager {
    constructor(api, eventBus, options = {}) {
        this.api = api;
        this.eventBus = eventBus;
        
        this.options = {
            interval: 30000,           // 30 segundos
            retryAttempts: 3,
            backoffMultiplier: 2,
            maxBackoff: 300000,        // 5 minutos max
            batchUpdates: true,
            ...options
        };
        
        this.isRunning = false;
        this.retryCount = 0;
        this.currentInterval = this.options.interval;
        this.timeoutId = null;
        
        // Registry de métricas
        this.metrics = new Map();
        this.pendingUpdates = new Map();
        this.updateScheduled = false;
        
        this.init();
    }
    
    // ===== INITIALIZATION =====
    
    init() {
        this.discoverMetrics();
        
        // Suscribirse a eventos
        this.eventBus.on('metrics:refresh-requested', () => {
            this.updateMetrics(true);
        });
        
        this.eventBus.on('experiment:updated', () => {
            this.updateMetrics(true);
        });
    }
    
    discoverMetrics() {
        const elements = document.querySelectorAll('[data-live-metric]');
        
        elements.forEach(element => {
            const metricName = element.dataset.liveMetric;
            this.registerMetric(metricName, element);
        });
        
        console.log(`[MetricsManager] Discovered ${this.metrics.size} unique metrics`);
    }
    
    registerMetric(metricName, element) {
        if (!this.metrics.has(metricName)) {
            this.metrics.set(metricName, []);
        }
        
        const elements = this.metrics.get(metricName);
        if (!elements.includes(element)) {
            elements.push(element);
        }
    }
    
    // ===== START/STOP =====
    
    start() {
        if (this.isRunning) {
            console.warn('[MetricsManager] Already running');
            return;
        }
        
        if (this.metrics.size === 0) {
            console.warn('[MetricsManager] No metrics to track');
            return;
        }
        
        this.isRunning = true;
        console.log('[MetricsManager] Started');
        
        // Primera actualización inmediata
        this.scheduleNext(1000);
        
        this.eventBus.emit('metrics:started');
    }
    
    stop() {
        if (!this.isRunning) return;
        
        this.isRunning = false;
        
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
        
        console.log('[MetricsManager] Stopped');
        this.eventBus.emit('metrics:stopped');
    }
    
    // ===== UPDATE LOGIC =====
    
    async updateMetrics(force = false) {
        if (!this.isRunning && !force) return;
        
        const metricNames = Array.from(this.metrics.keys());
        
        if (metricNames.length === 0) {
            return;
        }
        
        try {
            const response = await this.api.get('/api/metrics/live', {
                metrics: metricNames.join(',')
            });
            
            if (response.success) {
                this.processMetricsUpdate(response.data);
                
                // Reset retry logic on success
                this.retryCount = 0;
                this.currentInterval = this.options.interval;
                
                this.eventBus.emit('metrics:updated', response.data);
            }
            
        } catch (error) {
            this.handleError(error);
        }
        
        // Schedule next update
        if (this.isRunning) {
            this.scheduleNext(this.currentInterval);
        }
    }
    
    processMetricsUpdate(metricsData) {
        if (this.options.batchUpdates) {
            // Batch updates para mejor performance
            Object.entries(metricsData).forEach(([key, value]) => {
                this.pendingUpdates.set(key, value);
            });
            
            this.scheduleUpdateFlush();
        } else {
            // Update inmediato
            Object.entries(metricsData).forEach(([key, value]) => {
                this.updateMetricElements(key, value);
            });
        }
    }
    
    scheduleUpdateFlush() {
        if (this.updateScheduled) return;
        
        this.updateScheduled = true;
        
        requestAnimationFrame(() => {
            this.flushPendingUpdates();
            this.updateScheduled = false;
        });
    }
    
    flushPendingUpdates() {
        const updates = Array.from(this.pendingUpdates.entries());
        this.pendingUpdates.clear();
        
        updates.forEach(([metricName, value]) => {
            this.updateMetricElements(metricName, value);
        });
    }
    
    updateMetricElements(metricName, value) {
        const elements = this.metrics.get(metricName) || [];
        
        elements.forEach(element => {
            // Verificar si el elemento aún está en el DOM
            if (!document.contains(element)) {
                return;
            }
            
            this.animateValueChange(element, value);
        });
    }
    
    animateValueChange(element, newValue) {
        const currentValue = element.textContent.trim();
        const formattedValue = this.formatValue(element, newValue);
        
        if (currentValue !== formattedValue) {
            // Animación con Web Animations API si está disponible
            if (element.animate) {
                element.animate([
                    { transform: 'scale(1)', opacity: 1 },
                    { transform: 'scale(1.05)', opacity: 0.8 },
                    { transform: 'scale(1)', opacity: 1 }
                ], {
                    duration: 300,
                    easing: 'ease-out'
                });
            } else {
                // Fallback CSS
                element.style.transition = 'all 0.3s ease';
                element.style.transform = 'scale(1.05)';
                
                setTimeout(() => {
                    element.style.transform = 'scale(1)';
                }, 300);
            }
            
            element.textContent = formattedValue;
            
            // Agregar clase para styling adicional
            element.classList.add('metric-updated');
            setTimeout(() => {
                element.classList.remove('metric-updated');
            }, 300);
        }
    }
    
    formatValue(element, value) {
        const format = element.dataset.format;
        
        if (!format) return String(value);
        
        switch (format) {
            case 'number':
                return this.formatNumber(value);
            case 'percentage':
                return this.formatPercentage(value);
            case 'currency':
                return this.formatCurrency(value);
            case 'compact':
                return this.formatCompact(value);
            default:
                return String(value);
        }
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('en-US').format(num);
    }
    
    formatPercentage(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'percent',
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }).format(value);
    }
    
    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(value);
    }
    
    formatCompact(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return String(num);
    }
    
    // ===== SCHEDULING =====
    
    scheduleNext(delay) {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
        }
        
        this.timeoutId = setTimeout(() => {
            this.updateMetrics();
        }, delay);
    }
    
    // ===== ERROR HANDLING =====
    
    handleError(error) {
        console.error('[MetricsManager] Update failed:', error);
        
        this.retryCount++;
        
        if (this.retryCount <= this.options.retryAttempts) {
            // Exponential backoff
            this.currentInterval = Math.min(
                this.options.interval * Math.pow(this.options.backoffMultiplier, this.retryCount),
                this.options.maxBackoff
            );
            
            console.log(`[MetricsManager] Retry ${this.retryCount}/${this.options.retryAttempts} in ${this.currentInterval}ms`);
            
            this.eventBus.emit('metrics:retry', {
                attempt: this.retryCount,
                nextInterval: this.currentInterval
            });
        } else {
            // Max retries reached, stop polling
            console.error('[MetricsManager] Max retries reached, stopping');
            this.stop();
            
            this.eventBus.emit('metrics:failed', { error });
        }
    }
    
    // ===== PUBLIC API =====
    
    addMetric(metricName, element) {
        this.registerMetric(metricName, element);
    }
    
    removeMetric(metricName, element) {
        const elements = this.metrics.get(metricName);
        if (elements) {
            const index = elements.indexOf(element);
            if (index > -1) {
                elements.splice(index, 1);
            }
            
            if (elements.length === 0) {
                this.metrics.delete(metricName);
            }
        }
    }
    
    forceUpdate() {
        return this.updateMetrics(true);
    }
    
    setInterval(interval) {
        this.options.interval = interval;
        this.currentInterval = interval;
        
        if (this.isRunning) {
            this.stop();
            this.start();
        }
    }
    
    getMetrics() {
        return Array.from(this.metrics.keys());
    }
    
    getStatus() {
        return {
            isRunning: this.isRunning,
            metricCount: this.metrics.size,
            currentInterval: this.currentInterval,
            retryCount: this.retryCount
        };
    }
    
    // ===== CLEANUP =====
    
    cleanupStaleElements() {
        this.metrics.forEach((elements, metricName) => {
            const validElements = elements.filter(el => document.contains(el));
            
            if (validElements.length === 0) {
                this.metrics.delete(metricName);
            } else if (validElements.length < elements.length) {
                this.metrics.set(metricName, validElements);
            }
        });
        
        console.log(`[MetricsManager] Cleanup complete. ${this.metrics.size} metrics remaining`);
    }
    
    destroy() {
        this.stop();
        this.metrics.clear();
        this.pendingUpdates.clear();
        console.log('[MetricsManager] Destroyed');
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MetricsManager;
} else {
    window.MetricsManager = MetricsManager;
}
