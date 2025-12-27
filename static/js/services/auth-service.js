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
        // En V2 real, esto retornaría un token JWT o cookie session
        // Por ahora simulamos la llamada al endpoint estándar OAuth2 o similar
        const response = await this.api.post('/auth/login', { username: email, password });
        return response.data;
    }

    async register(data) {
        // data: { first_name, last_name, email, password, company }
        const response = await this.api.post('/auth/register', data);
        return response.data;
    }

    async getProfile() {
        const response = await this.api.get('/users/me');
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
