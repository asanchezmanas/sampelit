/**
 * Sampelit Theme Manager
 * Handles dark/light mode toggle with localStorage persistence
 */

(function () {
    // Check for saved theme or system preference
    function getInitialTheme() {
        const saved = localStorage.getItem('theme');
        if (saved) return saved;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    // Apply theme to document
    function applyTheme(theme) {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }

    // Toggle theme
    function toggleTheme() {
        const isDark = document.documentElement.classList.contains('dark');
        const newTheme = isDark ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    }

    // Initialize on page load
    applyTheme(getInitialTheme());

    // Setup toggle buttons after DOM is ready
    function setupToggles() {
        const toggles = document.querySelectorAll('#theme-toggle, [data-theme-toggle]');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', toggleTheme);
        });
    }

    // Run setup when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupToggles);
    } else {
        setupToggles();
    }

    // Also setup after includes are processed (for pages using include.js)
    const observer = new MutationObserver(() => {
        setupToggles();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Expose for external use
    window.SampelitTheme = {
        toggle: toggleTheme,
        get: getInitialTheme,
        set: function (theme) {
            localStorage.setItem('theme', theme);
            applyTheme(theme);
        }
    };
})();
