/**
 * Samplit Visual Editor Client
 * Injected into the proxied iframe to handle element selection and interaction.
 */

(function () {
    console.log('[Samplit] Editor Client Initialized');

    let hoveredElement = null;
    let selectedElement = null;

    // Helper: Generate unique CSS selector
    function getCssSelector(el) {
        if (!(el instanceof Element)) return;

        const path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            let selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break;
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
        }
        return path.join(" > ");
    }

    // 1. Highlight on Hover
    document.addEventListener('mouseover', (e) => {
        if (hoveredElement) {
            hoveredElement.classList.remove('samplit-highlight');
        }
        hoveredElement = e.target;
        hoveredElement.classList.add('samplit-highlight');
        e.stopPropagation();
    }, true);

    // 2. Select on Click
    document.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();

        if (selectedElement) {
            selectedElement.classList.remove('samplit-selected');
        }

        selectedElement = e.target;
        selectedElement.classList.add('samplit-selected');

        // Send to Parent
        const selector = getCssSelector(selectedElement);
        const payload = {
            tagName: selectedElement.tagName,
            id: selectedElement.id,
            className: selectedElement.className,
            innerHTML: selectedElement.innerHTML,
            innerText: selectedElement.innerText,
            selector: selector
        };

        console.log('[Samplit] Selected:', payload);

        // Post Message to Parent Window (visual-editor.html)
        window.parent.postMessage({
            type: 'SAMPLIT_ELEMENT_SELECTED',
            payload: payload
        }, '*');

    }, true);

    // 3. Disable Links and Forms
    document.addEventListener('submit', (e) => e.preventDefault(), true);

})();
