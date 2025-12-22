/**
 * Samplit Visual Editor Injector
 * 
 * This script is injected into the proxied iframe.
 * It handles element highlighting and selection.
 */

(function () {
    console.log('[Samplit] Visual Editor Injector Loaded');

    let hoveredElement = null;
    let selectedElement = null;

    // Helper to generate CSS selector
    function getCssSelector(el) {
        if (!el || el.tagName.toLowerCase() === 'html') return '';

        let path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            let selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break; // IDs are unique
            } else {
                let sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() == selector)
                        nth++;
                }
                if (nth != 1)
                    selector += ":nth-of-type(" + nth + ")";
            }
            path.unshift(selector);
            el = el.parentNode;
            if (el.id === 'samplit-overlay-root') break;
        }
        return path.join(" > ");
    }

    document.addEventListener('mouseover', function (e) {
        // Ignorar scripts y estilos
        if (['HTML', 'BODY', 'SCRIPT', 'STYLE'].includes(e.target.tagName)) return;

        if (hoveredElement && hoveredElement !== e.target) {
            hoveredElement.classList.remove('samplit-highlight');
        }

        hoveredElement = e.target;
        hoveredElement.classList.add('samplit-highlight');
    }, true);

    document.addEventListener('mouseout', function (e) {
        if (hoveredElement) {
            hoveredElement.classList.remove('samplit-highlight');
            hoveredElement = null;
        }
    }, true);

    document.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();

        if (selectedElement) {
            selectedElement.classList.remove('samplit-selected');
        }

        selectedElement = e.target;
        selectedElement.classList.add('samplit-selected');

        const selector = getCssSelector(selectedElement);

        // Send data to parent
        window.parent.postMessage({
            type: 'SAMPLIT_ELEMENT_SELECTED',
            payload: {
                tagName: selectedElement.tagName,
                selector: selector,
                innerHTML: selectedElement.innerHTML,
                innerText: selectedElement.innerText,
                rect: selectedElement.getBoundingClientRect()
            }
        }, '*');

        console.log('[Samplit] Selected:', selector);
        return false;
    }, true);

})();
