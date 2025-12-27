/**
 * Auth Controller (V2)
 * Maneja Login y Signup pages.
 */
document.addEventListener('alpine:init', () => {

    // --- LOGIN CONTROLLER ---
    Alpine.data('loginController', () => ({
        email: '',
        password: '',
        loading: false,
        error: null,
        showPassword: false,
        shakeError: false, // SOTA: Shake animation trigger

        async submit() {
            this.loading = true;
            this.error = null;
            this.shakeError = false;
            try {
                // Initialize standalone service logic for these pages
                const api = new APIClient();
                const auth = new AuthService(api);

                await auth.login(this.email, this.password);

                // Redirect on success
                window.location.href = 'index_v2.html';
            } catch (err) {
                console.error('Login failed', err);
                this.error = 'Invalid credentials. Please try again.';

                // SOTA: Trigger shake and then reset
                this.shakeError = true;
                setTimeout(() => { this.shakeError = false; }, 500);

                // Mock redirect for demo purposes if backend assumes stateless
                if (err.status === 404 || err.status === 401) {
                    // For pure frontend demo without backend, uncomment next line:
                    // window.location.href = 'index_v2.html';
                }
            } finally {
                this.loading = false;
            }
        },

        // Demo helper for prototype
        demoLogin() {
            this.email = 'demo@sampelit.com';
            this.password = 'password';
        }
    }));

    // --- SIGNUP CONTROLLER ---
    Alpine.data('signupController', () => ({
        form: {
            first_name: '',
            last_name: '',
            email: '',
            password: '',
            company: ''
        },
        loading: false,
        error: null,

        async submit() {
            this.loading = true;
            this.error = null;
            try {
                const api = new APIClient();
                const auth = new AuthService(api);

                await auth.register(this.form);

                // Redirect to onboarding or login
                window.location.href = 'index_v2.html';
            } catch (err) {
                console.error('Signup failed', err);
                this.error = 'Registration failed. Try a different email.';
            } finally {
                this.loading = false;
            }
        }
    }));
});
