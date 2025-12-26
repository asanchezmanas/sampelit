/**
 * Simple client-side include system for Vanilla JS dashboard
 * Handles <include src="..."></include> tags
 */

document.addEventListener('DOMContentLoaded', () => {
    processIncludes();
});

async function processIncludes() {
    // Process one batch of includes at a time to avoid live collection issues
    const includes = Array.from(document.getElementsByTagName('include'));
    if (includes.length === 0) return;

    for (const include of includes) {
        const src = include.getAttribute('src');
        if (!src) continue;

        try {
            const response = await fetch(src);
            if (response.ok) {
                const html = await response.text();
                const temp = document.createElement('div');
                temp.innerHTML = html;

                // Move nodes to a fragment to replace the include tag
                const fragment = document.createDocumentFragment();
                const insertedNodes = Array.from(temp.childNodes);
                insertedNodes.forEach(node => fragment.appendChild(node));

                // Replace the include tag
                const parent = include.parentNode;
                if (parent) {
                    include.replaceWith(fragment);

                    // Execute scripts in the newly inserted content
                    insertedNodes.forEach(node => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            executeScriptsInElement(node);
                        }
                    });

                    // Trigger a custom event to notify scripts that an include was loaded
                    document.dispatchEvent(new CustomEvent('include-loaded', { detail: { src } }));
                }
            } else {
                console.error(`Failed to load include: ${src}`, response.status);
                include.innerHTML = `<!-- Error loading ${src} -->`;
            }
        } catch (err) {
            console.error(`Error loading include: ${src}`, err);
        }
    }

    // Check for nested includes after the current batch is finished
    const remaining = document.getElementsByTagName('include');
    if (remaining.length > 0) {
        processIncludes();
    }
}

/**
 * Execute scripts that were inserted via innerHTML
 */
function executeScriptsInElement(element) {
    const scripts = element.tagName === 'SCRIPT' ? [element] : Array.from(element.querySelectorAll('script'));

    scripts.forEach(oldScript => {
        if (oldScript.hasAttribute('data-executed')) return;

        const newScript = document.createElement('script');
        Array.from(oldScript.attributes).forEach(attr => {
            newScript.setAttribute(attr.name, attr.value);
        });
        newScript.textContent = oldScript.textContent;
        oldScript.setAttribute('data-executed', 'true');
        oldScript.replaceWith(newScript);
    });
}
