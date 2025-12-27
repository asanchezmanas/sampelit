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
        showUpgradeModal: false,
        billingCycle: 'monthly', // 'monthly' or 'yearly'
        pricingPlans: [
            {
                name: 'Starter',
                price: { monthly: 49, yearly: 39 },
                description: 'Perfect for early-stage startups and solo entrepreneurs.',
                features: ['5,000 MAU', '3 Experiments', 'Standard Support'],
                icon: 'rocket',
                color: 'blue'
            },
            {
                name: 'Business Pro',
                price: { monthly: 149, yearly: 119 },
                description: 'Our most popular plan for scaling growth teams.',
                features: ['100,000 MAU', 'Unlimited Experiments', 'Priority Support', 'Custom Domains'],
                icon: 'rocket_launch',
                color: 'sampelit',
                current: true
            },
            {
                name: 'Enterprise',
                price: { monthly: 'Custom', yearly: 'Custom' },
                description: 'Tailored solutions for global organizations with complex needs.',
                features: ['Unlimited MAU', 'Custom SLA', 'Dedicated Manager', 'Audit Logs'],
                icon: 'corporate_fare',
                color: 'indigo'
            }
        ],
        invoices: [],

        async init() {
            console.log('Billing Controller Initializing...');
            await this.fetchBillingData();
        },

        async fetchBillingData() {
            this.loading = true;
            try {
                // Instantiate service directly for this page (or use store if we had one)
                const api = new APIClient();
                const billingService = new BillingService(api);

                // Parallel fetch
                const [sub, invoices] = await Promise.all([
                    billingService.getSubscription(),
                    billingService.listInvoices()
                ]);

                this.subscription = sub;
                this.invoices = invoices;

            } catch (error) {
                console.error('Error fetching billing data:', error);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Error loading billing information', type: 'error' } }));
            } finally {
                this.loading = false;
            }
        },

        async downloadInvoice(id) {
            window.showToast?.(`Extracting PDF for ${id}...`, 'success');
            await new Promise(resolve => setTimeout(resolve, 800));
        },

        contactSupport() {
            window.location.href = 'contact_v2.html';
        },

        openUpgradeModal() {
            this.showUpgradeModal = true;
        },

        switchPlan(planName) {
            window.showToast?.(`Switching to ${planName} plan...`, 'info');
            setTimeout(() => {
                this.showUpgradeModal = false;
                window.showToast?.(`Subscription updated successfully!`, 'success');
            }, 1500);
        }
    }));
});
