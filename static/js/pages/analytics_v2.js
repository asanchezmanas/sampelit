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
        },

        // SOTA: Export to CSV (client-side)
        exportCSV() {
            const data = [
                ['Metric', 'Value'],
                ['Total Visitors', this.stats.total_visitors],
                ['Trend', this.stats.trend + '%'],
                ['Desktop', this.stats.devices?.desktop || 0],
                ['Mobile', this.stats.devices?.mobile || 0],
                ['Tablet', this.stats.devices?.tablet || 0]
            ];

            // Add traffic sources
            this.stats.traffic_sources.forEach(source => {
                data.push([source.name, source.visitors]);
            });

            const csv = data.map(row => row.join(',')).join('\n');
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = `sampelit-analytics-${this.period}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);

            // Toast notification
            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: 'CSV exported successfully!', type: 'success' }
            }));
        },

        // SOTA: Export Chart to PNG
        exportPNG() {
            if (this.charts.yield) {
                this.charts.yield.dataURI().then(({ imgURI }) => {
                    const link = document.createElement('a');
                    link.href = imgURI;
                    link.download = `sampelit-analytics-${this.period}.png`;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);

                    window.dispatchEvent(new CustomEvent('toast:show', {
                        detail: { message: 'Chart exported as PNG!', type: 'success' }
                    }));
                });
            } else {
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'No chart to export', type: 'error' }
                }));
            }
        },

        // SOTA: Comparison Mode
        comparisonMode: false,
        comparisonExperimentId: null,
        comparisonData: null,

        toggleComparisonMode() {
            this.comparisonMode = !this.comparisonMode;
            if (!this.comparisonMode) {
                this.comparisonExperimentId = null;
                this.comparisonData = null;
                this.renderCharts(); // Re-render without comparison
            }
        },

        async addComparisonExperiment(experimentId) {
            this.comparisonExperimentId = experimentId;

            // Fetch comparison data
            try {
                const store = Alpine.store('analytics');
                this.comparisonData = await store.fetchForExperiment(experimentId, this.period);

                // Re-render chart with overlay
                this.renderYieldChartWithComparison();

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Comparison data loaded', type: 'success' }
                }));
            } catch (error) {
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Failed to load comparison data', type: 'error' }
                }));
            }
        },

        renderYieldChartWithComparison() {
            // Extend the existing chart with a second series
            if (this.charts.yield && this.comparisonData) {
                this.charts.yield.updateSeries([
                    { name: 'Current', data: this.stats.traffic_sources.map(s => s.visitors || 0) },
                    { name: 'Comparison', data: this.comparisonData.map(s => s.visitors || 0) }
                ]);
            }
        },

        // SOTA: Timeline Annotations
        annotations: [],

        addAnnotation(date, label) {
            this.annotations.push({ date, label, id: Date.now() });
            this.applyAnnotations();

            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: `Annotation added: ${label}`, type: 'success' }
            }));
        },

        removeAnnotation(id) {
            this.annotations = this.annotations.filter(a => a.id !== id);
            this.applyAnnotations();
        },

        applyAnnotations() {
            if (this.charts.yield) {
                const xaxisAnnotations = this.annotations.map(a => ({
                    x: new Date(a.date).getTime(),
                    borderColor: '#f59e0b',
                    label: {
                        text: a.label,
                        style: { background: '#f59e0b', color: '#fff' }
                    }
                }));

                this.charts.yield.updateOptions({
                    annotations: { xaxis: xaxisAnnotations }
                });
            }
        }
    }));
});
