document.addEventListener('alpine:init', () => {
    Alpine.data('profileController', () => ({
        loading: true,
        saving: false,
        user: {
            first_name: '',
            last_name: '',
            email: '',
            company: '',
            plan: 'Pro Plan',
            initials: '??'
        },
        security: {
            current_password: '',
            new_password: '',
            confirm_password: ''
        },

        async init() {
            await this.fetchProfile();
        },

        async fetchProfile() {
            this.loading = true;
            try {
                const response = await apiClient.get('/users/me');
                if (response.success) {
                    this.user = {
                        ...this.user,
                        ...response.data
                    };
                    this.generateInitials();
                }
            } catch (error) {
                console.error('Error fetching profile:', error);
                window.showToast?.('Error loading profile data', 'error');
            } finally {
                this.loading = false;
            }
        },

        async saveChanges() {
            this.saving = true;
            try {
                const response = await apiClient.put('/users/me', {
                    first_name: this.user.first_name,
                    last_name: this.user.last_name,
                    company: this.user.company
                });

                if (response.success) {
                    window.showToast?.('Profile updated successfully', 'success');
                    this.generateInitials();
                }
            } catch (error) {
                console.error('Error updating profile:', error);
                window.showToast?.('Failed to update profile', 'error');
            } finally {
                this.saving = false;
            }
        },

        async updatePassword() {
            if (this.security.new_password !== this.security.confirm_password) {
                window.showToast?.('Passwords do not match', 'error');
                return;
            }

            this.saving = true;
            try {
                // In a real app: await apiClient.post('/users/password', this.security);
                await new Promise(resolve => setTimeout(resolve, 1000));
                window.showToast?.('Password updated successfully', 'success');
                this.security = { current_password: '', new_password: '', confirm_password: '' };
            } catch (error) {
                window.showToast?.('Error updating password', 'error');
            } finally {
                this.saving = false;
            }
        },

        generateInitials() {
            const f = this.user.first_name?.[0] || '';
            const l = this.user.last_name?.[0] || '';
            this.user.initials = (f + l).toUpperCase() || '??';
        },

        get fullName() {
            return `${this.user.first_name} ${this.user.last_name}`.trim() || 'User Name';
        }
    }));
});
