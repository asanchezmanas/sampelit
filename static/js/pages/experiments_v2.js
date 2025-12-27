document.addEventListener('alpine:init', () => {
    Alpine.data('experimentsTable', () => ({
        search: '',
        currentPage: 1,
        perPage: 10,
        sortColumn: 'created_at',
        sortDirection: 'desc',
        data: [],
        loading: true,

        async init() {
            console.log('Experiments Table Initializing...');
            await this.fetchExperiments();
        },

        async fetchExperiments() {
            this.loading = true;
            try {
                // Mock delay
                await new Promise(resolve => setTimeout(resolve, 800));

                // Mock data in case API fails or for demo
                this.data = [
                    {
                        id: 1,
                        name: 'High-Value CTA Overhaul',
                        url: 'https://sampelit.com/checkout',
                        status: 'Running',
                        total_visitors: 12540,
                        variant_count: 3,
                        overall_conversion_rate: 0.124,
                        created_at: '2023-10-15T10:00:00Z'
                    },
                    {
                        id: 2,
                        name: 'Mobile Navigation Simplified',
                        url: 'https://sampelit.com/home',
                        status: 'Paused',
                        total_visitors: 45200,
                        variant_count: 2,
                        overall_conversion_rate: -0.021,
                        created_at: '2023-10-12T14:30:00Z'
                    },
                    {
                        id: 3,
                        name: 'Free Shipping Threshold Test',
                        url: 'https://sampelit.com/cart',
                        status: 'Running',
                        total_visitors: 8900,
                        variant_count: 2,
                        overall_conversion_rate: 0.057,
                        created_at: '2023-10-20T09:15:00Z'
                    },
                    {
                        id: 4,
                        name: 'Footer Social Proof Integration',
                        url: 'https://sampelit.com/',
                        status: 'Completed',
                        total_visitors: 120500,
                        variant_count: 3,
                        overall_conversion_rate: 0.082,
                        created_at: '2023-09-28T11:20:00Z'
                    },
                    {
                        id: 5,
                        name: 'Search Bar Autocomplete AI',
                        url: 'https://sampelit.com/search',
                        status: 'Draft',
                        total_visitors: 0,
                        variant_count: 1,
                        overall_conversion_rate: 0,
                        created_at: '2023-10-22T16:45:00Z'
                    },
                    {
                        id: 6,
                        name: 'Bento Grid vs List Layout',
                        url: 'https://sampelit.com/blog',
                        status: 'Running',
                        total_visitors: 22100,
                        variant_count: 2,
                        overall_conversion_rate: 0.034,
                        created_at: '2023-10-18T08:00:00Z'
                    }
                ];

                // In real implementation:
                // const response = await APIClient.get('/experiments');
                // if (response.data) this.data = response.data;
            } catch (error) {
                console.error('Failed to fetch experiments:', error);
                window.showToast?.('Failed to sync discoveries', 'error');
            } finally {
                this.loading = false;
            }
        },

        sortBy(column) {
            if (this.sortColumn === column) {
                this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                this.sortColumn = column;
                this.sortDirection = 'asc';
            }
            this.currentPage = 1;
        },

        get sortedData() {
            return [...this.data].sort((a, b) => {
                let aVal = a[this.sortColumn];
                let bVal = b[this.sortColumn];
                if (typeof aVal === 'string') aVal = aVal.toLowerCase();
                if (typeof bVal === 'string') bVal = bVal.toLowerCase();
                if (aVal < bVal) return this.sortDirection === 'asc' ? -1 : 1;
                if (aVal > bVal) return this.sortDirection === 'asc' ? 1 : -1;
                return 0;
            });
        },

        get filteredData() {
            const sorted = this.sortedData;
            if (!this.search) return sorted;
            const q = this.search.toLowerCase();
            return sorted.filter(exp =>
                exp.name.toLowerCase().includes(q) ||
                exp.url.toLowerCase().includes(q) ||
                exp.status.toLowerCase().includes(q)
            );
        },

        get paginatedData() {
            const start = (this.currentPage - 1) * this.perPage;
            return this.filteredData.slice(start, start + parseInt(this.perPage));
        },

        get totalPages() {
            return Math.max(1, Math.ceil(this.filteredData.length / this.perPage));
        },

        get totalEntries() { return this.filteredData.length; },
        get startEntry() { return this.totalEntries === 0 ? 0 : (this.currentPage - 1) * this.perPage + 1; },
        get endEntry() { return Math.min(this.currentPage * this.perPage, this.totalEntries); },

        prevPage() { if (this.currentPage > 1) this.currentPage--; },
        nextPage() { if (this.currentPage < this.totalPages) this.currentPage++; },
        goToPage(page) { this.currentPage = page; },

        deleteExperiment(id) {
            if (confirm('Are you sure you want to delete this discovery? This action cannot be undone.')) {
                this.data = this.data.filter(e => e.id !== id);
                window.showToast?.('Discovery deleted permanently', 'info');
            }
        }
    }));
});
