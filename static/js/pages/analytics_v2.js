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

            // Traffic Sources
            this.stats.traffic_sources = [
                { source: 'Google Organic', volume: 12450, integrity: 523, yield: 4.2 },
                { source: 'Direct Access', volume: 8234, integrity: 412, yield: 5.0 },
                { source: 'Meta Services', volume: 5120, integrity: 186, yield: 3.6 },
                { source: 'X Ecosystem', volume: 2845, integrity: 89, yield: 3.1 }
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
        },

        renderYieldChart() {
            const isDark = document.documentElement.classList.contains('dark');

            const options = {
                series: [{
                    name: 'Total Discoveries',
                    data: [31, 40, 28, 51, 42, 109, 100]
                }],
                chart: {
                    type: 'area',
                    height: 350,
                    toolbar: { show: false },
                    fontFamily: 'Manrope, sans-serif',
                    zoom: { enabled: false }
                },
                colors: ['#0f172a'],
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.45,
                        opacityTo: 0.05,
                        stops: [20, 100, 100, 100]
                    }
                },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 3 },
                grid: {
                    borderColor: isDark ? '#374151' : '#f1f5f9',
                    strokeDashArray: 4
                },
                xaxis: {
                    categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                    labels: { style: { colors: '#9CA3AF', fontSize: '12px' } }
                },
                yaxis: {
                    labels: { style: { colors: '#9CA3AF', fontSize: '12px' } }
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
                colors: ['#0f172a', '#1e3a8a', '#94a3b8'],
                plotOptions: {
                    pie: {
                        donut: {
                            size: '75%',
                            labels: {
                                show: true,
                                name: { show: true, fontSize: '12px', fontWeight: 'bold' },
                                value: { show: true, fontSize: '20px', fontWeight: 'extrabold' },
                                total: { show: true, label: 'Devices', fontSize: '12px' }
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
