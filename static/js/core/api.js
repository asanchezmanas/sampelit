// static/js/core/api.js

class APIClient {
    constructor(options = {}) {
        this.options = {
            baseUrl: '',
            timeout: 30000,
            retries: 3,
            retryDelay: 1000,
            ...options
        };
        
        this.csrfToken = options.csrfToken;
        this.requestInterceptors = [];
        this.responseInterceptors = [];
        
        // Setup default interceptors
        this.setupDefaultInterceptors();
    }
    
    // ===== INTERCEPTORS =====
    
    setupDefaultInterceptors() {
        // Request interceptor to add auth token
        this.addRequestInterceptor((config) => {
            const token = localStorage.getItem('mab_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });
        
        // Response interceptor to handle common errors
        this.addResponseInterceptor(
            (response) => response,
            (error) => {
                if (error.status === 401) {
                    // Token expired or invalid
                    localStorage.removeItem('mab_token');
                    if (window.location.pathname !== '/login') {
                        window.location.href = '/login';
                    }
                }
                throw error;
            }
        );
    }
    
    addRequestInterceptor(onFulfilled, onRejected) {
        this.requestInterceptors.push({ onFulfilled, onRejected });
        return this.requestInterceptors.length - 1;
    }
    
    addResponseInterceptor(onFulfilled, onRejected) {
        this.responseInterceptors.push({ onFulfilled, onRejected });
        return this.responseInterceptors.length - 1;
    }
    
    // ===== CORE REQUEST METHOD =====
    
    async request(config) {
        // Apply request interceptors
        let requestConfig = { ...config };
        
        for (const interceptor of this.requestInterceptors) {
            try {
                if (interceptor.onFulfilled) {
                    requestConfig = await interceptor.onFulfilled(requestConfig);
                }
            } catch (error) {
                if (interceptor.onRejected) {
                    requestConfig = await interceptor.onRejected(error);
                } else {
                    throw error;
                }
            }
        }
        
        // Prepare URL
        const url = this.buildUrl(requestConfig.url);
        
        // Prepare headers
        const headers = {
            'Content-Type': 'application/json',
            ...requestConfig.headers
        };
        
        if (this.csrfToken) {
            headers['X-CSRF-Token'] = this.csrfToken;
        }
        
        // Prepare fetch options
        const fetchOptions = {
            method: requestConfig.method || 'GET',
            headers,
            ...requestConfig.options
        };
        
        // Add body for POST/PUT/PATCH requests
        if (requestConfig.data && ['POST', 'PUT', 'PATCH'].includes(fetchOptions.method)) {
            if (requestConfig.data instanceof FormData) {
                // Don't set Content-Type for FormData, let browser set it
                delete headers['Content-Type'];
                fetchOptions.body = requestConfig.data;
            } else {
                fetchOptions.body = JSON.stringify(requestConfig.data);
            }
        }
        
        // Add query parameters for GET requests
        if (requestConfig.params && fetchOptions.method === 'GET') {
            const searchParams = new URLSearchParams(requestConfig.params);
            const separator = url.includes('?') ? '&' : '?';
            url = url + separator + searchParams.toString();
        }
        
        // Make request with retry logic
        let lastError;
        
        for (let attempt = 0; attempt <= this.options.retries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), this.options.timeout);
                
                fetchOptions.signal = controller.signal;
                
                const response = await fetch(url, fetchOptions);
                clearTimeout(timeoutId);
                
                // Parse response
                const result = await this.parseResponse(response);
                
                // Apply response interceptors
                let finalResult = result;
                
                for (const interceptor of this.responseInterceptors) {
                    try {
                        if (interceptor.onFulfilled) {
                            finalResult = await interceptor.onFulfilled(finalResult);
                        }
                    } catch (error) {
                        if (interceptor.onRejected) {
                            finalResult = await interceptor.onRejected(error);
                        } else {
                            throw error;
                        }
                    }
                }
                
                return finalResult;
                
            } catch (error) {
                lastError = error;
                
                // Don't retry on client errors (4xx) or auth errors
                if (error.status >= 400 && error.status < 500) {
                    break;
                }
                
                // Don't retry on last attempt
                if (attempt === this.options.retries) {
                    break;
                }
                
                // Wait before retry
                await this.delay(this.options.retryDelay * (attempt + 1));
            }
        }
        
        // Apply error response interceptors
        for (const interceptor of this.responseInterceptors) {
            if (interceptor.onRejected) {
                try {
                    return await interceptor.onRejected(lastError);
                } catch (error) {
                    lastError = error;
                }
            }
        }
        
        throw lastError;
    }
    
    // ===== RESPONSE PARSING =====
    
    async parseResponse(response) {
        const contentType = response.headers.get('content-type');
        
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        
        const result = {
            data,
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers),
            success: response.ok
        };
        
        if (!response.ok) {
            const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
            error.response = result;
            error.status = response.status;
            throw error;
        }
        
        return result;
    }
    
    // ===== CONVENIENCE METHODS =====
    
    async get(url, params = {}, options = {}) {
        return this.request({
            method: 'GET',
            url,
            params,
            ...options
        });
    }
    
    async post(url, data = {}, options = {}) {
        return this.request({
            method: 'POST',
            url,
            data,
            ...options
        });
    }
    
    async put(url, data = {}, options = {}) {
        return this.request({
            method: 'PUT',
            url,
            data,
            ...options
        });
    }
    
    async patch(url, data = {}, options = {}) {
        return this.request({
            method: 'PATCH',
            url,
            data,
            ...options
        });
    }
    
    async delete(url, options = {}) {
        return this.request({
            method: 'DELETE',
            url,
            ...options
        });
    }
    
    // ===== FILE UPLOADS =====
    
    async upload(url, file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add additional fields if provided
        if (options.fields) {
            Object.entries(options.fields).forEach(([key, value]) => {
                formData.append(key, value);
            });
        }
        
        return this.request({
            method: 'POST',
            url,
            data: formData,
            headers: {
                // Don't set Content-Type, let browser set it for FormData
            },
            ...options
        });
    }
    
    // ===== UTILITIES =====
    
    buildUrl(path) {
        if (path.startsWith('http://') || path.startsWith('https://')) {
            return path;
        }
        
        const base = this.options.baseUrl.replace(/\/$/, '');
        const cleanPath = path.replace(/^\//, '');
        
        return base ? `${base}/${cleanPath}` : `/${cleanPath}`;
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // ===== BATCH REQUESTS =====
    
    async batch(requests) {
        const promises = requests.map(request => 
            this.request(request).catch(error => ({ error, request }))
        );
        
        const results = await Promise.all(promises);
        
        return {
            success: results.filter(r => !r.error),
            errors: results.filter(r => r.error)
        };
    }
    
    // ===== CANCELLATION =====
    
    createCancellableRequest(config) {
        const controller = new AbortController();
        
        const promise = this.request({
            ...config,
            options: {
                ...config.options,
                signal: controller.signal
            }
        });
        
        return {
            promise,
            cancel: () => controller.abort()
        };
    }
}
