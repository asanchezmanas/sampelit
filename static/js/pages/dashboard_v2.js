/**
 * Dashboard Controller (V2)
 * Refactorizado para arquitectura híbrida (Alpine Store + Services)
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('dashboard', () => ({
        // Metrics State
        metrics: {
            total_discovery: 124592,
            yield_achieved: 48.2,
            success_ratio: 0.85,
            precision_score: 98.4
        },

        // UI State
        timeRange: 'Monthly',
        isLoading: true,

        // Timeline & Experiments are now proxies to Store

        async init() {
            console.log('Dashboard Initializing...');

            // 1. Cargar datos del Store
            await Alpine.store('experiments').fetchAll();

            // 2. Simular carga de métricas globales (TODO: MetricsService)
            setTimeout(() => {
                this.isLoading = false;
                this.initChart();
            }, 600);
        },

        // SOTA: Dynamic Greeting based on time of day
        get greeting() {
            const hour = new Date().getHours();
            if (hour < 12) return 'Good morning';
            if (hour < 18) return 'Good afternoon';
            return 'Good evening';
        },

        // SOTA: Get user name (from store or localStorage)
        get userName() {
            const user = localStorage.getItem('user_name') || 'there';
            return user;
        },

        // Computed: Activities derived from store data
        get activities() {
            const experiments = Alpine.store('experiments').list;
            // Create artificial "activities" based on experiment state
            // In a real app, this would come from an Audit Log API
            return experiments.slice(0, 5).map(exp => ({
                id: exp.id,
                type: exp.status === 'active' ? 'experiment_launch' : 'draft_created',
                title: exp.status === 'active' ? `Launched "${exp.name}"` : `Drafted "${exp.name}"`,
                description: exp.description || 'No description provided',
                time: this.formatRelativeTime(exp.created_at || new Date().toISOString())
            })).concat([
                // Mock system events for "alive" feel
                { id: 'sys-1', type: 'system_alert', title: 'Auto-Scaling Active', description: 'Traffic spike detected. Redis tier scaling.', time: '1 hour ago' },
                { id: 'sys-2', type: 'conversion_spike', title: 'Conversion Spike', description: '+15% uplift detected in pricing test.', time: '2 hours ago' }
            ]);
        },

        // Chart Logic (ApexCharts)
        initChart() {
            // Check if element exists before rendering
            const chartEl = document.querySelector("#chartOne");
            if (!chartEl) return;

            // ... (rest of chart options same as before, abbreviated for brevity if needed, but keeping full configuration is safer)
            const options = {
                series: [
                    { name: 'Total Revenue', data: [440, 505, 414, 671, 227, 413, 201, 352, 752, 320, 257, 160] },
                    { name: 'Profit', data: [23, 42, 35, 27, 43, 22, 17, 31, 22, 22, 12, 16] }
                ],
                chart: {
                    fontFamily: 'Manrope, sans-serif',
                    type: 'area',
                    height: 350,
                    toolbar: { show: false },
                    zoom: { enabled: false }
                },
                colors: ['#0f172a', '#3b82f6'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.3,
                        opacityTo: 0.05,
                        stops: [0, 90, 100]
                    }
                },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 2 },
                xaxis: {
                    type: 'category',
                    categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                    labels: { style: { colors: '#94a3b8', fontSize: '11px', fontWeight: 600 } }
                },
                yaxis: {
                    labels: {
                        style: { colors: '#94a3b8', fontSize: '11px', fontWeight: 600 },
                        formatter: (val) => val >= 100 ? (val / 100).toFixed(1) + 'k' : val
                    }
                },
                grid: {
                    borderColor: 'rgba(241, 245, 249, 0.5)',
                    strokeDashArray: 4,
                    xaxis: { lines: { show: true } },
                    yaxis: { lines: { show: true } }
                },
                legend: {
                    show: true,
                    position: 'top',
                    horizontalAlign: 'right',
                    fontSize: '11px',
                    fontWeight: 700,
                    markers: { radius: 12 }
                },
                tooltip: {
                    theme: 'light',
                    x: { show: true },
                    y: { formatter: (val) => val }
                }
            };

            // Clear previous if any (though Alpine handles init)
            chartEl.innerHTML = '';
            new ApexCharts(chartEl, options).render();
        },

        // Helpers
        getActivityIcon(type) {
            const icons = {
                'experiment_launch': 'rocket_launch',
                'draft_created': 'edit_note',
                'conversion_spike': 'trending_up',
                'system_alert': 'dns',
                'report_ready': 'analytics'
            };
            return icons[type] || 'circle'; // Default icon
        },

        formatRelativeTime(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);

            if (isNaN(diffInSeconds)) return 'Just now'; // Handle invalid dates

            if (diffInSeconds < 60) return 'Just now';
            if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
            if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
            return `${Math.floor(diffInSeconds / 86400)}d ago`;
        },

        formatNumber(num) {
            return new Intl.NumberFormat().format(num);
        },

        formatPercent(num) {
            return (num * 100).toFixed(2) + '%';
        },

        // ===== NUEVAS MEJORAS =====

        // Quick Actions
        quickActions: [
            { id: 'new-exp', label: 'New Experiment', icon: 'add', href: 'experiments_create_v2.html' },
            { id: 'view-analytics', label: 'View Analytics', icon: 'analytics', href: 'analytics_v2.html' },
            { id: 'invite-team', label: 'Invite Team', icon: 'person_add', href: 'settings_v2.html#team' }
        ],

        showQuickActionsModal: false,

        toggleQuickActions() {
            this.showQuickActionsModal = !this.showQuickActionsModal;
        },

        // Period Comparison
        previousPeriodMetrics: {
            total_discovery: 112340,
            yield_achieved: 42.1,
            success_ratio: 0.82,
            precision_score: 97.2
        },

        getMetricChange(current, previous) {
            if (!previous || previous === 0) return null;
            const change = ((current - previous) / previous) * 100;
            return {
                value: Math.abs(change).toFixed(1),
                direction: change >= 0 ? 'up' : 'down',
                isPositive: change >= 0
            };
        },

        get metricChanges() {
            return {
                total_discovery: this.getMetricChange(this.metrics.total_discovery, this.previousPeriodMetrics.total_discovery),
                yield_achieved: this.getMetricChange(this.metrics.yield_achieved, this.previousPeriodMetrics.yield_achieved),
                success_ratio: this.getMetricChange(this.metrics.success_ratio, this.previousPeriodMetrics.success_ratio),
                precision_score: this.getMetricChange(this.metrics.precision_score, this.previousPeriodMetrics.precision_score)
            };
        },

        // Sparkline data for metrics
        sparklineData: {
            total_discovery: [85, 92, 88, 95, 100, 105, 112, 108, 115, 120, 118, 124],
            yield_achieved: [38, 40, 42, 41, 44, 45, 43, 46, 47, 46, 48, 48],
            success_ratio: [78, 80, 82, 81, 83, 84, 83, 85, 84, 85, 85, 85],
            precision_score: [95, 96, 96, 97, 97, 97, 98, 98, 98, 98, 98, 98]
        },

        getSparklinePath(key, width = 60, height = 20) {
            const data = this.sparklineData[key];
            if (!data || data.length === 0) return '';

            const min = Math.min(...data);
            const max = Math.max(...data);
            const range = max - min || 1;

            const points = data.map((val, i) => {
                const x = (i / (data.length - 1)) * width;
                const y = height - ((val - min) / range) * height;
                return `${x},${y}`;
            });

            return `M${points.join(' L')}`;
        },

        // Refresh dashboard data
        async refreshDashboard() {
            this.isLoading = true;
            await Alpine.store('experiments').fetchAll();

            // Simulate metrics refresh
            setTimeout(() => {
                this.metrics.total_discovery += Math.floor(Math.random() * 100);
                this.isLoading = false;

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Dashboard refreshed', type: 'success' }
                }));
            }, 500);
        }
    }));
});
