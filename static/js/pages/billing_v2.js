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
                // Realistic wait to show skeleton/loading
                await new Promise(resolve => setTimeout(resolve, 800));

                this.invoices = [
                    {
                        id: 'INV-2023-009',
                        date: '24 Sep, 2023',
                        amount: '€149.00',
                        plan: 'Business Pro',
                        status: 'paid',
                        items: [
                            { desc: 'Business Pro Subscription (Monthly)', qty: 1, price: 149.00 }
                        ]
                    },
                    {
                        id: 'INV-2023-008',
                        date: '24 Aug, 2023',
                        amount: '€149.00',
                        plan: 'Business Pro',
                        status: 'paid',
                        items: [
                            { desc: 'Business Pro Subscription (Monthly)', qty: 1, price: 149.00 }
                        ]
                    },
                    {
                        id: 'INV-2023-007',
                        date: '24 Jul, 2023',
                        amount: '€149.00',
                        plan: 'Business Pro',
                        status: 'paid',
                        items: [
                            { desc: 'Business Pro Subscription (Monthly)', qty: 1, price: 149.00 }
                        ]
                    },
                    {
                        id: 'INV-2023-006',
                        date: '24 Jun, 2023',
                        amount: '€49.00',
                        plan: 'Starter',
                        status: 'paid',
                        items: [
                            { desc: 'Starter Plan Subscription (Monthly)', qty: 1, price: 49.00 }
                        ]
                    }
                ];
            } catch (error) {
                console.error('Error fetching billing data:', error);
                window.showToast?.('Error loading billing information', 'error');
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
