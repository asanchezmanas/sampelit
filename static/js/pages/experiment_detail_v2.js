/**
 * Experiment Detail Controller (V2)
 * Refactorizado para usar Alpine.store('experiments').fetchOne()
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('experimentDetail', () => ({
        loading: true,
        experimentId: null,
        data: {
            experiment_name: 'Loading...',
            status: 'active',
            // Default safe empty state
            elements: []
        },
        activeTab: 'overview',
        modal: {
            variant: false
        },
        selectedVariant: null,
        charts: {
            conversion: null,
            bayesian: null
        },

        init() {
            // 1. Get ID from URL
            const urlParams = new URLSearchParams(window.location.search);
            this.experimentId = urlParams.get('id');

            // 2. Dark mode sync
            this.darkMode = JSON.parse(localStorage.getItem('darkMode')) || false;
            this.$watch('darkMode', val => {
                localStorage.setItem('darkMode', JSON.stringify(val));
                this.updateChartsTheme();
            });

            this.fetchData();
        },

        async fetchData() {
            if (!this.experimentId) {
                console.warn("No experiment ID provided");
                // Fallback demo for stateless preview
                this.loadMockData();
                return;
            }

            this.loading = true;
            try {
                // Delegate to Global Store
                const experiment = await Alpine.store('experiments').fetchOne(this.experimentId);

                if (experiment) {
                    this.data = experiment;
                    this.processDataForCharts();
                } else {
                    console.error("Experiment not found");
                    // Could redirect or show error
                }
            } catch (error) {
                console.error("Error loading experiment details:", error);
            } finally {
                this.loading = false;
            }
        },

        // --- Logic below remains mostly view-specific ---

        processDataForCharts() {
            if (!this.data.elements || this.data.elements.length === 0) {
                this.data.human_insight = {
                    title: "Awaiting Discovery...",
                    recommendation: "Still gathering initial data.",
                    confidence_label: "Low Confidence",
                    color: "gray"
                };
                return;
            }

            const primaryElement = this.data.elements[0];

            // 1. Bayesian Logic
            let winProb = 0;
            if (primaryElement.bayesian_stats && primaryElement.bayesian_stats.winner) {
                winProb = primaryElement.bayesian_stats.winner.probability_best * 100;
            }

            this.data.human_insight = this.translateStatsToHuman(winProb, primaryElement.statistical_significance);
            this.data.statistical_significance = winProb.toFixed(1);

            // 2. Business Impact
            this.calculateBusinessImpact(primaryElement);

            // 3. Render
            this.enrichVariants(primaryElement);
            this.renderBayesianChart(winProb);

            const chartData = this.prepareChartData(primaryElement);
            this.renderConversionChart(chartData);
        },

        translateStatsToHuman(prob, isSignificant) {
            if (prob >= 95 && isSignificant) {
                return { title: "Clear Winner Found", recommendation: "Implement the winner immediately.", confidence_label: "Statistically Verified", color: "emerald" };
            } else if (prob >= 90) {
                return { title: "Trending Positive", recommendation: "Strong winner emerging. Keep running.", confidence_label: "High Confidence", color: "blue" };
            } else if (prob < 60) {
                return { title: "Experimental Tie", recommendation: "No clear distinction yet.", confidence_label: "Gathering Evidence", color: "amber" };
            } else {
                return { title: "Optimization in Progress", recommendation: "Testing ongoing.", confidence_label: "Analysis Active", color: "indigo" };
            }
        },

        calculateBusinessImpact(element) {
            const variants = element.variants || [];
            if (variants.length < 2) return;

            const control = variants.find(v => v.is_control) || variants[0];
            const winnerIdx = element.best_variant_index;
            const winner = variants.find(v => v.variant_index === winnerIdx) || variants[0];

            if (winner && control && control.conversion_rate > 0) {
                const upliftRate = (winner.conversion_rate - control.conversion_rate);
                const upliftPct = (upliftRate / control.conversion_rate) * 100;
                const totalVisitors = this.data.total_visitors || 0;

                this.data.business_impact = {
                    extra_conversions: Math.max(0, Math.round(totalVisitors * upliftRate)),
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
            const dates = element.daily_stats.map(d => new Date(d.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }));

            const variants = element.variants || [];
            const series = variants.map(v => ({
                name: v.name || 'Variant',
                data: []
            }));

            element.daily_stats.forEach(day => {
                day.variant_stats.forEach(vs => {
                    const seriesItem = series.find(s => s.name === vs.name);
                    if (seriesItem) seriesItem.data.push((vs.conversion_rate * 100).toFixed(1));
                });
            });

            return { categories: dates, series: series };
        },

        openVariantDetails(variant) {
            this.selectedVariant = variant;
            this.modal.variant = true;
        },

        // Legacy Mocks kept ONLY for direct file opening without ID
        loadMockData() {
            this.data = {
                experiment_name: 'Homepage Hero Test (Demo)',
                status: 'active',
                total_visitors: 12450,
                elements: [{
                    bayesian_stats: { winner: { probability_best: 0.952 } },
                    variants: [
                        { name: 'Control', conversion_rate: 0.10, is_control: true },
                        { name: 'Variant B', conversion_rate: 0.138, is_control: false }
                    ],
                    daily_stats: []
                }]
            };
            this.processDataForCharts();
            this.loading = false;
        },

        // Charts Rendering (Same as before, simplified for brevity)
        renderBayesianChart(probability) {
            const isDark = document.documentElement.classList.contains('dark');
            const options = {
                series: [probability.toFixed(1)],
                chart: { type: 'radialBar', height: 320, fontFamily: 'Manrope, sans-serif' },
                plotOptions: {
                    radialBar: {
                        hollow: { size: '70%' },
                        track: { background: isDark ? '#374151' : '#f1f5f9' },
                        dataLabels: { show: false }
                    }
                },
                fill: { type: 'gradient', gradient: { shade: 'dark', type: 'horizontal', gradientToColors: ['#10b981'], stops: [0, 100] } },
                colors: ['#0f172a'], labels: ['Confidence']
            };
            const chartEl = document.querySelector("#bayesianChart");
            if (chartEl) {
                if (this.charts.bayesian) this.charts.bayesian.destroy();
                this.charts.bayesian = new ApexCharts(chartEl, options);
                this.charts.bayesian.render();
            }
        },

        renderConversionChart(chartData) {
            const isDark = document.documentElement.classList.contains('dark');
            const options = {
                series: chartData ? chartData.series : [],
                chart: { type: 'area', height: 320, fontFamily: 'Manrope, sans-serif', toolbar: { show: false } },
                colors: ['#94a3b8', '#10b981'],
                fill: { type: 'gradient', gradient: { opacityFrom: 0.45, opacityTo: 0.05 } },
                dataLabels: { enabled: false },
                stroke: { curve: 'smooth', width: 3 },
                xaxis: { categories: chartData ? chartData.categories : [], labels: { style: { colors: '#9CA3AF' } } },
                grid: { borderColor: isDark ? '#374151' : '#f1f5f9' },
                tooltip: { theme: isDark ? 'dark' : 'light' }
            };
            const chartEl = document.querySelector("#conversionChart");
            if (chartEl) {
                if (this.charts.conversion) this.charts.conversion.destroy();
                this.charts.conversion = new ApexCharts(chartEl, options);
                this.charts.conversion.render();
            }
        },

        updateChartsTheme() {
            // Theme update logic
            if (this.charts.bayesian) this.charts.bayesian.updateOptions({ plotOptions: { radialBar: { track: { background: this.darkMode ? '#374151' : '#f1f5f9' } } } });
            if (this.charts.conversion) this.charts.conversion.updateOptions({ grid: { borderColor: this.darkMode ? '#374151' : '#f1f5f9' }, tooltip: { theme: this.darkMode ? 'dark' : 'light' } });
        },

        formatNumber(num) { return nFormatter(num); },
        formatPercent(num) { return (num * 100).toFixed(1) + '%'; }
    }));
});

// Tiny helper
function nFormatter(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
    return num ? num.toString() : '0';
}
