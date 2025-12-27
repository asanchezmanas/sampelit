document.addEventListener('alpine:init', () => {
    Alpine.data('helpCenter', () => ({
        searchQuery: '',
        categories: [
            {
                id: 'getting-started',
                title: 'Primeros Pasos',
                description: 'Configura tu cuenta, instala el script y lanza tu primer experimento.',
                icon: 'rocket_launch',
                colorClass: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-500/10 dark:text-indigo-400',
                link: '#'
            },
            {
                id: 'integrations',
                title: 'Integraciones',
                description: 'Conecta Sampelit con Shopify, WordPress, Segment y más.',
                icon: 'hub',
                colorClass: 'text-purple-500 bg-purple-50 dark:bg-purple-500/10 dark:text-purple-400',
                link: '#'
            },
            {
                id: 'analytics',
                title: 'Análisis de Datos',
                description: 'Guías sobre significancia estadística y reportes de conversión.',
                icon: 'analytics',
                colorClass: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 dark:text-emerald-400',
                link: '#'
            },
            {
                id: 'billing',
                title: 'Facturación',
                description: 'Gestiona tu plan, métodos de pago e historial.',
                icon: 'receipt_long',
                colorClass: 'text-amber-500 bg-amber-50 dark:bg-amber-500/10 dark:text-amber-400',
                link: 'billing_v2.html'
            },
            {
                id: 'troubleshooting',
                title: 'Solución de Problemas',
                description: 'Respuestas a errores comunes y debugging.',
                icon: 'build',
                colorClass: 'text-rose-500 bg-rose-50 dark:bg-rose-500/10 dark:text-rose-400',
                link: '#'
            },
            {
                id: 'api',
                title: 'API & Developers',
                description: 'Documentación técnica para implementaciones avanzadas.',
                icon: 'api',
                colorClass: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-500/10 dark:text-cyan-400',
                link: '#'
            }
        ],
        articles: [
            { title: 'Cómo interpretar los resultados de confianza (Confidence LeveL)', category: 'analytics' },
            { title: 'Guía de instalación para Single Page Applications (SPA)', category: 'getting-started' },
            { title: 'Diferencia entre test A/B y test Multivariante', category: 'getting-started' },
            { title: 'Configurar objetivos de conversión personalizados', category: 'analytics' },
            { title: 'Resolviendo problemas de parpadeo (FOOC)', category: 'troubleshooting' },
            { title: 'Exportar datos a CSV/PDF', category: 'analytics' }
        ],

        get filteredCategories() {
            if (!this.searchQuery) return this.categories;
            const lowerQuery = this.searchQuery.toLowerCase();
            return this.categories.filter(cat =>
                cat.title.toLowerCase().includes(lowerQuery) ||
                cat.description.toLowerCase().includes(lowerQuery)
            );
        },

        get filteredArticles() {
            if (!this.searchQuery) return this.articles.slice(0, 4); // Show top 4 by default
            const lowerQuery = this.searchQuery.toLowerCase();
            return this.articles.filter(article =>
                article.title.toLowerCase().includes(lowerQuery)
            );
        },

        isSearchActive() {
            return this.searchQuery.length > 0;
        }
    }));
});
