/**
 * Simple client-side include system for Vanilla JS dashboard
 * Handles <include src="..."></include> tags
 */

document.addEventListener('DOMContentLoaded', () => {
    processIncludes();
});

async function processIncludes() {
    const includes = document.getElementsByTagName('include');

    for (let i = 0; i < includes.length; i++) {
        const include = includes[i];
        const src = include.getAttribute('src');

        if (src) {
            try {
                const response = await fetch(src);
                if (response.ok) {
                    const html = await response.text();

                    // Create a temporary container
                    const div = document.createElement('div');
                    div.innerHTML = html;

                    // Replace include tag with content
                    include.replaceWith(...div.childNodes);

                    // Execute any scripts that were inserted
                    executeScriptsInElement(document);

                    // Recursively process new includes
                    processIncludes();
                } else {
                    console.error(`Failed to load include: ${src}`, response.status);
                    include.innerHTML = `<!-- Error loading ${src} -->`;
                }
            } catch (err) {
                console.error(`Error loading include: ${src}`, err);
            }
        }
    }
}

/**
 * Execute scripts that were inserted via innerHTML
 * Scripts inserted via innerHTML don't execute automatically
 */
function executeScriptsInElement(element) {
    const scripts = element.querySelectorAll('script');
    scripts.forEach(oldScript => {
        // Skip already executed scripts (those with src attribute or data-executed)
        if (oldScript.hasAttribute('data-executed')) return;

        const newScript = document.createElement('script');

        // Copy all attributes
        Array.from(oldScript.attributes).forEach(attr => {
            newScript.setAttribute(attr.name, attr.value);
        });

        // Copy the script content
        newScript.textContent = oldScript.textContent;

        // Mark as executed to avoid re-running
        oldScript.setAttribute('data-executed', 'true');

        // Replace old script with new one (this causes execution)
        oldScript.parentNode.replaceChild(newScript, oldScript);
    });
}
