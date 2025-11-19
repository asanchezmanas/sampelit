// static/js/core/performance.js

// ===== SCRIPT LOADER OPTIMIZADO =====

class ScriptLoader {
    constructor() {
        this.loadedScripts = new Set();
        this.loadingPromises = new Map();
        this.criticalScripts = [
            '/static/js/core/utils.js',
            '/static/js/core/state.js',
            '/static/js/core/api.js'
        ];
    }

    async loadScript(src, options = {}) {
        const {
            critical = false,
            cache = true,
            timeout = 10000,
            retry = 2
        } = options;

        // Return if already loaded
        if (this.loadedScripts.has(src)) {
            return Promise.resolve();
        }

        // Return existing promise if currently loading
        if (this.loadingPromises.has(src)) {
            return this.loadingPromises.get(src);
        }

        const loadPromise = this.createLoadPromise(src, critical, timeout, retry);
        this.loadingPromises.set(src, loadPromise);

        try {
            await loadPromise;
            this.loadedScripts.add(src);
            if (cache) {
                this.cacheScript(src);
            }
        } catch (error) {
            console.error(`Failed to load script ${src}:`, error);
            throw error;
        } finally {
            this.loadingPromises.delete(src);
        }
    }

    createLoadPromise(src, critical, timeout, retryCount) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = !critical;
            script.defer = !critical;

            let timeoutId;
            let attempts = 0;

            const attemptLoad = () => {
                attempts++;
                
                const onLoad = () => {
                    clearTimeout(timeoutId);
                    cleanup();
                    resolve();
                };

                const onError = () => {
                    clearTimeout(timeoutId);
                    cleanup();
                    
                    if (attempts <= retryCount) {
                        console.warn(`Retrying script load: ${src} (attempt ${attempts})`);
                        setTimeout(attemptLoad, 1000 * attempts);
                    } else {
                        reject(new Error(`Failed to load script after ${attempts} attempts: ${src}`));
                    }
                };

                const cleanup = () => {
                    script.removeEventListener('load', onLoad);
                    script.removeEventListener('error', onError);
                };

                script.addEventListener('load', onLoad);
                script.addEventListener('error', onError);

                if (timeout > 0) {
                    timeoutId = setTimeout(() => {
                        cleanup();
                        onError();
                    }, timeout);
                }

                document.head.appendChild(script);
            };

            attemptLoad();
        });
    }

    cacheScript(src) {
        // Use Service Worker or Cache API if available
        if ('caches' in window) {
            caches.open('mab-scripts-v1').then(cache => {
                cache.add(src).catch(err => {
                    console.warn('Failed to cache script:', src, err);
                });
            });
        }
    }

    async preloadCriticalScripts() {
        const preloadPromises = this.criticalScripts.map(src => 
            this.loadScript(src, { critical: true })
        );

        try {
            await Promise.all(preloadPromises);
            console.log('Critical scripts loaded successfully');
        } catch (error) {
            console.error('Failed to load critical scripts:', error);
            throw error;
        }
    }

    loadNonCriticalScripts() {
        // Load non-critical scripts when idle
        const defer = window.requestIdleCallback || (cb => setTimeout(cb, 16));
        
        defer(() => {
            const nonCriticalScripts = [
                '/static/js/components/charts.js',
                '/static/js/components/tables.js'
            ];

            nonCriticalScripts.forEach(src => {
                this.loadScript(src, { critical: false }).catch(err => {
                    console.warn(`Non-critical script failed to load: ${src}`, err);
                });
            });
        });
    }
}

// ===== RESOURCE MANAGER =====

class ResourceManager {
    constructor() {
        this.imageCache = new Map();
        this.observer = null;
        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                this.handleIntersection.bind(this),
                {
                    rootMargin: '50px 0px',
                    threshold: 0.01
                }
            );
        }
    }

    handleIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                this.loadImage(img);
                this.observer.unobserve(img);
            }
        });
    }

    lazyLoadImages() {
        const images = document.querySelectorAll('img[data-src]');
        
        if (this.observer) {
            images.forEach(img => this.observer.observe(img));
        } else {
            // Fallback for browsers without Intersection Observer
            images.forEach(img => this.loadImage(img));
        }
    }

    async loadImage(img) {
        const src = img.dataset.src;
        if (!src) return;

        try {
            // Check cache first
            if (this.imageCache.has(src)) {
                img.src = this.imageCache.get(src);
                img.classList.add('loaded');
                return;
            }

            // Load image
            const imagePromise = new Promise((resolve, reject) => {
                const tempImg = new Image();
                tempImg.onload = () => resolve(tempImg);
                tempImg.onerror = reject;
                tempImg.src = src;
            });

            const loadedImg = await imagePromise;
            
            // Cache and apply
            this.imageCache.set(src, src);
            img.src = src;
            img.classList.add('loaded');
            
            // Add fade-in effect
            img.style.opacity = '0';
            img.style.transition = 'opacity 0.3s ease';
            
            requestAnimationFrame(() => {
                img.style.opacity = '1';
            });

        } catch (error) {
            console.warn(`Failed to load image: ${src}`, error);
            img.classList.add('error');
        }
    }

    preloadImages(urls) {
        return Promise.all(
            urls.map(url => {
                if (this.imageCache.has(url)) {
                    return Promise.resolve();
                }

                return new Promise((resolve, reject) => {
                    const img = new Image();
                    img.onload = () => {
                        this.imageCache.set(url, url);
                        resolve();
                    };
                    img.onerror = reject;
                    img.src = url;
                });
            })
        );
    }

    cleanup() {
        if (this.observer) {
            this.observer.disconnect();
        }
        this.imageCache.clear();
    }
}

// ===== VIRTUAL SCROLLING =====

class VirtualList {
    constructor(container, options = {}) {
        this.container = container;
        this.options = {
            itemHeight: 50,
            buffer: 5,
            threshold: 0.1,
            ...options
        };

        this.items = [];
        this.visibleItems = new Map();
        this.startIndex = 0;
        this.endIndex = 0;
        
        this.scrollTop = 0;
        this.containerHeight = 0;
        
        this.init();
    }

    init() {
        this.containerHeight = this.container.clientHeight;
        
        // Create scroll container
        this.scrollContainer = document.createElement('div');
        this.scrollContainer.style.height = `${this.getTotalHeight()}px`;
        this.scrollContainer.style.position = 'relative';
        
        this.container.appendChild(this.scrollContainer);
        
        // Setup scroll listener with throttling
        let ticking = false;
        this.container.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(() => {
                    this.handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        });

        // Handle resize
        window.addEventListener('resize', this.debounce(() => {
            this.containerHeight = this.container.clientHeight;
            this.render();
        }, 250));
    }

    setItems(items) {
        this.items = items;
        this.scrollContainer.style.height = `${this.getTotalHeight()}px`;
        this.render();
    }

    getTotalHeight() {
        return this.items.length * this.options.itemHeight;
    }

    handleScroll() {
        this.scrollTop = this.container.scrollTop;
        this.render();
    }

    render() {
        const visibleStart = Math.floor(this.scrollTop / this.options.itemHeight);
        const visibleEnd = Math.min(
            visibleStart + Math.ceil(this.containerHeight / this.options.itemHeight),
            this.items.length
        );

        // Add buffer
        this.startIndex = Math.max(0, visibleStart - this.options.buffer);
        this.endIndex = Math.min(this.items.length, visibleEnd + this.options.buffer);

        // Remove items outside visible range
        this.visibleItems.forEach((element, index) => {
            if (index < this.startIndex || index >= this.endIndex) {
                element.remove();
                this.visibleItems.delete(index);
            }
        });

        // Add new visible items
        for (let i = this.startIndex; i < this.endIndex; i++) {
            if (!this.visibleItems.has(i)) {
                const element = this.renderItem(this.items[i], i);
                this.visibleItems.set(i, element);
                this.scrollContainer.appendChild(element);
            }
        }
    }

    renderItem(item, index) {
        const element = document.createElement('div');
        element.className = 'virtual-list-item';
        element.style.position = 'absolute';
        element.style.top = `${index * this.options.itemHeight}px`;
        element.style.height = `${this.options.itemHeight}px`;
        element.style.width = '100%';

        // Custom render function
        if (this.options.renderItem) {
            this.options.renderItem(element, item, index);
        } else {
            element.textContent = String(item);
        }

        return element;
    }

    scrollToIndex(index) {
        const scrollTop = index * this.options.itemHeight;
        this.container.scrollTop = scrollTop;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    destroy() {
        this.visibleItems.clear();
        if (this.scrollContainer) {
            this.scrollContainer.remove();
        }
    }
}

// ===== BUNDLE ANALYZER =====

class BundleAnalyzer {
    constructor() {
        this.loadTimes = new Map();
        this.sizes = new Map();
        this.errors = [];
    }

    trackScript(src) {
        const start = performance.now();
        
        return {
            onLoad: () => {
                const loadTime = performance.now() - start;
                this.loadTimes.set(src, loadTime);
                this.analyzeSize(src);
            },
            onError: (error) => {
                this.errors.push({ src, error, timestamp: Date.now() });
            }
        };
    }

    async analyzeSize(src) {
        try {
            const response = await fetch(src, { method: 'HEAD' });
            const size = response.headers.get('content-length');
            if (size) {
                this.sizes.set(src, parseInt(size));
            }
        } catch (error) {
            console.warn(`Failed to analyze size for ${src}:`, error);
        }
    }

    getReport() {
        const totalSize = Array.from(this.sizes.values()).reduce((a, b) => a + b, 0);
        const avgLoadTime = Array.from(this.loadTimes.values()).reduce((a, b) => a + b, 0) / this.loadTimes.size;

        const recommendations = [];
        
        // Analyze load times
        this.loadTimes.forEach((time, src) => {
            if (time > 1000) {
                recommendations.push(`Slow loading script: ${src} (${time.toFixed(2)}ms)`);
            }
        });

        // Analyze sizes
        this.sizes.forEach((size, src) => {
            if (size > 100000) { // > 100KB
                recommendations.push(`Large script: ${src} (${(size / 1024).toFixed(2)}KB)`);
            }
        });

        return {
            summary: {
                totalScripts: this.loadTimes.size,
                totalSize: `${(totalSize / 1024).toFixed(2)}KB`,
                avgLoadTime: `${avgLoadTime.toFixed(2)}ms`,
                errors: this.errors.length
            },
            details: {
                loadTimes: Object.fromEntries(this.loadTimes),
                sizes: Object.fromEntries(this.sizes),
                errors: this.errors
            },
            recommendations
        };
    }
}

// ===== CACHE MANAGER =====

class CacheManager {
    constructor() {
        this.memoryCache = new Map();
        this.cachePrefix = 'mab-cache-';
        this.maxMemoryItems = 100;
        this.defaultTTL = 5 * 60 * 1000; // 5 minutos
    }

    async get(key, fetcher, options = {}) {
        const { ttl = this.defaultTTL, useMemory = true, useStorage = true } = options;
        
        // Check memory cache first
        if (useMemory) {
            const memoryItem = this.memoryCache.get(key);
            if (memoryItem && Date.now() < memoryItem.expires) {
                return memoryItem.data;
            }
        }

        // Check localStorage
        if (useStorage) {
            const storageItem = this.getFromStorage(key);
            if (storageItem && Date.now() < storageItem.expires) {
                // Update memory cache
                if (useMemory) {
                    this.setMemoryCache(key, storageItem.data, storageItem.expires);
                }
                return storageItem.data;
            }
        }

        // Fetch new data
        try {
            const data = await fetcher();
            const expires = Date.now() + ttl;
            
            // Cache the result
            if (useMemory) {
                this.setMemoryCache(key, data, expires);
            }
            
            if (useStorage) {
                this.setStorage(key, data, expires);
            }
            
            return data;
        } catch (error) {
            // Return stale data if available
            const staleMemory = this.memoryCache.get(key);
            if (staleMemory) {
                console.warn(`Using stale cache for ${key}:`, error);
                return staleMemory.data;
            }
            
            throw error;
        }
    }

    setMemoryCache(key, data, expires) {
        // Cleanup old items if at max capacity
        if (this.memoryCache.size >= this.maxMemoryItems) {
            const oldestKey = this.memoryCache.keys().next().value;
            this.memoryCache.delete(oldestKey);
        }

        this.memoryCache.set(key, { data, expires });
    }

    getFromStorage(key) {
        try {
            const item = localStorage.getItem(this.cachePrefix + key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.warn(`Failed to read cache ${key}:`, error);
            return null;
        }
    }

    setStorage(key, data, expires) {
        try {
            const item = { data, expires };
            localStorage.setItem(this.cachePrefix + key, JSON.stringify(item));
        } catch (error) {
            console.warn(`Failed to cache ${key}:`, error);
            // Handle quota exceeded
            if (error.name === 'QuotaExceededError') {
                this.cleanupStorage();
            }
        }
    }

    cleanupStorage() {
        const keysToDelete = [];
        const now = Date.now();

        // Find expired items
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                try {
                    const item = JSON.parse(localStorage.getItem(key));
                    if (item.expires < now) {
                        keysToDelete.push(key);
                    }
                } catch (error) {
                    keysToDelete.push(key); // Remove corrupted items
                }
            }
        }

        // Delete expired items
        keysToDelete.forEach(key => localStorage.removeItem(key));
        
        console.log(`Cleaned up ${keysToDelete.length} expired cache items`);
    }

    invalidate(pattern) {
        // Clear memory cache
        if (pattern instanceof RegExp) {
            for (const [key] of this.memoryCache) {
                if (pattern.test(key)) {
                    this.memoryCache.delete(key);
                }
            }
        } else {
            this.memoryCache.delete(pattern);
        }

        // Clear storage cache
        const keysToDelete = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                const cacheKey = key.substring(this.cachePrefix.length);
                if (pattern instanceof RegExp ? pattern.test(cacheKey) : cacheKey === pattern) {
                    keysToDelete.push(key);
                }
            }
        }
        keysToDelete.forEach(key => localStorage.removeItem(key));
    }

    clear() {
        this.memoryCache.clear();
        
        // Clear all cache items from localStorage
        const keysToDelete = [];
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith(this.cachePrefix)) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => localStorage.removeItem(key));
    }

    getStats() {
        return {
            memoryItems: this.memoryCache.size,
            storageItems: Object.keys(localStorage).filter(key => 
                key.startsWith(this.cachePrefix)
            ).length
        };
    }
}

// ===== OPTIMIZED API CLIENT =====

class APIClientOptimized extends APIClient {
    constructor(options = {}) {
        super(options);
        this.cache = new CacheManager();
        this.requestQueue = new Map();
        this.retryQueue = [];
        this.isOnline = navigator.onLine;
        
        this.setupNetworkHandling();
        this.setupRequestDeduplication();
    }

    setupNetworkHandling() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.processRetryQueue();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
        });
    }

    setupRequestDeduplication() {
        // Override request method to add deduplication
        const originalRequest = this.request.bind(this);
        
        this.request = async (config) => {
            const requestKey = this.generateRequestKey(config);
            
            // Check if identical request is already in flight
            if (this.requestQueue.has(requestKey)) {
                return this.requestQueue.get(requestKey);
            }

            // For GET requests, check cache first
            if (config.method === 'GET' || !config.method) {
                const cacheKey = this.generateCacheKey(config);
                try {
                    const cachedResponse = await this.cache.get(
                        cacheKey,
                        () => originalRequest(config),
                        { ttl: config.cacheTTL || 60000 } // 1 minute default
                    );
                    return cachedResponse;
                } catch (error) {
                    // Fall through to normal request handling
                }
            }

            // Execute request with deduplication
            const requestPromise = originalRequest(config);
            this.requestQueue.set(requestKey, requestPromise);

            try {
                const response = await requestPromise;
                return response;
            } finally {
                this.requestQueue.delete(requestKey);
            }
        };
    }

    generateRequestKey(config) {
        const key = `${config.method || 'GET'}:${config.url}`;
        if (config.params) {
            key += ':' + JSON.stringify(config.params);
        }
        if (config.data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            key += ':' + JSON.stringify(config.data);
        }
        return key;
    }

    generateCacheKey(config) {
        return `api:${this.generateRequestKey(config)}`;
    }

    async processRetryQueue() {
        if (!this.isOnline || this.retryQueue.length === 0) return;

        const retryItems = [...this.retryQueue];
        this.retryQueue = [];

        const retryPromises = retryItems.map(async ({ config, resolve, reject }) => {
            try {
                const response = await this.request(config);
                resolve(response);
            } catch (error) {
                reject(error);
            }
        });

        await Promise.allSettled(retryPromises);
    }

    // Batch multiple requests
    async batchRequests(configs, options = {}) {
        const { maxConcurrent = 6, delayBetween = 0 } = options;
        const results = [];
        
        for (let i = 0; i < configs.length; i += maxConcurrent) {
            const batch = configs.slice(i, i + maxConcurrent);
            const batchPromises = batch.map(config => 
                this.request(config).catch(error => ({ error, config }))
            );
            
            const batchResults = await Promise.all(batchPromises);
            results.push(...batchResults);
            
            // Delay between batches to avoid overwhelming server
            if (delayBetween > 0 && i + maxConcurrent < configs.length) {
                await new Promise(resolve => setTimeout(resolve, delayBetween));
            }
        }

        return results;
    }

    // Optimistic updates
    async optimisticRequest(config, optimisticUpdate) {
        // Apply optimistic update immediately
        if (optimisticUpdate && window.MAB?.state) {
            window.MAB.state.batchSet(optimisticUpdate.data);
        }

        try {
            const response = await this.request(config);
            
            // Apply real response
            if (optimisticUpdate && optimisticUpdate.onSuccess) {
                optimisticUpdate.onSuccess(response.data);
            }
            
            return response;
        } catch (error) {
            // Revert optimistic update on error
            if (optimisticUpdate && optimisticUpdate.onError) {
                optimisticUpdate.onError(error);
            }
            throw error;
        }
    }

    // Invalidate cached responses
    invalidateCache(pattern) {
        this.cache.invalidate(pattern);
    }
}

// ===== INITIALIZATION OPTIMIZER =====

class InitializationOptimizer {
    constructor() {
        this.criticalTasks = [];
        this.deferredTasks = [];
        this.idleTasks = [];
        this.completed = new Set();
    }

    addCriticalTask(name, task) {
        this.criticalTasks.push({ name, task, priority: 1 });
        return this;
    }

    addDeferredTask(name, task, delay = 0) {
        this.deferredTasks.push({ name, task, delay, priority: 2 });
        return this;
    }

    addIdleTask(name, task) {
        this.idleTasks.push({ name, task, priority: 3 });
        return this;
    }

    async execute() {
        const startTime = performance.now();

        try {
            // Execute critical tasks first
            await this.executeCriticalTasks();
            
            // Schedule deferred tasks
            this.scheduleDeferredTasks();
            
            // Schedule idle tasks
            this.scheduleIdleTasks();

            const totalTime = performance.now() - startTime;
            console.log(`Initialization completed in ${totalTime.toFixed(2)}ms`);
            
        } catch (error) {
            console.error('Critical initialization failed:', error);
            throw error;
        }
    }

    async executeCriticalTasks() {
        for (const taskInfo of this.criticalTasks) {
            const start = performance.now();
            
            try {
                await taskInfo.task();
                this.completed.add(taskInfo.name);
                
                const duration = performance.now() - start;
                console.log(`Critical task "${taskInfo.name}" completed in ${duration.toFixed(2)}ms`);
                
            } catch (error) {
                console.error(`Critical task "${taskInfo.name}" failed:`, error);
                throw error;
            }
        }
    }

    scheduleDeferredTasks() {
        this.deferredTasks.forEach(taskInfo => {
            setTimeout(async () => {
                const start = performance.now();
                
                try {
                    await taskInfo.task();
                    this.completed.add(taskInfo.name);
                    
                    const duration = performance.now() - start;
                    console.log(`Deferred task "${taskInfo.name}" completed in ${duration.toFixed(2)}ms`);
                    
                } catch (error) {
                    console.error(`Deferred task "${taskInfo.name}" failed:`, error);
                }
            }, taskInfo.delay);
        });
    }

    scheduleIdleTasks() {
        const executeIdleTask = (taskInfo) => {
            const start = performance.now();
            
            try {
                const result = taskInfo.task();
                
                // Handle both sync and async tasks
                Promise.resolve(result).then(() => {
                    this.completed.add(taskInfo.name);
                    
                    const duration = performance.now() - start;
                    console.log(`Idle task "${taskInfo.name}" completed in ${duration.toFixed(2)}ms`);
                }).catch(error => {
                    console.error(`Idle task "${taskInfo.name}" failed:`, error);
                });
                
            } catch (error) {
                console.error(`Idle task "${taskInfo.name}" failed:`, error);
            }
        };

        if (window.requestIdleCallback) {
            this.idleTasks.forEach(taskInfo => {
                window.requestIdleCallback(() => executeIdleTask(taskInfo));
            });
        } else {
            // Fallback for browsers without requestIdleCallback
            this.idleTasks.forEach((taskInfo, index) => {
                setTimeout(() => executeIdleTask(taskInfo), 100 * index);
            });
        }
    }

    getCompletedTasks() {
        return Array.from(this.completed);
    }

    getProgress() {
        const total = this.criticalTasks.length + this.deferredTasks.length + this.idleTasks.length;
        const completed = this.completed.size;
        return { completed, total, percentage: (completed / total) * 100 };
    }
}

// ===== USAGE EXAMPLES =====

// Example: Optimized application initialization
async function initializeOptimizedApp() {
    const optimizer = new InitializationOptimizer();
    const scriptLoader = new ScriptLoader();
    const resourceManager = new ResourceManager();

    // Critical tasks (blocking)
    optimizer
        .addCriticalTask('preload-scripts', () => scriptLoader.preloadCriticalScripts())
        .addCriticalTask('setup-state', () => {
            // Initialize state management
            window.MAB = new MABAppOptimized();
        })
        .addCriticalTask('setup-ui', () => {
            // Setup critical UI elements
            return window.MAB.setupCriticalSystems();
        });

    // Deferred tasks (non-blocking, scheduled)
    optimizer
        .addDeferredTask('load-components', () => scriptLoader.loadNonCriticalScripts(), 500)
        .addDeferredTask('lazy-images', () => resourceManager.lazyLoadImages(), 1000)
        .addDeferredTask('analytics', () => {
            // Initialize analytics
            if (window.gtag) {
                gtag('config', 'GA_TRACKING_ID');
            }
        }, 2000);

    // Idle tasks (when browser is idle)
    optimizer
        .addIdleTask('preload-routes', () => {
            // Preload likely next pages
            scriptLoader.loadScript('/static/js/pages/experiments.js');
        })
        .addIdleTask('service-worker', () => {
            // Register service worker
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js');
            }
        });

    // Execute optimization
    await optimizer.execute();
    
    return window.MAB;
}

// Export for use
if (typeof window !== 'undefined') {
    window.initializeOptimizedApp = initializeOptimizedApp;
    window.ScriptLoader = ScriptLoader;
    window.ResourceManager = ResourceManager;
    window.VirtualList = VirtualList;
    window.CacheManager = CacheManager;
    window.APIClientOptimized = APIClientOptimized;
}
