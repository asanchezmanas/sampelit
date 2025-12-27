/**
 * Auth Service
 * 
 * Gestiona autenticación y perfil del usuario actual.
 */
class AuthService {
    constructor(apiClient) {
        this.api = apiClient;
    }

    async login(email, password) {
        // Backend expects 'email', not 'username'
        const response = await this.api.post('/auth/login', { email, password });
        return response.data;
    }

    async register(data) {
        // Backend expects 'name', not split names.
        // Frontend sends: { first_name, last_name, email, password, company }
        const payload = {
            email: data.email,
            password: data.password,
            name: `${data.first_name || ''} ${data.last_name || ''}`.trim(),
            company: data.company || '',
            role: 'client' // auto-default
        };
        const response = await this.api.post('/auth/register', payload);
        return response.data;
    }

    async getProfile() {
        // Backend endpoint is /auth/me
        const response = await this.api.get('/auth/me');
        // Fallback mock check handled by api client usually, or here
        if (!response.data && !response.success) {
            // Mock data for demo if API fails/is missing
            return {
                id: 'u1', first_name: 'John', last_name: 'Doe',
                email: 'john.doe@example.com', company: 'Acme Inc',
                plan: 'Pro Plan'
            };
        }
        return response.data;
    }

    async updateProfile(data) {
        const response = await this.api.put('/users/me', data);
        return response.data;
    }

    async updatePassword(currentPassword, newPassword) {
        const response = await this.api.post('/users/password', {
            current_password: currentPassword,
            new_password: newPassword
        });
        return response.success;
    }

    async logout() {
        await this.api.post('/auth/logout');
        window.location.href = '/login.html';
    }
}

window.AuthService = AuthService;
