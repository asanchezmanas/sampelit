document.addEventListener('alpine:init', () => {
    Alpine.data('experimentDetail', () => ({
        loading: true,
        experimentId: null, // Will extract from URL or context
        data: {
            experiment_name: 'Loading...',
            status: 'active',
            total_visitors: 0,
            total_conversions: 0,
            overall_conversion_rate: 0,
            statistical_significance: 0,
            elements: []
        },
        activeTab: 'overview',
        charts: {
            conversion: null,
            bayesian: null
        },

        init() {
            // Extract ID from URL query param for now, or mock
            // In a real app, this might come from the path /experiment/123
            // For now, we'll try to find it in URL params or default to a demo ID
            const urlParams = new URLSearchParams(window.location.search);
            this.experimentId = urlParams.get('id');

            this.darkMode = JSON.parse(localStorage.getItem('darkMode')) || false;
            this.$watch('darkMode', val => {
                localStorage.setItem('darkMode', JSON.stringify(val));
                this.updateChartsTheme();
            });

            this.fetchData();
        },

        async fetchData() {
            if (!this.experimentId) {
                console.warn("No experiment ID found, using mock data for UI demo");
                this.loadMockData();
                return;
            }

            this.loading = true;
            try {
                const client = new APIClient();
                const response = await client.get(`/analytics/experiment/${this.experimentId}`);

                if (response) {
                    this.data = response;
                    this.processDataForCharts();
                }
            } catch (error) {
                console.error("Failed to fetch experiment details:", error);
                this.loadMockData(); // Fallback
            } finally {
                this.loading = false;
            }
        },

        processDataForCharts() {
            if (!this.data.elements || this.data.elements.length === 0) {
                this.data.human_insight = {
                    title: "Awaiting Discovery...",
                    recommendation: "Still gathering the first data points to provide a reliable direction.",
                    confidence_label: "Low Confidence",
                    color: "gray"
                };
                return;
            }

            const primaryElement = this.data.elements[0];
            const variants = primaryElement.variants || [];

            // 1. Bayesian Logic & Plain Language Translation
            let winProb = 0;
            if (primaryElement.bayesian_stats && primaryElement.bayesian_stats.winner) {
                winProb = primaryElement.bayesian_stats.winner.probability_best * 100;
            }

            // Human-Readable Mapping
            this.data.human_insight = this.translateStatsToHuman(winProb, primaryElement.statistical_significance);

            // 2. Business Impact (Extra Conversions & Uplift)
            this.calculateBusinessImpact(primaryElement);

            // 3. Statistical Significance
            this.data.statistical_significance = winProb.toFixed(1);

            // 4. Enrich variants for Table Display
            this.enrichVariants(primaryElement);

            this.renderBayesianChart(winProb);

            // 5. Conversion Chart
            let chartData = this.prepareChartData(primaryElement);
            this.renderConversionChart(chartData);
        },

        translateStatsToHuman(prob, isSignificant) {
            if (prob >= 95 && isSignificant) {
                return {
                    title: "Clear Winner Found",
                    recommendation: "Implement the top-performing variant immediately to maximize your yield.",
                    confidence_label: "Statistically Verified",
                    color: "emerald"
                };
            } else if (prob >= 90) {
                return {
                    title: "Trending Positive",
                    recommendation: "One variant is showing very strong signs of winning. Keep it running to confirm.",
                    confidence_label: "High Confidence",
                    color: "blue"
                };
            } else if (prob < 60) {
                return {
                    title: "Experimental Tie",
                    recommendation: "No clear distinction yet. We recommend letting it run for a few more days.",
                    confidence_label: "Gathering Evidence",
                    color: "amber"
                };
            } else {
                return {
                    title: "Optimization in Progress",
                    recommendation: "Insights are forming. Your variants are being tested against control.",
                    confidence_label: "Analysis Active",
                    color: "indigo"
                };
            }
        },

        calculateBusinessImpact(element) {
            const variants = element.variants || [];
            if (variants.length < 2) return;

            const control = variants.find(v => v.is_control) || variants[0];
            const winner = variants.find(v => v.variant_index === element.best_variant_index) || variants[0];

            if (winner && control && control.conversion_rate > 0) {
                const upliftRate = (winner.conversion_rate - control.conversion_rate);
                const upliftPct = (upliftRate / control.conversion_rate) * 100;

                // Extra Conversions calculation:
                // Total traffic * (Winner Rate - Control Rate) 
                const totalVisitors = this.data.total_visitors || 0;
                const extraConversions = Math.max(0, Math.round(totalVisitors * upliftRate));

                this.data.business_impact = {
                    extra_conversions: extraConversions,
                    uplift_percentage: upliftPct.toFixed(1),
                    status: upliftPct > 0 ? 'positive' : 'stable'
                };
            }
        },

        enrichVariants(element) {
            const variants = element.variants || [];
            const control = variants.find(v => v.is_control) || variants[0];
            const bayesianResults = (element.bayesian_stats && element.bayesian_stats.variants) ? element.bayesian_stats.variants : [];

            element.variants = variants.map(v => {
                const bayesianVar = bayesianResults.find(b => b.variant_id === v.variant_id) || {};
                let uplift = 0;
                if (control && control.conversion_rate > 0) {
                    uplift = ((v.conversion_rate - control.conversion_rate) / control.conversion_rate) * 100;
                }

                return {
                    ...v,
                    uplift: uplift,
                    probability_best: (bayesianVar.probability_best || 0) * 100,
                    is_control: v === control
                };
            });
        },

        prepareChartData(element) {
            if (!element.daily_stats || element.daily_stats.length === 0) return null;

            const dates = element.daily_stats.map(d => {
                const date = new Date(d.date);
                return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
            });

            const variants = element.variants || [];
            const series = variants.map(v => ({
                name: v.name || 'Variant',
                data: []
            }));

            element.daily_stats.forEach(day => {
                day.variant_stats.forEach(vs => {
                    const seriesItem = series.find(s => s.name === vs.name);
                    if (seriesItem) {
                        seriesItem.data.push((vs.conversion_rate * 100).toFixed(1));
                    }
                });
            });

            return { categories: dates, series: series };
        },

        loadMockData() {
            this.data = {
                experiment_name: 'Homepage Hero Test',
                status: 'active',
                total_visitors: 12450,
                total_conversions: 1543,
                overall_conversion_rate: 0.124,
                elements: [{
                    bayesian_stats: {
                        winner: { probability_best: 0.952 }
                    },
                    variants: [
                        { name: 'Control', conversion_rate: 0.10 },
                        { name: 'Variant B', conversion_rate: 0.12 }
                    ],
                    daily_stats: [
                        { date: '2025-01-01', variant_stats: [{ name: 'Control', conversion_rate: 0.08 }, { name: 'Variant B', conversion_rate: 0.09 }] },
                        { date: '2025-01-02', variant_stats: [{ name: 'Control', conversion_rate: 0.09 }, { name: 'Variant B', conversion_rate: 0.10 }] },
                        { date: '2025-01-03', variant_stats: [{ name: 'Control', conversion_rate: 0.095 }, { name: 'Variant B', conversion_rate: 0.11 }] },
                        { date: '2025-01-04', variant_stats: [{ name: 'Control', conversion_rate: 0.10 }, { name: 'Variant B', conversion_rate: 0.12 }] }
                    ]
                }]
            };
            this.processDataForCharts();
            this.loading = false;
        },

        renderBayesianChart(probability) {
            const options = {
                series: [probability.toFixed(1)],
                chart: {
                    type: 'radialBar',
                    height: 320,
                    fontFamily: 'Manrope, sans-serif',
                },
                plotOptions: {
                    radialBar: {
                        startAngle: -135,
                        endAngle: 135,
                        hollow: {
                            margin: 15,
                            size: '65%',
                            background: 'transparent',
                        },
                        track: {
                            background: this.darkMode ? '#374151' : '#f1f5f9',
                            strokeWidth: '100%',
                            margin: 0,
                        },
                        dataLabels: { show: false }
                    }
                },
                fill: {
                    type: 'gradient',
                    gradient: {
                        shade: 'dark',
                        type: 'horizontal',
                        shadeIntensity: 0.5,
                        gradientToColors: ['#10b981'],
                        inverseColors: true,
                        opacityFrom: 1,
                        opacityTo: 1,
                        stops: [0, 100]
                    }
                },
                stroke: { lineCap: 'round' },
                colors: ['#1E3A8A'],
                labels: ['Confidence'],
            };

            const chartEl = document.querySelector("#bayesianChart");
            if (chartEl) {
                if (this.charts.bayesian) this.charts.bayesian.destroy();
                this.charts.bayesian = new ApexCharts(chartEl, options);
                this.charts.bayesian.render();
            }

            // Update text manually if needed or bind via Alpine
            // (We are binding via Alpine in HTML: x-text="...")
        },

        renderConversionChart(chartData = null) {
            // Default mock data if no real data
            let days = ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'];
            let series = [
                { name: 'Control', data: [10, 10.2, 10.5, 10.3, 10.8, 11.0, 11.1] },
                { name: 'Variant B', data: [10, 11.5, 12.0, 12.5, 13.0, 13.5, 13.8] }
            ];

            // Use real data if passed
            if (chartData) {
                days = chartData.categories;
                series = chartData.series;
            }

            const options = {
                series: series,
                chart: {
                    type: 'area',
                    height: 320,
                    fontFamily: 'Manrope, sans-serif',
                    toolbar: { show: false },
                    animations: { enabled: true }
                },
                colors: ['#94a3b8', '#10b981', '#3b82f6', '#f59e0b'], // Extended color palette for more variants
                fill: {
                    type: 'gradient',
                    gradient: {
                        shadeIntensity: 1,
                        opacityFrom: 0.4,
                        opacityTo: 0.05,
                        stops: [0, 90, 100]
                    }
                },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 2 },
                xaxis: {
                    categories: days,
                    axisBorder: { show: false },
                    axisTicks: { show: false },
                    labels: { style: { colors: '#9CA3AF', fontSize: '11px' } }
                },
                yaxis: {
                    labels: { style: { colors: '#9CA3AF', fontSize: '11px' }, formatter: (val) => val + '%' }
                },
                grid: {
                    borderColor: this.darkMode ? '#374151' : '#f1f5f9',
                    strokeDashArray: 4
                },
                tooltip: { theme: this.darkMode ? 'dark' : 'light' }
            };

            const chartEl = document.querySelector("#conversionChart");
            if (chartEl) {
                if (this.charts.conversion) this.charts.conversion.destroy();
                this.charts.conversion = new ApexCharts(chartEl, options);
                this.charts.conversion.render();
            }
        },

        updateChartsTheme() {
            // Re-render to pick up new logic or updateOptions
            if (this.charts.bayesian) {
                this.charts.bayesian.updateOptions({
                    plotOptions: { radialBar: { track: { background: this.darkMode ? '#374151' : '#f1f5f9' } } }
                });
            }
            if (this.charts.conversion) {
                this.charts.conversion.updateOptions({
                    grid: { borderColor: this.darkMode ? '#374151' : '#f1f5f9' },
                    tooltip: { theme: this.darkMode ? 'dark' : 'light' }
                });
            }
        },

        formatNumber(num) {
            if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
            if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
            return num.toString();
        },

        formatPercent(num) {
            return (num * 100).toFixed(1) + '%';
        }
    }));
});
