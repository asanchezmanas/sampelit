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
            // Init dark mode
            this.darkMode = JSON.parse(localStorage.getItem('darkMode')) || false;
            this.$watch('darkMode', value => localStorage.setItem('darkMode', JSON.stringify(value)));

            // SOTA: Auto-Recovery of Draft
            const savedDraft = localStorage.getItem('wizard_draft');
            if (savedDraft) {
                try {
                    const draft = JSON.parse(savedDraft);
                    // Merge draft into experiment object safely
                    this.experiment = { ...this.experiment, ...draft };
                    // SOTA: Restore step position
                    if (draft._step) {
                        this.step = draft._step;
                    }
                    console.log('Draft restored from local storage');

                    window.dispatchEvent(new CustomEvent('toast:show', {
                        detail: { message: 'Draft restored from your last session', type: 'info' }
                    }));
                } catch (e) {
                    console.error('Failed to restore draft', e);
                }
            }

            // SOTA: Auto-Save on change
            this.$watch('experiment', (value) => {
                localStorage.setItem('wizard_draft', JSON.stringify(value));
                // Flash "Saved" badge
                this.showSavedBadge = true;
                setTimeout(() => { this.showSavedBadge = false; }, 1500);
            });
        },

        // SOTA: Auto-Save Indicator
        showSavedBadge: false,

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
                // SOTA: Clear draft on success
                localStorage.removeItem('wizard_draft');

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

        // SOTA: Inline Validation State
        errors: {},
        touched: {},

        // SOTA: Validate field on blur
        validateField(field) {
            this.touched[field] = true;
            this.errors[field] = null;

            switch (field) {
                case 'name':
                    if (!this.experiment.name || this.experiment.name.length < 3) {
                        this.errors[field] = 'Name must be at least 3 characters';
                    }
                    break;
                case 'url':
                    try {
                        new URL(this.experiment.url);
                        if (!this.experiment.url.startsWith('http')) {
                            this.errors[field] = 'URL must start with http:// or https://';
                        }
                    } catch {
                        this.errors[field] = 'Invalid URL format';
                    }
                    break;
                case 'hypothesis':
                    if (!this.experiment.hypothesis || this.experiment.hypothesis.length < 10) {
                        this.errors[field] = 'Hypothesis should be at least 10 characters';
                    }
                    break;
            }

            return !this.errors[field];
        },

        hasError(field) {
            return this.touched[field] && this.errors[field];
        },

        getError(field) {
            return this.errors[field];
        },

        // SOTA: Validate current step before proceeding
        canProceed() {
            switch (this.step) {
                case 1:
                    return this.validateField('name') && this.validateField('url');
                case 2:
                    return this.validateField('hypothesis');
                default:
                    return true;
            }
        },

        // Navigation Helpers with validation
        nextStep() {
            if (this.step < 4 && this.canProceed()) {
                this.step++;
                this.saveStepToStorage();
            } else if (!this.canProceed()) {
                window.dispatchEvent(new CustomEvent('toast:show', {
                    detail: { message: 'Please fix validation errors before continuing', type: 'error' }
                }));
            }
        },
        prevStep() {
            if (this.step > 1) {
                this.step--;
                this.saveStepToStorage();
            }
        },
        goToStep(s) {
            this.step = s;
            this.saveStepToStorage();
        },

        // SOTA: Persist step to localStorage
        saveStepToStorage() {
            const draft = JSON.parse(localStorage.getItem('wizard_draft') || '{}');
            draft._step = this.step;
            localStorage.setItem('wizard_draft', JSON.stringify(draft));
        },

        // SOTA: URL Site Preview
        sitePreviewLoading: false,
        sitePreviewError: null,

        async loadSitePreview() {
            if (!this.experiment.url || this.experiment.url === 'https://') return;

            try {
                new URL(this.experiment.url);
                this.sitePreviewLoading = true;
                this.sitePreviewError = null;

                // The actual iframe will handle loading
                // This just sets the state for UI feedback
                setTimeout(() => {
                    this.sitePreviewLoading = false;
                }, 2000);
            } catch {
                this.sitePreviewError = 'Invalid URL';
            }
        }
    }));
});
