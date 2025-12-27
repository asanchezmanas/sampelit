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

        // Computeds
        get activeExperiments() {
            // Obtener experimentos activos del store
            return Alpine.store('experiments').list
                .filter(exp => exp.status === 'Running' || exp.status === 'active')
                .slice(0, 5); // Top 5
        },

        get recentActivity() {
            // Generar actividad basada en los experimentos reales
            // En un futuro esto vendría de un endpoint /activity-log
            const experiments = Alpine.store('experiments').list;
            const activities = [];

            experiments.forEach(exp => {
                activities.push({
                    type: exp.status === 'Running' ? 'started' : 'created',
                    experiment: exp.name,
                    time: this.formatRelativeTime(exp.created_at),
                    user: 'You' // Mock user
                });
            });

            return activities.slice(0, 10);
        },

        // Chart Logic (ApexCharts)
        initChart() {
            // Lógica intacta de TailAdmin Chart (chart-03-ish)
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
                colors: ['#0f172a', '#3b82f6'], // Navy + Blue
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

            const chartSelector = "#chartOne";
            if (document.querySelector(chartSelector)) {
                new ApexCharts(document.querySelector(chartSelector), options).render();
            }
        },

        // Helpers
        formatRelativeTime(dateString) {
            const date = new Date(dateString);
            const now = new Date();
            const diffInSeconds = Math.floor((now - date) / 1000);

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
        }
    }));
});
