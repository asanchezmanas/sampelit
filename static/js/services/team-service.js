/**
 * Team Service
 * 
 * Capa de servicio para gestión de miembros y organización.
 */
class TeamService {
    /**
     * @param {APIClient} apiClient 
     */
    constructor(apiClient) {
        this.api = apiClient;
    }

    /**
     * Obtiene la lista de miembros
     * @returns {Promise<Array>}
     */
    async listMembers() {
        const response = await this.api.get('/team/members');
        return response.data || [];
    }

    /**
     * Invita un nuevo miembro
     * @param {string} email 
     * @param {string} role 
     */
    async inviteMember(email, role) {
        const response = await this.api.post('/team/invite', { email, role });
        return response.data;
    }

    /**
     * Actualiza el rol de un miembro
     * @param {string} memberId 
     * @param {string} newRole 
     */
    async updateRole(memberId, newRole) {
        const response = await this.api.patch(`/team/members/${memberId}/role`, { role: newRole });
        return response.data;
    }

    /**
     * Elimina un miembro
     * @param {string} memberId 
     */
    async removeMember(memberId) {
        const response = await this.api.delete(`/team/members/${memberId}`);
        return response.success;
    }

    /**
     * Obtiene info de la organización
     */
    async getOrganization() {
        const response = await this.api.get('/organization/info');
        return response.data;
    }
}

// Exponer globalmente
window.TeamService = TeamService;
