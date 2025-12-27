/**
 * Integration Service (V2)
 * Manages third-party integrations (Analytics, E-commerce, Marketing).
 */
class IntegrationService {
    constructor(api) {
        this.api = api || new APIClient();
    }

    /**
     * Get all available integrations with their connection status
     * @returns {Promise<Array>} List of integrations
     */
    async getAll() {
        try {
            return await this.api.get('/integrations');
        } catch (error) {
            console.warn('IntegrationService.getAll failed, using mock data', error);
            return this.getMockIntegrations();
        }
    }

    /**
     * Connect an integration
     * @param {string} id - Integration ID
     * @param {Object} config - Connection configuration (API keys, etc.)
     * @returns {Promise<Object>} Updated integration
     */
    async connect(id, config = {}) {
        try {
            return await this.api.post(`/integrations/${id}/connect`, config);
        } catch (error) {
            console.error('IntegrationService.connect failed', error);
            throw error;
        }
    }

    /**
     * Disconnect an integration
     * @param {string} id - Integration ID
     * @returns {Promise<void>}
     */
    async disconnect(id) {
        try {
            return await this.api.delete(`/integrations/${id}`);
        } catch (error) {
            console.error('IntegrationService.disconnect failed', error);
            throw error;
        }
    }

    /**
     * Mock data for demo/fallback
     */
    getMockIntegrations() {
        return [
            // Analytics
            { id: 'ga4', name: 'Google Analytics 4', category: 'analytics', icon: 'analytics', connected: true, description: 'Track visitors and conversions with GA4 integration.' },
            { id: 'mixpanel', name: 'Mixpanel', category: 'analytics', icon: 'query_stats', connected: false, description: 'Product analytics for user behavior insights.' },
            { id: 'amplitude', name: 'Amplitude', category: 'analytics', icon: 'show_chart', connected: false, description: 'Digital optimization and product analytics.' },
            { id: 'segment', name: 'Segment', category: 'analytics', icon: 'hub', connected: true, description: 'Customer data platform for unified tracking.' },

            // E-commerce
            { id: 'shopify', name: 'Shopify', category: 'ecommerce', icon: 'shopping_cart', connected: true, description: 'Sync experiments with your Shopify store.' },
            { id: 'woocommerce', name: 'WooCommerce', category: 'ecommerce', icon: 'storefront', connected: false, description: 'WordPress e-commerce integration.' },
            { id: 'bigcommerce', name: 'BigCommerce', category: 'ecommerce', icon: 'store', connected: false, description: 'Enterprise e-commerce platform.' },

            // Marketing
            { id: 'mailchimp', name: 'Mailchimp', category: 'marketing', icon: 'mail', connected: false, description: 'Email marketing automation.' },
            { id: 'hubspot', name: 'HubSpot', category: 'marketing', icon: 'campaign', connected: true, description: 'CRM and marketing automation.' },
            { id: 'klaviyo', name: 'Klaviyo', category: 'marketing', icon: 'mark_email_read', connected: false, description: 'E-commerce marketing platform.' },

            // Webhooks
            { id: 'slack', name: 'Slack', category: 'webhooks', icon: 'chat', connected: true, description: 'Get experiment notifications in Slack.' },
            { id: 'zapier', name: 'Zapier', category: 'webhooks', icon: 'bolt', connected: false, description: 'Connect to 5000+ apps via Zapier.' },
        ];
    }
}

// Export for use in controllers
if (typeof window !== 'undefined') {
    window.IntegrationService = IntegrationService;
}
