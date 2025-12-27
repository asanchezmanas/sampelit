// static/js/components/visual-editor.js

/**
 * Visual Editor - Component for DOM element selection
 * 
 * Permite a los usuarios:
 * - Cargar su página en iframe
 * - Seleccionar elementos haciendo click
 * - Generar selectores CSS automáticamente
 * - Configurar variantes sin código
 * 
 * CRÍTICO: Maneja CORS, genera selectores únicos, detecta tipos
 */
class VisualEditor {
    constructor(options = {}) {
        this.options = {
            iframeSelector: '#preview-iframe',
            containerSelector: '#iframe-container',
            onElementSelected: null,
            onError: null,
            ...options
        };

        // State
        this.state = {
            pageUrl: null,
            iframe: null,
            iframeDoc: null,
            selectedElements: new Map(), // id -> elementData
            currentElement: null,
            isReady: false,
            corsError: false,
            viewportMode: 'desktop' // SOTA: 'desktop' | 'tablet' | 'mobile'
        };

        // SOTA: Undo/Redo Stack
        this.history = {
            undoStack: [], // Array of { action, elementId, before, after }
            redoStack: [],
            maxSize: 50
        };

        // Tracking
        this.highlightedElement = null;
        this.overlays = new Map();

        this.init();
    }

    // ===== INITIALIZATION =====

    init() {
        this.iframe = document.querySelector(this.options.iframeSelector);
        this.container = document.querySelector(this.options.containerSelector);

        if (!this.iframe || !this.container) {
            console.error('[VisualEditor] Required elements not found');
            return;
        }

        this.setupIframeListeners();
        this.setupKeyboardShortcuts(); // SOTA: Ctrl+Z/Y, 1/2/3 viewports
    }

    setupIframeListeners() {
        this.iframe.addEventListener('load', () => {
            this.handleIframeLoad();
        });

        this.iframe.addEventListener('error', () => {
            this.handleIframeError();
        });
    }

    // ===== LOAD PAGE =====

    async loadPage(url) {
        try {
            // Validate URL
            new URL(url);

            this.state.pageUrl = url;
            this.state.isReady = false;
            this.state.corsError = false;

            // Show loading
            this.showLoading(true);

            // Load in iframe
            this.iframe.src = url;

        } catch (error) {
            this.handleError('Invalid URL', error);
        }
    }

    handleIframeLoad() {
        try {
            // Try to access iframe content
            this.state.iframeDoc = this.iframe.contentDocument || this.iframe.contentWindow.document;

            // Test if we can access it (CORS check)
            const test = this.state.iframeDoc.body;

            if (!test) {
                throw new Error('Cannot access iframe content');
            }

            // Success! Initialize interactions
            this.initializeIframeInteractions();
            this.state.isReady = true;
            this.showLoading(false);

            this.emit('pageLoaded', { url: this.state.pageUrl });

        } catch (error) {
            this.handleCORSError();
        }
    }

    handleIframeError() {
        this.handleError('Failed to load page', new Error('Network error or page not found'));
    }

    handleCORSError() {
        this.state.corsError = true;
        this.showLoading(false);

        this.handleError(
            'CORS Error: Cannot interact with this page',
            new Error('The page blocks cross-origin access. Try using the Proxy method or manual snippet.')
        );
    }

    // ===== IFRAME INTERACTIONS =====

    initializeIframeInteractions() {
        const doc = this.state.iframeDoc;

        // Prevent default behaviors
        doc.addEventListener('click', this.handleClick.bind(this), true);
        doc.addEventListener('mouseover', this.handleMouseOver.bind(this), true);
        doc.addEventListener('mouseout', this.handleMouseOut.bind(this), true);

        // Prevent links and forms
        this.preventDefaultBehaviors(doc);

        // Inject custom styles for highlighting
        this.injectCustomStyles(doc);

        console.log('[VisualEditor] Iframe interactions initialized');
    }

    preventDefaultBehaviors(doc) {
        // Prevent all links from navigating
        doc.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link) {
                e.preventDefault();
                e.stopPropagation();
            }
        }, true);

        // Prevent form submissions
        doc.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, true);
    }

    injectCustomStyles(doc) {
        const style = doc.createElement('style');
        style.textContent = `
            .mab-highlight {
                outline: 2px dashed #465fff !important;
                outline-offset: 2px !important;
                cursor: pointer !important;
                position: relative !important;
            }
            
            .mab-selected {
                outline: 2px solid #12b76a !important;
                outline-offset: 2px !important;
                background-color: rgba(18, 183, 106, 0.1) !important;
            }
            
            .mab-label {
                position: absolute !important;
                top: -24px !important;
                left: 0 !important;
                background: #465fff !important;
                color: white !important;
                padding: 2px 8px !important;
                border-radius: 4px !important;
                font-size: 11px !important;
                font-weight: 600 !important;
                z-index: 999999 !important;
                pointer-events: none !important;
            }
        `;

        doc.head.appendChild(style);
    }

    // ===== EVENT HANDLERS =====

    handleClick(e) {
        e.preventDefault();
        e.stopPropagation();

        const element = e.target;

        // Ignore if already selected
        if (element.classList.contains('mab-selected')) {
            return;
        }

        this.selectElement(element);
    }

    handleMouseOver(e) {
        const element = e.target;

        // Don't highlight if already selected
        if (element.classList.contains('mab-selected')) {
            return;
        }

        // Remove previous highlight
        if (this.highlightedElement && this.highlightedElement !== element) {
            this.highlightedElement.classList.remove('mab-highlight');
        }

        // Add new highlight
        element.classList.add('mab-highlight');
        this.highlightedElement = element;
    }

    handleMouseOut(e) {
        const element = e.target;
        element.classList.remove('mab-highlight');
    }

    // ===== ELEMENT SELECTION =====

    selectElement(element) {
        const elementData = this.analyzeElement(element);

        // Mark as selected in DOM
        element.classList.add('mab-selected');
        element.classList.remove('mab-highlight');

        // Add label
        this.addElementLabel(element, elementData.name);

        // Store
        this.state.selectedElements.set(elementData.id, {
            ...elementData,
            domElement: element
        });

        // Open configuration modal
        this.state.currentElement = elementData.id;
        this.emit('elementSelected', elementData);

        console.log('[VisualEditor] Element selected:', elementData);
    }

    analyzeElement(element) {
        const id = this.generateElementId();

        return {
            id: id,
            name: this.generateElementName(element),
            selector: this.generateSelector(element),
            elementType: this.detectElementType(element),
            originalContent: this.extractContent(element),
            xpath: this.generateXPath(element),
            tagName: element.tagName.toLowerCase(),
            classes: Array.from(element.classList),
            attributes: this.getRelevantAttributes(element)
        };
    }

    // ===== SELECTOR GENERATION =====

    generateSelector(element) {
        // Strategy: Try methods in order of specificity

        // 1. ID (most specific)
        if (element.id && this.isUniqueSelector(`#${element.id}`)) {
            return {
                type: 'id',
                selector: `#${element.id}`,
                confidence: 'high'
            };
        }

        // 2. Unique data attribute
        const dataAttrs = this.getDataAttributes(element);
        for (const [key, value] of Object.entries(dataAttrs)) {
            const selector = `[${key}="${value}"]`;
            if (this.isUniqueSelector(selector)) {
                return {
                    type: 'data-attribute',
                    selector: selector,
                    confidence: 'high'
                };
            }
        }

        // 3. Unique class combination
        if (element.classList.length > 0) {
            const classSelector = '.' + Array.from(element.classList).join('.');
            if (this.isUniqueSelector(classSelector)) {
                return {
                    type: 'class',
                    selector: classSelector,
                    confidence: 'medium'
                };
            }
        }

        // 4. nth-child with parent context
        const nthSelector = this.generateNthChildSelector(element);
        if (nthSelector && this.isUniqueSelector(nthSelector)) {
            return {
                type: 'nth-child',
                selector: nthSelector,
                confidence: 'medium'
            };
        }

        // 5. Full path (last resort)
        return {
            type: 'path',
            selector: this.generatePathSelector(element),
            confidence: 'low'
        };
    }

    generateNthChildSelector(element) {
        const parent = element.parentElement;
        if (!parent) return null;

        const siblings = Array.from(parent.children);
        const index = siblings.indexOf(element) + 1;

        const parentSelector = parent.id
            ? `#${parent.id}`
            : parent.className
                ? `.${Array.from(parent.classList)[0]}`
                : parent.tagName.toLowerCase();

        return `${parentSelector} > ${element.tagName.toLowerCase()}:nth-child(${index})`;
    }

    generatePathSelector(element) {
        const path = [];
        let current = element;

        while (current && current.nodeType === Node.ELEMENT_NODE) {
            let selector = current.tagName.toLowerCase();

            if (current.id) {
                selector += `#${current.id}`;
                path.unshift(selector);
                break; // ID is unique, stop here
            }

            if (current.className) {
                const firstClass = Array.from(current.classList)[0];
                if (firstClass) {
                    selector += `.${firstClass}`;
                }
            }

            // Add nth-of-type if needed for specificity
            const parent = current.parentElement;
            if (parent) {
                const siblings = Array.from(parent.children).filter(
                    el => el.tagName === current.tagName
                );

                if (siblings.length > 1) {
                    const index = siblings.indexOf(current) + 1;
                    selector += `:nth-of-type(${index})`;
                }
            }

            path.unshift(selector);
            current = parent;

            // Limit depth
            if (path.length > 5) break;
        }

        return path.join(' > ');
    }

    isUniqueSelector(selector) {
        try {
            const matches = this.state.iframeDoc.querySelectorAll(selector);
            return matches.length === 1;
        } catch (error) {
            return false;
        }
    }

    // ===== XPATH GENERATION =====

    generateXPath(element) {
        if (element.id) {
            return `//*[@id="${element.id}"]`;
        }

        const paths = [];
        let current = element;

        while (current && current.nodeType === Node.ELEMENT_NODE) {
            let index = 0;
            let sibling = current.previousSibling;

            while (sibling) {
                if (sibling.nodeType === Node.ELEMENT_NODE &&
                    sibling.tagName === current.tagName) {
                    index++;
                }
                sibling = sibling.previousSibling;
            }

            const tagName = current.tagName.toLowerCase();
            const pathIndex = index > 0 ? `[${index + 1}]` : '';
            paths.unshift(tagName + pathIndex);

            current = current.parentElement;
        }

        return '/' + paths.join('/');
    }

    // ===== ELEMENT TYPE DETECTION =====

    detectElementType(element) {
        const tag = element.tagName.toLowerCase();

        // Button
        if (tag === 'button' ||
            (tag === 'a' && element.textContent.trim()) ||
            element.getAttribute('role') === 'button') {
            return 'button';
        }

        // Headline
        if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tag)) {
            return 'headline';
        }

        // Image
        if (tag === 'img') {
            return 'image';
        }

        // Link
        if (tag === 'a') {
            return 'link';
        }

        // Form input
        if (['input', 'textarea', 'select'].includes(tag)) {
            return 'form-input';
        }

        // Video
        if (tag === 'video' || tag === 'iframe') {
            return 'media';
        }

        // Section/Container
        if (['div', 'section', 'article', 'aside', 'main'].includes(tag)) {
            // Check if it's a meaningful container
            if (element.children.length > 3) {
                return 'section';
            }
        }

        // Default: text
        return 'text';
    }

    // ===== CONTENT EXTRACTION =====

    extractContent(element) {
        const type = this.detectElementType(element);

        const content = {
            type: type,
            text: element.textContent?.trim() || '',
            html: element.innerHTML
        };

        // Type-specific extraction
        switch (type) {
            case 'image':
                content.src = element.src;
                content.alt = element.alt;
                content.width = element.width;
                content.height = element.height;
                break;

            case 'link':
            case 'button':
                content.href = element.href;
                content.text = element.textContent.trim();
                break;

            case 'form-input':
                content.value = element.value;
                content.placeholder = element.placeholder;
                content.inputType = element.type;
                break;

            case 'headline':
                content.level = element.tagName.toLowerCase();
                break;
        }

        // Computed styles
        if (this.iframe.contentWindow) {
            const styles = this.iframe.contentWindow.getComputedStyle(element);
            content.styles = {
                color: styles.color,
                backgroundColor: styles.backgroundColor,
                fontSize: styles.fontSize,
                fontWeight: styles.fontWeight,
                fontFamily: styles.fontFamily
            };
        }

        return content;
    }

    // ===== ELEMENT MANAGEMENT =====

    deselectElement(elementId) {
        const elementData = this.state.selectedElements.get(elementId);
        if (!elementData) return;

        const domElement = elementData.domElement;
        if (domElement) {
            domElement.classList.remove('mab-selected');

            // Remove label
            const label = domElement.querySelector('.mab-label');
            if (label) {
                label.remove();
            }
        }

        this.state.selectedElements.delete(elementId);
        this.emit('elementDeselected', { elementId });
    }

    clearAllSelections() {
        this.state.selectedElements.forEach((data, id) => {
            this.deselectElement(id);
        });
    }

    addElementLabel(element, text) {
        // Remove existing label
        const existingLabel = element.querySelector('.mab-label');
        if (existingLabel) {
            existingLabel.remove();
        }

        const label = this.state.iframeDoc.createElement('div');
        label.className = 'mab-label';
        label.textContent = text;

        element.style.position = 'relative';
        element.appendChild(label);
    }

    // ===== PREVIEW VARIANTS =====

    previewVariant(elementId, variantContent) {
        const elementData = this.state.selectedElements.get(elementId);
        if (!elementData) return;

        const domElement = elementData.domElement;
        if (!domElement) return;

        const type = elementData.elementType;

        // Store original if not already stored
        if (!elementData.originalSnapshot) {
            elementData.originalSnapshot = {
                html: domElement.innerHTML,
                src: domElement.src,
                href: domElement.href,
                text: domElement.textContent
            };
        }

        // Apply variant
        switch (type) {
            case 'text':
            case 'headline':
            case 'button':
                if (variantContent.text) {
                    domElement.textContent = variantContent.text;
                }
                break;

            case 'image':
                if (variantContent.src) {
                    domElement.src = variantContent.src;
                }
                if (variantContent.alt) {
                    domElement.alt = variantContent.alt;
                }
                break;

            case 'link':
                if (variantContent.text) {
                    domElement.textContent = variantContent.text;
                }
                if (variantContent.href) {
                    domElement.href = variantContent.href;
                }
                break;
        }

        // Apply style changes if provided
        if (variantContent.styles) {
            Object.entries(variantContent.styles).forEach(([prop, value]) => {
                domElement.style[prop] = value;
            });
        }
    }

    restoreOriginal(elementId) {
        const elementData = this.state.selectedElements.get(elementId);
        if (!elementData || !elementData.originalSnapshot) return;

        const domElement = elementData.domElement;
        const snapshot = elementData.originalSnapshot;

        // Restore
        if (snapshot.html !== undefined) {
            domElement.innerHTML = snapshot.html;
        }
        if (snapshot.src !== undefined) {
            domElement.src = snapshot.src;
        }
        if (snapshot.href !== undefined) {
            domElement.href = snapshot.href;
        }

        // Clear inline styles
        domElement.style.cssText = '';
    }

    // ===== EXPORT DATA =====

    exportConfiguration() {
        const elements = [];

        this.state.selectedElements.forEach((data, id) => {
            elements.push({
                id: data.id,
                name: data.name,
                selector: data.selector,
                element_type: data.elementType,
                original_content: data.originalContent,
                xpath: data.xpath
            });
        });

        return {
            page_url: this.state.pageUrl,
            elements: elements,
            created_at: new Date().toISOString()
        };
    }

    // ===== UTILITIES =====

    getDataAttributes(element) {
        const dataAttrs = {};

        Array.from(element.attributes).forEach(attr => {
            if (attr.name.startsWith('data-')) {
                dataAttrs[attr.name] = attr.value;
            }
        });

        return dataAttrs;
    }

    getRelevantAttributes(element) {
        const relevant = ['id', 'class', 'name', 'type', 'role', 'aria-label'];
        const attrs = {};

        relevant.forEach(attr => {
            const value = element.getAttribute(attr);
            if (value) {
                attrs[attr] = value;
            }
        });

        return attrs;
    }

    generateElementId() {
        return 'el_' + Math.random().toString(36).substr(2, 9);
    }

    generateElementName(element) {
        // Try to generate a meaningful name
        const id = element.id;
        const text = element.textContent?.trim().substring(0, 30);
        const tag = element.tagName.toLowerCase();

        if (id) return id;
        if (text && text.length > 0) return text;

        return `${tag}_${Date.now()}`;
    }

    showLoading(show) {
        const container = this.container;
        const loading = document.getElementById('iframe-loading');

        if (show) {
            if (loading) loading.style.display = 'flex';
            container.style.display = 'none';
        } else {
            if (loading) loading.style.display = 'none';
            container.style.display = 'block';
        }
    }

    // ===== ERROR HANDLING =====

    handleError(message, error) {
        console.error('[VisualEditor]', message, error);

        if (this.options.onError) {
            this.options.onError({ message, error });
        }

        this.emit('error', { message, error });
    }

    // ===== EVENT EMITTER =====

    emit(event, data) {
        const callback = this.options[`on${event.charAt(0).toUpperCase() + event.slice(1)}`];
        if (callback) {
            callback(data);
        }

        // Also emit to global event bus if available
        if (window.MAB?.eventBus) {
            window.MAB.eventBus.emit(`visualEditor:${event}`, data);
        }
    }

    // ===== PUBLIC API =====

    getSelectedElements() {
        return Array.from(this.state.selectedElements.values());
    }

    getElement(elementId) {
        return this.state.selectedElements.get(elementId);
    }

    isReady() {
        return this.state.isReady;
    }

    hasCORSError() {
        return this.state.corsError;
    }

    getPageUrl() {
        return this.state.pageUrl;
    }

    // ===== SOTA: UNDO/REDO =====

    pushToHistory(action, elementId, before, after) {
        // Clear redo stack on new action
        this.history.redoStack = [];

        this.history.undoStack.push({ action, elementId, before, after, timestamp: Date.now() });

        // Limit size
        if (this.history.undoStack.length > this.history.maxSize) {
            this.history.undoStack.shift();
        }

        this.emit('historyChanged', { canUndo: this.canUndo(), canRedo: this.canRedo() });
    }

    undo() {
        if (!this.canUndo()) return false;

        const item = this.history.undoStack.pop();
        this.history.redoStack.push(item);

        // Restore previous state
        this.applyHistoryState(item.elementId, item.before);

        this.emit('undo', item);
        this.emit('historyChanged', { canUndo: this.canUndo(), canRedo: this.canRedo() });

        window.dispatchEvent(new CustomEvent('toast:show', {
            detail: { message: 'Undo: ' + item.action, type: 'info' }
        }));

        return true;
    }

    redo() {
        if (!this.canRedo()) return false;

        const item = this.history.redoStack.pop();
        this.history.undoStack.push(item);

        // Apply the change again
        this.applyHistoryState(item.elementId, item.after);

        this.emit('redo', item);
        this.emit('historyChanged', { canUndo: this.canUndo(), canRedo: this.canRedo() });

        window.dispatchEvent(new CustomEvent('toast:show', {
            detail: { message: 'Redo: ' + item.action, type: 'info' }
        }));

        return true;
    }

    applyHistoryState(elementId, state) {
        const elementData = this.state.selectedElements.get(elementId);
        if (!elementData || !elementData.domElement) return;

        const el = elementData.domElement;

        if (state.html !== undefined) el.innerHTML = state.html;
        if (state.text !== undefined) el.textContent = state.text;
        if (state.src !== undefined) el.src = state.src;
        if (state.styles) {
            Object.entries(state.styles).forEach(([k, v]) => el.style[k] = v);
        }
    }

    canUndo() { return this.history.undoStack.length > 0; }
    canRedo() { return this.history.redoStack.length > 0; }

    // ===== SOTA: RESPONSIVE PREVIEW =====

    setViewportMode(mode) {
        const modes = {
            desktop: { width: '100%', label: 'Desktop' },
            tablet: { width: '768px', label: 'Tablet' },
            mobile: { width: '375px', label: 'Mobile' }
        };

        if (!modes[mode]) return;

        this.state.viewportMode = mode;

        if (this.iframe) {
            this.iframe.style.width = modes[mode].width;
            this.iframe.style.margin = mode === 'desktop' ? '0' : '0 auto';
            this.iframe.style.transition = 'width 0.3s ease';
        }

        this.emit('viewportChanged', { mode, ...modes[mode] });

        window.dispatchEvent(new CustomEvent('toast:show', {
            detail: { message: `Preview: ${modes[mode].label}`, type: 'info' }
        }));
    }

    getViewportMode() { return this.state.viewportMode; }

    // ===== SOTA: KEYBOARD SHORTCUTS =====

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only when editor is active
            if (!this.state.isReady) return;

            // Ctrl/Cmd + Z = Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.undo();
            }

            // Ctrl/Cmd + Shift + Z = Redo (or Ctrl + Y)
            if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
                e.preventDefault();
                this.redo();
            }

            // Escape = Deselect current
            if (e.key === 'Escape' && this.state.currentElement) {
                this.deselectElement(this.state.currentElement);
                this.state.currentElement = null;
            }

            // 1, 2, 3 = Viewport modes
            if (e.key === '1' && !e.ctrlKey && !e.metaKey) this.setViewportMode('desktop');
            if (e.key === '2' && !e.ctrlKey && !e.metaKey) this.setViewportMode('tablet');
            if (e.key === '3' && !e.ctrlKey && !e.metaKey) this.setViewportMode('mobile');
        });

        console.log('[VisualEditor] Keyboard shortcuts enabled');
    }

    // ===== CLEANUP =====

    destroy() {
        this.clearAllSelections();

        if (this.iframe) {
            this.iframe.src = 'about:blank';
        }

        this.state.selectedElements.clear();
        this.overlays.clear();
    }
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VisualEditor;
} else {
    window.VisualEditor = VisualEditor;
}
