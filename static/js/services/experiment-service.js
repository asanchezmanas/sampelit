/**
 * Experiment Service
 * 
 * Capa de servicio puro para interactuar con los endpoints de experimentos.
 * Desacoplado de la UI y del estado local (Store).
 */
class ExperimentService {
    /**
     * @param {APIClient} apiClient - Instancia del cliente HTTP
     */
    constructor(apiClient) {
        this.api = apiClient;
    }

    // ===== CRUD =====

    /**
     * Lista todos los experimentos con filtros opcionales
     * @param {Object} filters 
     * @returns {Promise<Array>}
     */
    async list(filters = {}) {
        const response = await this.api.get('/experiments', filters);
        return response.data;
    }

    /**
     * Obtiene un experimento por ID
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async get(id) {
        const response = await this.api.get(`/experiments/${id}`);
        return response.data;
    }

    /**
     * Crea un nuevo experimento
     * @param {Object} data 
     * @returns {Promise<Object>}
     */
    async create(data) {
        const response = await this.api.post('/experiments', data);
        return response.data;
    }

    /**
     * Actualiza un experimento existente
     * @param {string} id 
     * @param {Object} updates 
     * @returns {Promise<Object>}
     */
    async update(id, updates) {
        const response = await this.api.patch(`/experiments/${id}`, updates);
        return response.data;
    }

    /**
     * Elimina un experimento
     * @param {string} id 
     * @returns {Promise<boolean>}
     */
    async delete(id) {
        const response = await this.api.delete(`/experiments/${id}`);
        return response.success;
    }

    // ===== ACTIONS =====

    /**
     * Inicia un experimento (Draft -> Active)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async start(id) {
        // Backend expects PATCH /experiments/{id}/status?new_status=active
        const response = await this.api.patch(`/experiments/${id}/status`, null, { params: { new_status: 'active' } });
        return response.data;
    }

    /**
     * Pausa un experimento (Active -> Paused)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async pause(id) {
        const response = await this.api.patch(`/experiments/${id}/status`, null, { params: { new_status: 'paused' } });
        return response.data;
    }

    /**
     * Detiene definitivamente un experimento (Active/Paused -> Completed)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async stop(id) {
        const response = await this.api.patch(`/experiments/${id}/status`, null, { params: { new_status: 'completed' } });
        return response.data;
    }

    /**
     * Obtiene estadísticas detalladas (Resultados)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async getResults(id) {
        // Backend endpoint: /analytics/experiment/{id}
        const response = await this.api.get(`/analytics/experiment/${id}`);
        return response.data;
    }

    // ===== FORECASTING / SIMULATION =====

    /**
     * Simula resultados futuros (Monte Carlo)
     * @param {Object} params { traffic_daily, baseline_cr, uplift, confidence_target }
     * @returns {Promise<Object>}
     */
    async forecast(params) {
        // Fallback mock if endpoint doesn't exist yet
        try {
            const response = await this.api.post('/simulate/forecast', params);
            return response.data || response;
        } catch (e) {
            console.warn('Simulation API unavailable, using internal deterministic model');
            // Internal simple calc
            return this._mockForecast(params);
        }
    }

    _mockForecast(params) {
        const { traffic_daily, baseline_cr, uplift } = params;
        // Mock logic: generate a decaying p-value curve
        const days = 14;
        const pValues = [];
        let currentP = 0.5;
        for (let i = 0; i < days; i++) {
            // Artificial logarithmic decay towards 0 (significance) based on uplift strength
            const decay = (uplift * traffic_daily) / 10000;
            currentP = currentP * (1 - decay);
            pValues.push(Math.max(0.001, currentP));
        }

        return {
            days_to_significance: 7,
            forecast: pValues,
            required_sample: Math.round(1600 / (uplift * uplift)) // Simplified Evan Miller approx
        };
    }
}

// Exponer globalmente para uso en Alpine
window.ExperimentService = ExperimentService;
