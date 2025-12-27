/**
 * Experiment Creation Wizard Controller
 * Handles the multi-step form and submission via ExperimentService (through Store).
 */

document.addEventListener('alpine:init', () => {
    Alpine.data('experimentWizard', () => ({
        step: 1,
        sidebarToggle: false,
        darkMode: false,
        isSubmitting: false,

        // Form Data
        experiment: {
            name: '',
            url: 'https://',
            metric: 'Conversion Rate',
            hypothesis: '',
            traffic: 100,
            variants: [
                { name: 'Control', type: 'baseline', traffic: 50 },
                { name: 'Variant A', type: 'variant', traffic: 50 }
            ]
        },

        init() {
            console.log('Wizard Initialized');
            // Init dark mode from store or local storage if store not ready (fallback)
            this.darkMode = JSON.parse(localStorage.getItem('darkMode')) || false;
            this.$watch('darkMode', value => localStorage.setItem('darkMode', JSON.stringify(value)));
        },

        async launchExperiment() {
            if (this.isSubmitting) return; // Prevent double submit
            this.isSubmitting = true;

            try {
                // 1. Prepare Payload
                const payload = {
                    name: this.experiment.name || 'Untitled Experiment',
                    description: this.experiment.hypothesis,
                    url: this.experiment.url,
                    traffic_allocation: this.experiment.traffic / 100,
                    status: 'draft', // Default to draft, user can start later
                    // Construct elements structure expected by backend
                    elements: [{
                        name: "Main Content",
                        selector: { type: "css", selector: "body" },
                        element_type: "generic",
                        original_content: { text: "Original" },
                        variants: this.experiment.variants.slice(1).map(v => ({
                            text: v.name,
                            weight: v.traffic / 100
                        }))
                    }]
                };

                // 2. Call Store Action
                // This delegates to ExperimentService.create and updates local list
                await Alpine.store('experiments').create(payload);

                // 3. Success Handling
                // Toast is already fired by the Store

                // Redirect after short delay to let user see success
                setTimeout(() => {
                    window.location.href = 'experiments_v2.html';
                }, 1000);

            } catch (error) {
                console.error('Wizard Submit Error:', error);

                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Failed to create experiment. Check console.', type: 'error' }
                }));
            } finally {
                this.isSubmitting = false;
            }
        },

        // Navigation Helpers
        nextStep() { if (this.step < 4) this.step++; },
        prevStep() { if (this.step > 1) this.step--; },
        goToStep(s) { this.step = s; }
    }));
});
