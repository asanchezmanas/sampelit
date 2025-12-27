document.addEventListener('alpine:init', () => {
    Alpine.data('simulator', () => ({
        // State
        config: {
            traffic: 5000,
            baseline_cr: 5.0,
            uplift: 10.0,
            confidence: 95
        },
        loading: false,
        results: null,
        chart: null,
        darkMode: false,

        init() {
            this.darkMode = JSON.parse(localStorage.getItem('darkMode')) || false;
            this.$watch('darkMode', val => {
                localStorage.setItem('darkMode', JSON.stringify(val));
                this.updateChartTheme();
            });

            // Run initial simulation
            this.runSimulation();
        },

        async runSimulation() {
            this.loading = true;
            try {
                // Use the service directly (if global) or via store if we added it there (not really fit for store state yet, direct service is fine for tools)
                // Assuming experimentService is globally available from alpine-store.js logic
                const service = window.ExperimentService ? new ExperimentService(new APIClient()) : null;
                // Better yet, just reuse the one instantiated in alpine-store if accessible, or instantiate one.
                // Since this is a standalone tool, we can instantiate a fresh service or rely on global.
                // Let's rely on standard pattern:

                const apiClient = new APIClient();
                const expService = new ExperimentService(apiClient);

                const response = await expService.forecast({
                    traffic_daily: parseInt(this.config.traffic),
                    baseline_cr: parseFloat(this.config.baseline_cr) / 100,
                    uplift: parseFloat(this.config.uplift) / 100,
                    confidence_target: parseFloat(this.config.confidence) / 100
                });

                if (response) {
                    this.results = response;
                    this.renderChart(response.forecast);
                }
            } catch (error) {
                console.error("Simulation failed:", error);
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Simulation failed', type: 'error' } }));
            } finally {
                this.loading = false;
            }
        },

        renderChart(dataSeries) {
            const options = {
                series: [{
                    name: 'Projected P-Value',
                    data: dataSeries
                }],
                chart: {
                    type: 'area',
                    height: 350,
                    fontFamily: 'Manrope, sans-serif',
                    toolbar: { show: false },
                    animations: { enabled: true }
                },
                theme: { mode: this.darkMode ? 'dark' : 'light' },
                colors: ['#1E3A8A'], // Primary Navy
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.4,
                        opacityTo: 0.05,
                        stops: [0, 90, 100]
                    }
                },
                stroke: { curve: 'smooth', width: 2 },
                xaxis: {
                    categories: Array.from({ length: dataSeries.length }, (_, i) => `Day ${i + 1}`),
                    labels: { style: { fontSize: '10px', colors: '#9CA3AF' } },
                    axisBorder: { show: false },
                    axisTicks: { show: false }
                },
                yaxis: {
                    min: 0,
                    max: 0.20, // Focus on significance area
                    tickAmount: 4,
                    labels: {
                        style: { fontSize: '10px', colors: '#9CA3AF' },
                        formatter: (val) => val.toFixed(3)
                    }
                },
                annotations: {
                    yaxis: [{
                        y: 0.05,
                        borderColor: '#10b981',
                        label: {
                            borderColor: '#10b981',
                            style: { color: '#fff', background: '#10b981', fontSize: '10px' },
                            text: 'Significance (p < 0.05)'
                        }
                    }]
                },
                grid: {
                    borderColor: this.darkMode ? '#333' : '#f3f4f6',
                    strokeDashArray: 4
                },
                dataLabels: { enabled: false }
            };

            const chartEl = document.querySelector("#convergenceChart");
            if (this.chart) {
                this.chart.destroy();
            }
            if (chartEl) {
                chartEl.innerHTML = ""; // Clear placeholder
                this.chart = new ApexCharts(chartEl, options);
                this.chart.render();
            }
        },

        updateChartTheme() {
            if (this.chart) {
                this.chart.updateOptions({
                    theme: { mode: this.darkMode ? 'dark' : 'light' },
                    grid: { borderColor: this.darkMode ? '#333' : '#f3f4f6' }
                });
            }
        }
    }));
});
