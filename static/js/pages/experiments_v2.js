document.addEventListener('alpine:init', () => {
    Alpine.data('experimentsTable', () => ({
        search: '',
        currentPage: 1,
        perPage: 10,
        sortColumn: 'created_at',
        sortDirection: 'desc',
        // Note: 'data' is removed as it's now managed by the store

        async init() {
            console.log('Experiments Table Initializing...');
            // Load experiments from the store on init
            await Alpine.store('experiments').fetchAll();
        },

        // Getters that proxy to the store state
        get loading() { return Alpine.store('experiments').loading; },
        get data() { return Alpine.store('experiments').list; },

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
            // Defensive copy to avoid mutating store directly if using sort() in place
            // But here we use toSorted or slice.sort
            return [...this.data].sort((a, b) => {
                let aVal = a[this.sortColumn];
                let bVal = b[this.sortColumn];

                // Handle complex nested or null values gracefully
                if (aVal == null) aVal = '';
                if (bVal == null) bVal = '';

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
                (exp.name && exp.name.toLowerCase().includes(q)) ||
                (exp.url && exp.url.toLowerCase().includes(q)) ||
                (exp.status && exp.status.toLowerCase().includes(q))
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

        async deleteExperiment(id) {
            // Delegate logic to the store
            await Alpine.store('experiments').delete(id);
        }
    }));
});
