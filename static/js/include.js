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
