/**
 * Analytics Controller (V2)
 * Refactorizado para usar Alpine.store('analytics')
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('analyticsDashboard', () => ({
        loading: true,
        period: '30d',
        // Local proxies to store state are handy but we can access directly too.
        // We'll map them in computeds or fetch logic.

        charts: {
            yield: null,
            device: null
        },

        async init() {
            // Watch for period changes to reload data
            this.$watch('period', async () => {
                await this.fetchData();
            });

            await this.fetchData();
        },

        // Computeds mapping to Store
        get stats() {
            const store = Alpine.store('analytics');
            return {
                total_visitors: store.global.total_visitors || 0,
                trend: store.global.trend || 0,
                traffic_sources: store.traffic || [],
                devices: store.devices || { desktop: 0, mobile: 0, tablet: 0 },
                page_performance: store.pages || [],
                // Adapter for countries if not in store yet, use mock fallbacks or add to store later
                countries: [
                    { name: 'United States', value: 65 },
                    { name: 'United Kingdom', value: 40 },
                    { name: 'Germany', value: 28 }
                ]
            };
        },

        async fetchData() {
            this.loading = true;
            try {
                // Delegate to Global Store
                await Alpine.store('analytics').fetchOverview(this.period);

                // Once data is in store, render charts
                this.renderCharts();

            } catch (error) {
                console.error('Error fetching analytics:', error);
            } finally {
                this.loading = false;
            }
        },

        renderCharts() {
            // Wait for DOM
            this.$nextTick(() => {
                this.renderYieldChart();
                this.renderDeviceChart();
                this.renderSparklines();
            });
        },

        renderSparklines() {
            this.stats.traffic_sources.forEach(source => {
                // Sparklines often come as simple array in API, e.g. source.history
                // If not present, we can mock visual for now or use real data if service provides it
                const visualData = source.series || [10, 20, 15, 25, 20, 30, 25];

                const options = {
                    series: [{ data: visualData }],
                    chart: {
                        type: 'area',
                        height: 40,
                        sparkline: { enabled: true },
                        animations: { enabled: false }
                    },
                    fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.4, opacityTo: 0.1, stops: [0, 100] } },
                    stroke: { curve: 'smooth', width: 2 },
                    colors: [source.yield >= 4 ? '#10b981' : '#f59e0b'],
                    tooltip: { enabled: false }
                };
                const el = document.querySelector(`#sparkline-${source.id}`);
                if (el) {
                    // Destroy old if exists to prevent leaks (generic unique ID approach recommended for prod)
                    // new ApexCharts(el, options).render();
                    el.innerHTML = ''; // Reset
                    new ApexCharts(el, options).render();
                }
            });
        },

        renderYieldChart() {
            const isDark = document.documentElement.classList.contains('dark');
            // TODO: Use real history data from Store if available. For now using structural mock for the big chart.
            const options = {
                series: [
                    { name: 'Discovery Velocity', data: [31, 40, 28, 51, 42, 109, 100] },
                    { name: 'Yield Efficiency', data: [11, 32, 45, 32, 34, 52, 41] }
                ],
                chart: { type: 'area', height: 350, toolbar: { show: false }, fontFamily: 'Manrope, sans-serif', zoom: { enabled: false } },
                colors: ['#0f172a', '#3b82f6'],
                fill: { type: 'gradient', gradient: { shadeIntensity: 1, opacityFrom: 0.45, opacityTo: 0.05, stops: [0, 100] } },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 3 },
                grid: { borderColor: isDark ? '#374151' : '#f1f5f9' },
                xaxis: { categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], labels: { style: { colors: '#9CA3AF' } } },
                yaxis: { labels: { style: { colors: '#9CA3AF' }, formatter: (val) => val >= 1000 ? (val / 1000).toFixed(1) + 'k' : val } },
                legend: { show: true, position: 'top', horizontalAlign: 'left' },
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
                chart: { type: 'donut', height: 300, fontFamily: 'Manrope, sans-serif' },
                labels: ['Desktop', 'Mobile', 'Tablet'],
                colors: ['#0f172a', '#3b82f6', '#94a3b8'],
                plotOptions: { pie: { donut: { size: '80%', labels: { show: true, total: { show: true, label: 'Devices' } } } } },
                dataLabels: { enabled: false },
                legend: { show: false },
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
            return num ? num.toLocaleString() : '0';
        },

        formatPercent(num) {
            return (num || 0).toFixed(1) + '%';
        }
    }));
});
