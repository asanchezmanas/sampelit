document.addEventListener('alpine:init', () => {
    Alpine.data('billingController', () => ({
        loading: true,
        saving: false,
        subscription: {
            plan_name: 'Business Pro',
            status: 'active',
            renewal_date: 'Oct 24, 2025',
            usage: {
                mau: { current: 45000, limit: 100000, percent: 45 },
                experiments: { current: 8, limit: 15, percent: 53 }
            },
            payment_method: {
                type: 'Visa',
                last4: '4242',
                expiry: '12/25',
                holder: 'Alex Morgan',
                billing_address: 'Bahnhofstrasse 12, Zurich'
            }
        },
        invoices: [],

        async init() {
            console.log('Billing Controller Initializing...');
            await this.fetchBillingData();
        },

        async fetchBillingData() {
            this.loading = true;
            try {
                // Realistic wait to show skeleton/loading
                // const response = await apiClient.get('/billing');
                await new Promise(resolve => setTimeout(resolve, 800));

                // Mock data since endpoint might be pending backend implementation
                this.invoices = [
                    { id: 'INV-2023-009', date: '24 Sep, 2023', amount: '€149.00', plan: 'Business Pro', status: 'paid' },
                    { id: 'INV-2023-008', date: '24 Aug, 2023', amount: '€149.00', plan: 'Business Pro', status: 'paid' },
                    { id: 'INV-2023-007', date: '24 Jul, 2023', amount: '€149.00', plan: 'Business Pro', status: 'paid' },
                    { id: 'INV-2023-006', date: '24 Jun, 2023', amount: '€49.00', plan: 'Starter', status: 'archived' }
                ];
            } catch (error) {
                console.error('Error fetching billing data:', error);
                window.showToast?.('Error loading billing information', 'error');
            } finally {
                this.loading = false;
            }
        },

        async downloadInvoice(id) {
            window.showToast?.(`Starting download for ${id}...`, 'success');
            // Mock download action
            await new Promise(resolve => setTimeout(resolve, 500));
        },

        contactSupport() {
            window.location.href = 'contact_v2.html';
        },

        upgradePlan() {
            window.location.href = 'pricing_v2.html';
        }
    }));
});
