/**
 * Metrics Service
 * 
 * Capa de servicio para interactuar con los endpoints de analítica y reportes.
 */
class MetricsService {
    /**
     * @param {APIClient} apiClient 
     */
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * Obtiene métricas globales para un periodo dado
     * @param {string} period '24h', '7d', '30d', '12m'
     * @returns {Promise<Object>}
     */
    async getGlobalMetrics(period = '30d') {
        // En producción real:
        // return (await this.api.get(`/analytics/global`, { period })).data;

        // Simulación temporal para demo si el endpoint no soporta filtros aun
        const response = await this.api.get('/analytics/global');
        return response.data || response;
    }

    /**
     * Obtiene desglose de tráfico (Fuentes)
     * @returns {Promise<Array>}
     */
    async getTrafficSources(period = '30d') {
        const response = await this.api.get('/analytics/traffic');
        return response.data || [];
    }

    /**
     * Obtiene estadísticas de dispositivos
     * @returns {Promise<Object>} { desktop: %, mobile: %, tablet: % }
     */
    async getDeviceStats(period = '30d') {
        const response = await this.api.get('/analytics/devices');
        return response.data || { desktop: 0, mobile: 0, tablet: 0 };
    }

    /**
     * Obtiene rendimiento de páginas
     * @returns {Promise<Array>}
     */
    async getPagePerformance(period = '30d') {
        const response = await this.api.get('/analytics/pages');
        return response.data || [];
    }
}

// Exponer globalmente
window.MetricsService = MetricsService;
