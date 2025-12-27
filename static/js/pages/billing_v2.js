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
        },

        // SOTA: Usage Alert Color (green -> yellow -> red)
        getUsageColor(percent) {
            if (percent >= 90) return 'red';
            if (percent >= 70) return 'yellow';
            return 'emerald';
        },

        getUsageBarClass(percent) {
            const color = this.getUsageColor(percent);
            return {
                'bg-emerald-500': color === 'emerald',
                'bg-yellow-500': color === 'yellow',
                'bg-red-500': color === 'red'
            };
        },

        getUsageTextClass(percent) {
            const color = this.getUsageColor(percent);
            return {
                'text-emerald-600': color === 'emerald',
                'text-yellow-600': color === 'yellow',
                'text-red-600': color === 'red'
            };
        },

        // SOTA: Invoice PDF Generation (client-side)
        async generateInvoicePDF(invoice) {
            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: 'Generating PDF...', type: 'info' }
            }));

            // Simulate PDF generation (in production, use jsPDF)
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Create a simple text representation as downloadable file
            const content = `
INVOICE: ${invoice.id}
========================
Date: ${invoice.date}
Amount: ${invoice.amount}
Status: ${invoice.status}

Sampelit Inc.
Thank you for your business!
            `.trim();

            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = `invoice-${invoice.id}.txt`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: 'Invoice downloaded!', type: 'success' }
            }));
        },

        // SOTA: Pro-rata Calculator
        calculateProrata(targetPlan) {
            const currentPrice = this.pricingPlans.find(p => p.current)?.price[this.billingCycle] || 0;
            const targetPrice = this.pricingPlans.find(p => p.name === targetPlan)?.price[this.billingCycle] || 0;

            if (typeof targetPrice === 'string') return null; // Custom pricing

            // Calculate days remaining in current period
            const today = new Date();
            const renewalDate = new Date(this.subscription.renewal_date);
            const daysRemaining = Math.ceil((renewalDate - today) / (1000 * 60 * 60 * 24));
            const daysInMonth = 30;

            const currentCredit = (currentPrice / daysInMonth) * daysRemaining;
            const newCharge = (targetPrice / daysInMonth) * daysRemaining;
            const difference = newCharge - currentCredit;

            return {
                credit: currentCredit.toFixed(2),
                charge: newCharge.toFixed(2),
                difference: difference.toFixed(2),
                isUpgrade: difference > 0
            };
        }
    }));
});
