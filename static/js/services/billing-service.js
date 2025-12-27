/**
 * Billing Service
 * 
 * Gestiona suscripciones, facturas y métodos de pago.
 */
class BillingService {
    constructor(apiClient) {
        this.api = apiClient;
    }

    async getSubscription() {
        const response = await this.api.get('/billing/subscription');
        // Mock fallback if API not ready
        if (!response.data && !response.success) {
            return {
                plan_name: 'Business Pro',
                status: 'active',
                renewal_date: 'Oct 24, 2025',
                usage: {
                    mau: { current: 45000, limit: 100000, percent: 45 },
                    experiments: { current: 8, limit: 15, percent: 53 }
                },
                payment_method: {
                    type: 'Visa', last4: '4242', expiry: '12/25', holder: 'Alex Morgan'
                }
            };
        }
        return response.data;
    }

    async listInvoices() {
        const response = await this.api.get('/billing/invoices');
        if (!response.data) {
            return [
                { id: 'INV-2023-009', date: '24 Sep, 2023', amount: '€149.00', status: 'paid', plan: 'Business Pro' },
                { id: 'INV-2023-008', date: '24 Aug, 2023', amount: '€149.00', status: 'paid', plan: 'Business Pro' }
            ];
        }
        return response.data;
    }

    async upgradePlan(planId, cycle) {
        return await this.api.post('/billing/upgrade', { plan_id: planId, cycle });
    }

    async downloadInvoice(id) {
        // En prod esto retornaría un blob o url
        return await this.api.get(`/billing/invoices/${id}/download`);
    }
}

window.BillingService = BillingService;
