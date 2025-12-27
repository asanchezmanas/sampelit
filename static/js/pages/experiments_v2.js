/**
 * Experiments Table Controller (V2)
 * SOTA Features: Deep Linking, Bulk Selection, Status Filter
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('experimentsTable', () => ({
        search: '',
        currentPage: 1,
        perPage: 10,
        sortColumn: 'created_at',
        sortDirection: 'desc',
        statusFilter: 'all', // SOTA: Filter by status
        selectedIds: [], // SOTA: Bulk Selection

        async init() {
            console.log('Experiments Table Initializing...');

            // SOTA: Deep Linking - Read URL params on init
            this.readFromURL();

            // Load experiments from the store on init
            await Alpine.store('experiments').fetchAll();

            // SOTA: Deep Linking - Watch for changes and update URL
            this.$watch('search', () => this.updateURL());
            this.$watch('statusFilter', () => this.updateURL());
            this.$watch('sortColumn', () => this.updateURL());
            this.$watch('sortDirection', () => this.updateURL());
            this.$watch('currentPage', () => this.updateURL());
        },

        // SOTA: Deep Linking - Read state from URL
        readFromURL() {
            const params = new URLSearchParams(window.location.search);
            this.search = params.get('q') || '';
            this.statusFilter = params.get('status') || 'all';
            this.sortColumn = params.get('sort') || 'created_at';
            this.sortDirection = params.get('dir') || 'desc';
            this.currentPage = parseInt(params.get('page')) || 1;
        },

        // SOTA: Deep Linking - Update URL without reload
        updateURL() {
            const params = new URLSearchParams();
            if (this.search) params.set('q', this.search);
            if (this.statusFilter !== 'all') params.set('status', this.statusFilter);
            if (this.sortColumn !== 'created_at') params.set('sort', this.sortColumn);
            if (this.sortDirection !== 'desc') params.set('dir', this.sortDirection);
            if (this.currentPage > 1) params.set('page', this.currentPage);

            const qs = params.toString();
            const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
            window.history.replaceState({}, '', url);
        },

        // Getters that proxy to the store state
        get loading() { return Alpine.store('experiments').loading; },
        get data() { return Alpine.store('experiments').list; },

        // SOTA: Check if all visible are selected
        get allSelected() {
            return this.paginatedData.length > 0 &&
                this.paginatedData.every(exp => this.selectedIds.includes(exp.id));
        },

        // SOTA: Toggle all on current page
        toggleAll() {
            if (this.allSelected) {
                this.paginatedData.forEach(exp => {
                    const idx = this.selectedIds.indexOf(exp.id);
                    if (idx > -1) this.selectedIds.splice(idx, 1);
                });
            } else {
                this.paginatedData.forEach(exp => {
                    if (!this.selectedIds.includes(exp.id)) {
                        this.selectedIds.push(exp.id);
                    }
                });
            }
        },

        // SOTA: Toggle single row
        toggleSelection(id) {
            const idx = this.selectedIds.indexOf(id);
            if (idx > -1) {
                this.selectedIds.splice(idx, 1);
            } else {
                this.selectedIds.push(id);
            }
        },

        isSelected(id) {
            return this.selectedIds.includes(id);
        },

        // SOTA: Bulk Actions
        async bulkArchive() {
            if (this.selectedIds.length === 0) return;

            for (const id of this.selectedIds) {
                await Alpine.store('experiments').updateStatus(id, 'archived');
            }

            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: `${this.selectedIds.length} experiments archived`, type: 'success' }
            }));

            this.selectedIds = [];
        },

        async bulkDelete() {
            if (this.selectedIds.length === 0) return;

            if (!confirm(`Delete ${this.selectedIds.length} experiments? This cannot be undone.`)) return;

            for (const id of this.selectedIds) {
                await Alpine.store('experiments').delete(id);
            }

            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: `${this.selectedIds.length} experiments deleted`, type: 'info' }
            }));

            this.selectedIds = [];
        },

        clearSelection() {
            this.selectedIds = [];
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
            let sorted = this.sortedData;

            // SOTA: Status filter
            if (this.statusFilter !== 'all') {
                sorted = sorted.filter(exp => exp.status === this.statusFilter);
            }

            // Search filter
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
            await Alpine.store('experiments').delete(id);
        }
    }));
});
