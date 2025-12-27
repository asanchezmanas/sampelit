document.addEventListener('alpine:init', () => {
    Alpine.data('settingsController', () => ({
        activeTab: 'team',
        searchQuery: '',
        roleFilter: 'all',
        loading: true,
        inviting: false,
        organization: {
            name: 'Sampelit Corp',
            total_members: 19,
            plan: 'Business Pro'
        },
        members: [],
        roles: [
            { id: 'admin', name: 'Administradores', description: 'Acceso total a configuración, facturación y gestión de usuarios.', count: 2, icon: 'admin_panel_settings', color: 'blue' },
            { id: 'editor', name: 'Editores', description: 'Pueden crear, editar y lanzar experimentos A/B.', count: 5, icon: 'edit_note', color: 'purple' },
            { id: 'viewer', name: 'Visores', description: 'Solo lectura. Acceso a dashboards y resultados finales.', count: 12, icon: 'visibility', color: 'emerald' }
        ],

        async init() {
            console.log('Settings Controller Initializing...');
            await this.fetchMembers();
        },

        async fetchMembers() {
            this.loading = true;
            try {
                // Mock delay
                await new Promise(resolve => setTimeout(resolve, 600));

                this.members = [
                    { id: 1, name: 'Ana García', email: 'ana.garcia@empresa.com', role: 'Administrador', status: 'active', last_activity: '22 Oct, 14:30', avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDmXEQoR1knRWNT84cvFQHJTdp8tJJ0D5WwwaMABhQYdPTnxG9s3vGruJVbaMeQkTI0Okg_D_1fMU_MMa0u00Zidt8Bcttw_PLOvJLfvw5iyWKPiYm4HTxmMwMOTjUMDUp1qHDidE-9Xi7btov16Ph1ec0AfGRImGldLLdt3QfMryOve3NtHY2LmoThvh1BkcAh_imo3Dmge9D6S82d1_Q5YQDT1mPxp6TwYPqEXEwxOM6BrFkd8waMGK8kG656x9SRcMMucVHa' },
                    { id: 2, name: 'Carlos Ruiz', email: 'carlos.ruiz@empresa.com', role: 'Editor', status: 'active', last_activity: '22 Oct, 09:15', avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuAXgsMyuWAHLWL_hOx41gp7oMEt7s20oK3lFyrPlHaem9JtwhyhQ2ijS7seLQjQ1L74NZyfQlT__X_znRTbAdsOUV_xOwajW-zhSrpWoFsU6qKkvuTeAeScYXcc2S27J7bJzIHdq5BWVtHOjhIQUYg1L8Kn_KUFS721xKlBSK9HjZ2BEjsqpbY87No72ylyvtGEu1HhsdBYIZL6kNPZtwqDnJ4Y1jEcHucbrdzh1_DUhPhtj2q106wdODI4aDQ7ZOZ5Yjiqty_L' },
                    { id: 3, name: 'Marta Jiménez', email: 'marta.j@empresa.com', role: 'Visor', status: 'pending', last_activity: 'Nunca', initials: 'MJ' },
                    { id: 4, name: 'Sofía López', email: 'sofia.lpz@empresa.com', role: 'Visor', status: 'active', last_activity: '21 Oct, 18:00', avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBeo4KQkO1l96Ie-VrX4w8MjfTC4I6jHUld4pjOBOJWWpMWu7c49JNSkVgEjJE392Nwt5jK0pfgxVklbyzowgFCiuL8n333RGZ1gljNaQgG_ANL7Jvme6fgMphsN9KOsu5D1eLSqem-yTIKPb-eiPoka0o0dL2A8Bt30byE-6h3wTXe78BxH02bPDzrt1MavVphDL__AyAaW3yXdhYHhtNgDQ0x3qEKMbzgwBfSJl8QmVPLaMHx3kF1k4q0o6EaucyiRqpbz2Bs' },
                    { id: 5, name: 'David Chen', email: 'david.c@empresa.com', role: 'Editor', status: 'inactive', last_activity: '15 Oct, 11:20', avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA9BMeLMNdRdn_cB5b39KrX4N_B2XHhR0rqZmLGX2Bwhiw5NQKpaPaQecucGwN2mGtz2mktcApfPAx5TxGlApKS3NGVpMOrhLQv_TJYOaiHFan5OvDhiEtcLkobYdBjrByHAyh21jre-A4QPLQQMMVPN08TGb0c0G6xfF17RRVgyk2il_tAZcIyaxpqHRls2OVHzswHdNAJwHCy1zxHErbD9rQGwY7whqy-MG27dl8C1N98Aor_TZIfCfoDIe2GmiBJHZzwqcEA' }
                ];
            } catch (error) {
                console.error('Error fetching members:', error);
                window.showToast?.('Failed to load team members', 'error');
            } finally {
                this.loading = false;
            }
        },

        get filteredMembers() {
            return this.members.filter(m => {
                const matchesSearch = m.name.toLowerCase().includes(this.searchQuery.toLowerCase()) ||
                    m.email.toLowerCase().includes(this.searchQuery.toLowerCase());
                const matchesRole = this.roleFilter === 'all' || m.role.toLowerCase() === this.roleFilter.toLowerCase();
                return matchesSearch && matchesRole;
            });
        },

        inviteMember() {
            this.inviting = true;
            setTimeout(() => {
                window.showToast?.('Invitation email sent successfully', 'success');
                this.inviting = false;
            }, 1000);
        },

        deleteMember(id) {
            if (confirm('Are you sure you want to remove this member from the team?')) {
                this.members = this.members.filter(m => m.id !== id);
                window.showToast?.('Member removed', 'info');
            }
        },

        changeRole(id, newRole) {
            const member = this.members.find(m => m.id === id);
            if (member) {
                member.role = newRole;
                window.showToast?.(`Role updated for ${member.name}`, 'success');
            }
        }
    }));
});
