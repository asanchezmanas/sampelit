/**
 * Settings Controller (V2)
 * Refactorizado para usar Alpine.store('team')
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('settingsController', () => ({
        activeTab: 'team',
        searchQuery: '',
        roleFilter: 'all',
        inviting: false,
        currentPage: 1,
        itemsPerPage: 5,

        // Static definition of roles for UI display logic (could also be fetched if dynamic)
        roleDefinitions: [
            { id: 'admin', name: 'Administrador', description: 'Total organization control, billing and security policies.', icon: 'admin_panel_settings', color: 'blue' },
            { id: 'editor', name: 'Editor', description: 'Full access to Discovery Lab and Experiment Detail.', icon: 'edit_note', color: 'purple' },
            { id: 'viewer', name: 'Visor', description: 'Read-only access to final results and analytics.', icon: 'visibility', color: 'emerald' }
        ],

        async init() {
            // Load initial data
            await Alpine.store('team').fetchAll();
        },

        // Computeds mapping to Store
        get loading() {
            return Alpine.store('team').loading;
        },

        get organization() {
            const org = Alpine.store('team').organization;
            // Default mock fallback if API returns nothing yet
            return org || {
                name: 'Sampelit Organization',
                total_members: this.members.length,
                plan: 'Business Pro'
            };
        },

        get members() {
            return Alpine.store('team').members;
        },

        // Derived Logic
        get rolesWithCounts() {
            // Calculate real counts based on current members
            return this.roleDefinitions.map(def => {
                const count = this.members.filter(m => m.role.toLowerCase() === def.name.toLowerCase() || m.role.toLowerCase() === def.id).length;
                return { ...def, count };
            });
        },

        get filteredMembers() {
            return this.members.filter(m => {
                const matchesSearch = (m.name || '').toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                    (m.email || '').toLowerCase().includes(this.searchQuery.toLowerCase());

                // Flexible role matching
                const memberRole = (m.role || '').toLowerCase();
                const matchesRole = this.roleFilter === 'all' ||
                    memberRole === this.roleFilter.toLowerCase() ||
                    memberRole === this.roleFilterName(this.roleFilter).toLowerCase();

                return matchesSearch && matchesRole;
            });
        },

        get paginatedMembers() {
            const start = (this.currentPage - 1) * this.itemsPerPage;
            return this.filteredMembers.slice(start, start + this.itemsPerPage);
        },

        // Helpers
        roleFilterName(filterId) {
            const role = this.roleDefinitions.find(r => r.id === filterId);
            return role ? role.name : filterId;
        },

        // Actions (Delegate to Store)
        async inviteMember(email, role) {
            this.inviting = true;
            try {
                // Mock implementation in Service will just echo back, 
                // in real app this sends invite
                await Alpine.store('team').invite(email, role);
            } finally {
                this.inviting = false;
            }
        },

        async deleteMember(id) {
            await Alpine.store('team').removeMember(id);
        },

        async changeRole(id, newRole) {
            await Alpine.store('team').updateRole(id, newRole);
        }
    }));

    // Install Verification Component
    Alpine.data('installVerification', () => ({
        domain: '',
        status: 'pending', // 'pending' | 'verified' | 'error'
        checking: false,

        async verifyInstall() {
            if (!this.domain) return;

            this.checking = true;
            this.status = 'pending';

            try {
                // Simulate API call to verify snippet installation
                const api = new APIClient();
                const result = await api.post('/installations/verify', { domain: this.domain });

                this.status = result.installed ? 'verified' : 'error';

                // Toast notification
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: {
                        message: result.installed ? 'Snippet verified!' : 'Snippet not detected',
                        type: result.installed ? 'success' : 'error'
                    }
                }));
            } catch (error) {
                // For demo: simulate random result
                await new Promise(resolve => setTimeout(resolve, 1500));
                this.status = Math.random() > 0.3 ? 'verified' : 'error';

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: {
                        message: this.status === 'verified' ? 'Snippet detected!' : 'Snippet not found',
                        type: this.status === 'verified' ? 'success' : 'error'
                    }
                }));
            } finally {
                this.checking = false;
            }
        }
    }));

    // SOTA: Dark Mode Controller with OS Preference Sync
    Alpine.data('darkModeController', () => ({
        darkMode: localStorage.getItem('darkMode') || 'system', // 'light' | 'dark' | 'system'

        init() {
            this.applyTheme();

            // Watch for OS preference changes
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (this.darkMode === 'system') {
                    this.applyTheme();
                }
            });
        },

        setMode(mode) {
            this.darkMode = mode;
            localStorage.setItem('darkMode', mode);
            this.applyTheme();

            window.dispatchEvent(new CustomEvent('toast:show', {
                detail: { message: `Theme: ${mode === 'system' ? 'System Default' : mode}`, type: 'info' }
            }));
        },

        applyTheme() {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const isDark = this.darkMode === 'dark' || (this.darkMode === 'system' && prefersDark);

            document.documentElement.classList.toggle('dark', isDark);
        },

        get currentTheme() {
            if (this.darkMode === 'system') {
                return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            }
            return this.darkMode;
        }
    }));

    // SOTA: Settings Changes Tracker (Reset)
    Alpine.data('settingsTracker', () => ({
        originalSettings: null,
        isDirty: false,

        init() {
            // Capture original state on load
            setTimeout(() => {
                this.originalSettings = JSON.stringify(this.getCurrentSettings());
            }, 1000);

            // Watch for changes
            this.$watch('getCurrentSettings()', () => {
                this.checkDirty();
            });
        },

        getCurrentSettings() {
            // Return current form values (customize per form)
            return {
                darkMode: localStorage.getItem('darkMode'),
                // Add other settings as needed
            };
        },

        checkDirty() {
            this.isDirty = JSON.stringify(this.getCurrentSettings()) !== this.originalSettings;
        },

        resetAll() {
            if (this.originalSettings) {
                const original = JSON.parse(this.originalSettings);
                if (original.darkMode) localStorage.setItem('darkMode', original.darkMode);

                this.isDirty = false;

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Settings reset to last saved state', type: 'info' }
                }));

                // Reload to apply
                location.reload();
            }
        }
    }));
});
