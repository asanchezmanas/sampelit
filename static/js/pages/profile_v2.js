/**
 * Profile Controller (V2)
 * Refactorizado para usar Alpine.store('auth')
 */
document.addEventListener('alpine:init', () => {
    Alpine.data('profileController', () => ({
        // Local form state (copied from store on init)
        userForm: {
            first_name: '',
            last_name: '',
            email: '',
            company: ''
        },
        security: {
            current_password: '',
            new_password: '',
            confirm_password: ''
        },
        saving: false,

        init() {
            // Wait for store to be ready or watch it
            this.$watch('$store.auth.user', (val) => {
                if (val) this.syncForm(val);
            });

            // Initial sync if already loaded
            if (Alpine.store('auth').user) {
                this.syncForm(Alpine.store('auth').user);
            } else {
                Alpine.store('auth').fetchUser();
            }
        },

        syncForm(userData) {
            this.userForm = {
                first_name: userData.first_name || '',
                last_name: userData.last_name || '',
                email: userData.email || '',
                company: userData.company || ''
            };
        },

        // Computeds accessing Store directly for Read-Only display
        get user() {
            return Alpine.store('auth').user || {};
        },

        get fullName() {
            return Alpine.store('auth').fullName;
        },

        async saveChanges() {
            this.saving = true;
            try {
                // Delegate to store
                await Alpine.store('auth').updateProfile({
                    first_name: this.userForm.first_name,
                    last_name: this.userForm.last_name,
                    company: this.userForm.company
                });
            } finally {
                this.saving = false;
            }
        },

        async updatePassword() {
            if (this.security.new_password !== this.security.confirm_password) {
                window.dispatchEvent(new CustomEvent('toast:show', { detail: { message: 'Passwords do not match', type: 'error' } }));
                return;
            }

            this.saving = true;
            try {
                await Alpine.store('auth').updatePassword(
                    this.security.current_password,
                    this.security.new_password
                );
                // Reset form on success
                this.security = { current_password: '', new_password: '', confirm_password: '' };
            } finally {
                this.saving = false;
            }
        }
    }));
});
