document.addEventListener('alpine:init', () => {
    Alpine.data('analyticsDashboard', () => ({
        loading: true,
        period: '30d',
        stats: {
            total_visitors: 0,
            trend: 0,
            devices: { desktop: 0, mobile: 0, tablet: 0 },
            traffic_sources: [],
            page_performance: []
        },
        charts: {
            yield: null,
            device: null
        },

        async init() {
            console.log('Analytics Dashboard Initializing...');
            await this.fetchData();

            // Watch for period changes to reload data
            this.$watch('period', async () => {
                await this.fetchData();
            });
        },

        async fetchData() {
            this.loading = true;
            try {
                // In a real app, we would pass the period to the API
                // const response = await apiClient.get(`/analytics/global?period=${this.period}`);
                const response = await apiClient.get('/analytics/global');

                if (response.success) {
                    this.stats = {
                        ...this.stats,
                        total_visitors: response.data.total_visitors || 0,
                        trend: response.data.trend || 0
                    };

                    // Mock additional detailed data that might not be in the simple global endpoint yet
                    // but we want to show the UI full-featured
                    this.loadDetailedStats();

                    this.renderCharts();
                }
            } catch (error) {
                console.error('Error fetching analytics:', error);
            } finally {
                this.loading = false;
            }
        },

        loadDetailedStats() {
            // Devices (Mock logic if not in API)
            this.stats.devices = { desktop: 62, mobile: 31, tablet: 7 };

            // Traffic Sources with detailed data and sparkline mock series
            this.stats.traffic_sources = [
                { id: 1, source: 'Google Organic', icon: 'search', volume: 12450, integrity: 523, yield: 4.2, series: [10, 20, 15, 25, 22, 30, 28] },
                { id: 2, source: 'Direct Access', icon: 'link', volume: 8234, integrity: 412, yield: 5.0, series: [25, 22, 28, 32, 30, 35, 38] },
                { id: 3, source: 'Meta Services', icon: 'share', volume: 5120, integrity: 186, yield: 3.6, series: [15, 12, 18, 14, 20, 15, 12] },
                { id: 4, source: 'X Ecosystem', icon: 'rss_feed', volume: 2845, integrity: 89, yield: 3.1, series: [5, 8, 4, 10, 7, 12, 9] }
            ];

            // Page Performance
            this.stats.page_performance = [
                { uri: '/checkout', impressions: 8234, bounce: 24 },
                { uri: '/pricing', impressions: 6123, bounce: 31 },
                { uri: '/homepage', impressions: 5890, bounce: 42 }
            ];

            // Countries
            this.stats.countries = [
                { name: 'United States', value: 65 },
                { name: 'United Kingdom', value: 40 },
                { name: 'Germany', value: 28 }
            ];
        },

        renderCharts() {
            this.renderYieldChart();
            this.renderDeviceChart();
            this.$nextTick(() => {
                this.renderSparklines();
            });
        },

        renderSparklines() {
            this.stats.traffic_sources.forEach(source => {
                const options = {
                    series: [{ data: source.series }],
                    chart: {
                        type: 'area',
                        height: 40,
                        sparkline: { enabled: true },
                        animations: { enabled: false }
                    },
                    fill: {
                        type: 'gradient',
                        gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 100] }
                    },
                    stroke: { curve: 'smooth', width: 2 },
                    colors: [source.yield >= 4 ? '#10b981' : '#f59e0b'],
                    tooltip: { enabled: false }
                };
                const el = document.querySelector(`#sparkline-${source.id}`);
                if (el) {
                    new ApexCharts(el, options).render();
                }
            });
        },

        renderYieldChart() {
            const isDark = document.documentElement.classList.contains('dark');
            const options = {
                series: [
                    { name: 'Discovery Velocity', data: [31, 40, 28, 51, 42, 109, 100] },
                    { name: 'Yield Efficiency', data: [11, 32, 45, 32, 34, 52, 41] }
                ],
                chart: {
                    type: 'area',
                    height: 350,
                    toolbar: { show: false },
                    fontFamily: 'Manrope, sans-serif',
                    zoom: { enabled: false },
                    dropShadow: { enabled: true, top: 18, left: 0, blur: 4, opacity: 0.05 }
                },
                colors: ['#0f172a', '#3b82f6'],
                fill: {
                    type: 'gradient',
                    gradient: { shadeIntensity: 1, opacityFrom: 0.45, opacityTo: 0.05, stops: [0, 100] }
                },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 3 },
                grid: {
                    borderColor: isDark ? '#374151' : '#f1f5f9',
                    strokeDashArray: 4,
                    xaxis: { lines: { show: true } },
                    yaxis: { lines: { show: true } }
                },
                xaxis: {
                    categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                    labels: { style: { colors: '#9CA3AF', fontSize: '12px', fontWeight: 600 } }
                },
                yaxis: {
                    labels: {
                        style: { colors: '#9CA3AF', fontSize: '12px', fontWeight: 600 },
                        formatter: (val) => val >= 1000 ? (val / 1000).toFixed(1) + 'k' : val
                    }
                },
                legend: {
                    show: true,
                    position: 'top',
                    horizontalAlign: 'left',
                    fontSize: '11px',
                    fontWeight: 800,
                    textAnchor: 'start',
                    markers: { radius: 12 }
                },
                tooltip: { theme: isDark ? 'dark' : 'light' }
            };

            const chartEl = document.querySelector("#analyticsChart");
            if (chartEl) {
                if (this.charts.yield) this.charts.yield.destroy();
                this.charts.yield = new ApexCharts(chartEl, options);
                this.charts.yield.render();
            }
        },

        renderDeviceChart() {
            const isDark = document.documentElement.classList.contains('dark');

            const options = {
                series: [this.stats.devices.desktop, this.stats.devices.mobile, this.stats.devices.tablet],
                chart: {
                    type: 'donut',
                    height: 300,
                    fontFamily: 'Manrope, sans-serif'
                },
                labels: ['Desktop', 'Mobile', 'Tablet'],
                colors: ['#0f172a', '#3b82f6', '#94a3b8'],
                plotOptions: {
                    pie: {
                        donut: {
                            size: '80%',
                            labels: {
                                show: true,
                                name: { show: true, fontSize: '12px', fontWeight: 'bold' },
                                value: { show: true, fontSize: '24px', fontWeight: '800', color: isDark ? '#fff' : '#0f172a' },
                                total: { show: true, label: 'Devices', fontSize: '11px', fontWeight: 'bold', color: '#94a3b8' }
                            }
                        }
                    }
                },
                dataLabels: { enabled: false },
                legend: { show: false },
                stroke: { show: false },
                tooltip: { theme: isDark ? 'dark' : 'light' }
            };

            const chartEl = document.querySelector("#deviceChart");
            if (chartEl) {
                if (this.charts.device) this.charts.device.destroy();
                this.charts.device = new ApexCharts(chartEl, options);
                this.charts.device.render();
            }
        },

        formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
            return num.toLocaleString();
        },

        formatPercent(num) {
            return num.toFixed(1) + '%';
        }
    }));
});
