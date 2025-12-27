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
        const response = await this.api.post(`/experiments/${id}/start`);
        return response.data;
    }

    /**
     * Pausa un experimento (Active -> Paused)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async pause(id) {
        const response = await this.api.post(`/experiments/${id}/pause`);
        return response.data;
    }

    /**
     * Detiene definitivamente un experimento (Active/Paused -> Completed)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async stop(id) {
        const response = await this.api.post(`/experiments/${id}/stop`);
        return response.data;
    }

    /**
     * Obtiene estadísticas detalladas (Resultados)
     * @param {string} id 
     * @returns {Promise<Object>}
     */
    async getResults(id) {
        const response = await this.api.get(`/experiments/${id}/results`);
        return response.data;
    }
}

// Exponer globalmente para uso en Alpine
window.ExperimentService = ExperimentService;
