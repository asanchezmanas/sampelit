// static/js/managers/experiment-manager.js

/**
 * Experiment Manager - Gestiona operaciones de experimentos
 * 
 * Responsabilidades:
 * - CRUD de experimentos
 * - Cambios de estado (start, pause, stop)
 * - Actualización de datos
 * - Sincronización con backend
 */
class ExperimentManager {
    constructor(api, state, eventBus, uiManager) {
        this.api = api;
        this.state = state;
        this.eventBus = eventBus;
        this.ui = uiManager;
        
        this.init();
    }
    
    init() {
        // Suscribirse a eventos relevantes
        this.eventBus.on('experiment:refresh-requested', (data) => {
            this.refreshExperiment(data.experimentId);
        });
    }
    
    // ===== CREATE =====
    
    async createExperiment(data) {
        try {
            this.ui.showLoading(true);
            
            const response = await this.api.post('/api/experiments', data);
            
            if (response.success) {
                // Actualizar estado
                this.state.addExperiment(response.data);
                
                // Notificar
                this.eventBus.emit('experiment:created', response.data);
                this.ui.showToast('Experiment created successfully!', 'success');
                
                return response.data;
            }
            
        } catch (error) {
            this.handleError('create', error);
            throw error;
        } finally {
            this.ui.showLoading(false);
        }
    }
    
    navigateToCreate() {
        window.location.href = '/experiments/new';
    }
    
    // ===== READ =====
    
    async getExperiment(experimentId) {
        try {
            const response = await this.api.get(`/api/experiments/${experimentId}`);
            
            if (response.success) {
                return response.data;
            }
            
        } catch (error) {
            this.handleError('get', error);
            throw error;
        }
    }
    
    async listExperiments(filters = {}) {
        try {
            const response = await this.api.get('/api/experiments', filters);
            
            if (response.success) {
                return response.data;
            }
            
        } catch (error) {
            this.handleError('list', error);
            throw error;
        }
    }
    
    // ===== UPDATE =====
    
    async updateExperiment(experimentId, updates) {
        try {
            this.ui.showLoading(true);
            
            const response = await this.api.patch(`/api/experiments/${experimentId}`, updates);
            
            if (response.success) {
                // Actualizar estado local
                this.state.updateExperiment(experimentId, response.data);
                
                // Actualizar UI
                this.updateExperimentCard(experimentId, response.data);
                
                // Notificar
                this.eventBus.emit('experiment:updated', response.data);
                this.ui.showToast('Experiment updated successfully!', 'success');
                
                return response.data;
            }
            
        } catch (error) {
            this.handleError('update', error);
            throw error;
        } finally {
            this.ui.showLoading(false);
        }
    }
    
    // ===== DELETE =====
    
    async deleteExperiment(experimentId) {
        // Confirmación
        if (!confirm('Are you sure you want to delete this experiment? This action cannot be undone.')) {
            return false;
        }
        
        try {
            this.ui.showLoading(true);
            
            const response = await this.api.delete(`/api/experiments/${experimentId}`);
            
            if (response.success) {
                // Actualizar estado
                this.state.removeExperiment(experimentId);
                
                // Remover de UI
                const card = document.querySelector(`[data-experiment-id="${experimentId}"]`);
                if (card) {
                    card.remove();
                }
                
                // Notificar
                this.eventBus.emit('experiment:deleted', { experimentId });
                this.ui.showToast('Experiment deleted successfully!', 'success');
                
                return true;
            }
            
        } catch (error) {
            this.handleError('delete', error);
            return false;
        } finally {
            this.ui.showLoading(false);
        }
    }
    
    // ===== STATE CHANGES =====
    
    async startExperiment(experimentId) {
        try {
            this.ui.showLoading(true);
            
            const response = await this.api.post(`/api/experiments/${experimentId}/start`);
            
            if (response.success) {
                // Actualizar estado
                this.state.updateExperiment(experimentId, { 
                    status: 'active',
                    started_at: new Date().toISOString()
                });
                
                // Actualizar UI
                this.updateExperimentCard(experimentId, response.data);
                
                // Notificar
                this.eventBus.emit('experiment:started', response.data);
                this.ui.showToast('Experiment started successfully!', 'success');
                
                return response.data;
            }
            
        } catch (error) {
            this.handleError('start', error);
            throw error;
        } finally {
            this.ui.showLoading(false);
        }
    }
    
    async pauseExperiment(experimentId) {
        try {
            this.ui.showLoading(true);
            
            const response = await this.api.post(`/api/experiments/${experimentId}/pause`);
            
            if (response.success) {
                // Actualizar estado
                this.state.updateExperiment(experimentId, { 
                    status: 'paused' 
                });
                
                // Actualizar UI
                this.updateExperimentCard(experimentId, response.data);
                
                // Notificar
                this.eventBus.emit('experiment:paused', response.data);
                this.ui.showToast('Experiment paused successfully!', 'success');
                
                return response.data;
            }
            
        } catch (error) {
            this.handleError('pause', error);
            throw error;
        } finally {
            this.ui.showLoading(false);
        }
    }
    
    async stopExperiment(experimentId) {
        if (!confirm('Are you sure you want to stop this experiment? This will end the test.')) {
            return false;
        }
        
        try {
            this.ui.showLoading(true);
            
            const response = await this.api.post(`/api/experiments/${experimentId}/stop`);
            
            if (response.success) {
                // Actualizar estado
                this.state.updateExperiment(experimentId, { 
                    status: 'completed',
                    completed_at: new Date().toISOString()
                });
                
                // Actualizar UI
                this.updateExperimentCard(experimentId, response.data);
                
                // Notificar
                this.eventBus.emit('experiment:stopped', response.data);
                this.ui.showToast('Experiment stopped successfully!', 'success');
                
                return response.data;
            }
            
        } catch (error) {
            this.handleError('stop', error);
            throw error;
        } finally {
            this.ui.showLoading(false);
        }
    }
    
    // ===== REFRESH & SYNC =====
    
    async refreshExperiment(experimentId) {
        try {
            const response = await this.api.get(`/api/experiments/${experimentId}`);
            
            if (response.success) {
                // Actualizar estado
                this.state.updateExperiment(experimentId, response.data);
                
                // Actualizar UI
                this.updateExperimentCard(experimentId, response.data);
                
                // Notificar
                this.eventBus.emit('experiment:refreshed', response.data);
                
                return response.data;
            }
            
        } catch (error) {
            console.error('Failed to refresh experiment:', error);
            throw error;
        }
    }
    
    async refreshAllExperiments() {
        try {
            const experiments = this.state.get('experiments') || [];
            const refreshPromises = experiments.map(exp => 
                this.refreshExperiment(exp.id).catch(err => {
                    console.error(`Failed to refresh experiment ${exp.id}:`, err);
                    return null;
                })
            );
            
            await Promise.all(refreshPromises);
            
            this.eventBus.emit('experiments:all-refreshed');
            
        } catch (error) {
            console.error('Failed to refresh all experiments:', error);
        }
    }
    
    // ===== UI UPDATES =====
    
    updateExperimentCard(experimentId, experimentData) {
        const card = document.querySelector(`[data-experiment-id="${experimentId}"]`);
        if (!card) return;
        
        // Actualizar badge de estado
        const statusBadge = card.querySelector('.status-badge');
        if (statusBadge && experimentData.status) {
            statusBadge.className = `status-badge badge badge-${experimentData.status}`;
            statusBadge.textContent = this.formatStatus(experimentData.status);
        }
        
        // Actualizar métricas live
        const metricsElements = card.querySelectorAll('[data-live-metric]');
        metricsElements.forEach(element => {
            const metric = element.dataset.liveMetric;
            if (experimentData[metric] !== undefined) {
                this.animateValueChange(element, experimentData[metric]);
            }
        });
        
        // Actualizar botones de acción según estado
        this.updateActionButtons(card, experimentData.status);
    }
    
    updateActionButtons(card, status) {
        const startBtn = card.querySelector('[data-action="start-experiment"]');
        const pauseBtn = card.querySelector('[data-action="pause-experiment"]');
        const stopBtn = card.querySelector('[data-action="stop-experiment"]');
        
        if (status === 'draft') {
            if (startBtn) startBtn.classList.remove('hidden');
            if (pauseBtn) pauseBtn.classList.add('hidden');
            if (stopBtn) stopBtn.classList.add('hidden');
        } else if (status === 'active') {
            if (startBtn) startBtn.classList.add('hidden');
            if (pauseBtn) pauseBtn.classList.remove('hidden');
            if (stopBtn) stopBtn.classList.remove('hidden');
        } else if (status === 'paused') {
            if (startBtn) startBtn.classList.remove('hidden');
            if (pauseBtn) pauseBtn.classList.add('hidden');
            if (stopBtn) stopBtn.classList.remove('hidden');
        } else {
            if (startBtn) startBtn.classList.add('hidden');
            if (pauseBtn) pauseBtn.classList.add('hidden');
            if (stopBtn) stopBtn.classList.add('hidden');
        }
    }
    
    animateValueChange(element, newValue) {
        const currentValue = element.textContent;
        
        if (currentValue !== String(newValue)) {
            // Animación simple
            element.style.transition = 'all 0.3s ease';
            element.style.transform = 'scale(1.05)';
            
            setTimeout(() => {
                element.textContent = newValue;
                element.style.transform = 'scale(1)';
            }, 150);
        }
    }
    
    // ===== NAVIGATION =====
    
    viewExperiment(experimentId) {
        window.location.href = `/experiment/${experimentId}`;
    }
    
    editExperiment(experimentId) {
        window.location.href = `/experiments/${experimentId}/edit`;
    }
    
    // ===== UTILITIES =====
    
    formatStatus(status) {
        const statusMap = {
            'draft': 'Draft',
            'active': 'Active',
            'paused': 'Paused',
            'completed': 'Completed',
            'archived': 'Archived'
        };
        
        return statusMap[status] || status;
    }
    
    getExperimentFromState(experimentId) {
        return this.state.getExperiment(experimentId);
    }
    
    getActiveExperiments() {
        return this.state.getActiveExperiments();
    }
    
    // ===== ERROR HANDLING =====
    
    handleError(operation, error) {
        console.error(`Experiment ${operation} error:`, error);
        
        let message = `Failed to ${operation} experiment. Please try again.`;
        
        if (error.response?.data?.detail) {
            message = error.response.data.detail;
        } else if (error.message) {
            message = error.message;
        }
        
        this.ui.showToast(message, 'error');
        this.eventBus.emit('experiment:error', { operation, error });
    }
    
    // ===== CLEANUP =====
    
    destroy() {
        // Cleanup si es necesario
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExperimentManager;
} else {
    window.ExperimentManager = ExperimentManager;
}
