/**
 * Integrations Controller (V2)
 * Manages the integrations page with dynamic loading and connection handling.
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('integrationsController', () => ({
        // State
        integrations: [],
        loading: true,
        activeTab: 'all',
        searchQuery: '',
        connectingId: null, // Currently connecting integration ID

        // Services
        service: null,

        async init() {
            this.service = new IntegrationService(new APIClient());
            await this.loadIntegrations();
        },

        async loadIntegrations() {
            this.loading = true;
            try {
                this.integrations = await this.service.getAll();
            } catch (error) {
                console.error('Failed to load integrations', error);
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Failed to load integrations', type: 'error' }
                }));
            } finally {
                this.loading = false;
            }
        },

        /**
         * Filter integrations by category and search
         */
        get filteredIntegrations() {
            let result = this.integrations;

            // Filter by category
            if (this.activeTab !== 'all') {
                result = result.filter(i => i.category === this.activeTab);
            }

            // Filter by search
            if (this.searchQuery.trim()) {
                const query = this.searchQuery.toLowerCase();
                result = result.filter(i =>
                    i.name.toLowerCase().includes(query) ||
                    i.description.toLowerCase().includes(query)
                );
            }

            return result;
        },

        /**
         * Get count of connected integrations
         */
        get connectedCount() {
            return this.integrations.filter(i => i.connected).length;
        },

        /**
         * Toggle connection state (optimistic UI)
         */
        async toggleConnection(integration) {
            const wasConnected = integration.connected;
            this.connectingId = integration.id;

            // Optimistic UI update
            integration.connected = !wasConnected;

            try {
                if (wasConnected) {
                    await this.service.disconnect(integration.id);
                    window.dispatchEvent(new CustomEvent('toast:show', {
                        detail: { message: `${integration.name} disconnected`, type: 'info' }
                    }));
                } else {
                    await this.service.connect(integration.id, {});
                    window.dispatchEvent(new CustomEvent('toast:show', {
                        detail: { message: `${integration.name} connected!`, type: 'success' }
                    }));
                }
            } catch (error) {
                // Revert on failure
                integration.connected = wasConnected;
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: `Failed to ${wasConnected ? 'disconnect' : 'connect'} ${integration.name}`, type: 'error' }
                }));
            } finally {
                this.connectingId = null;
            }
        },

        /**
         * Get icon for category
         */
        getCategoryIcon(category) {
            const icons = {
                analytics: 'insights',
                ecommerce: 'shopping_cart',
                marketing: 'campaign',
                webhooks: 'webhook'
            };
            return icons[category] || 'extension';
        }
    }));
});
