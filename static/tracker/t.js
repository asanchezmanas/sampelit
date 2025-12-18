/**
 * Samplit Tracker - Ultra Simple Version (t.js)
 * 
 * ✅ Auto-configura desde URL params (sin window.SAMPLIT_CONFIG)
 * ✅ Funciona con 1 sola línea de código
 * ✅ No requiere configuración técnica
 * 
 * Uso:
 * <script src="https://cdn.samplit.com/t.js?token=inst_abc123" async></script>
 * 
 * @version 2.0.0
 * @license MIT
 */

(function() {
  'use strict';
  
  // ════════════════════════════════════════════════════════════════════════
  // CONFIGURACIÓN
  // ════════════════════════════════════════════════════════════════════════
  
  const VERSION = '2.0.0';
  const DEBUG = false; // Set to true for debugging
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 1: AUTO-DETECTAR TOKEN desde URL del script
  // ════════════════════════════════════════════════════════════════════════
  
  function getScriptToken() {
    // Buscar el script actual en el DOM
    const scripts = document.getElementsByTagName('script');
    
    for (let i = 0; i < scripts.length; i++) {
      const src = scripts[i].src;
      
      // Buscar nuestro script
      if (src && (src.includes('cdn.samplit.com/t.js') || src.includes('samplit.com/t.js'))) {
        try {
          // Extraer token del query param
          const url = new URL(src);
          const token = url.searchParams.get('token');
          
          if (token) {
            log('Token detected:', token.substring(0, 10) + '...');
            return token;
          }
        } catch (e) {
          error('Failed to parse script URL:', e);
        }
      }
    }
    
    // Fallback: buscar en window.SAMPLIT_CONFIG (compatibilidad)
    if (window.SAMPLIT_CONFIG && window.SAMPLIT_CONFIG.installationToken) {
      log('Token from SAMPLIT_CONFIG');
      return window.SAMPLIT_CONFIG.installationToken;
    }
    
    error('Installation token not found');
    return null;
  }
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 2: INICIALIZAR CONFIGURACIÓN
  // ════════════════════════════════════════════════════════════════════════
  
  const TOKEN = getScriptToken();
  
  if (!TOKEN) {
    error('Cannot initialize without token. Make sure the script URL includes ?token=YOUR_TOKEN');
    return;
  }
  
  // API endpoint (puede ser configurado o auto-detectado)
  const API_ENDPOINT = (window.SAMPLIT_CONFIG && window.SAMPLIT_CONFIG.apiEndpoint) || 
                       'https://api.samplit.com/api/v1/tracker';
  
  log('Samplit Tracker initialized');
  log('Version:', VERSION);
  log('Token:', TOKEN.substring(0, 10) + '...');
  log('API:', API_ENDPOINT);
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 3: USER IDENTIFICATION
  // ════════════════════════════════════════════════════════════════════════
  
  function generateUserId() {
    return 'user_' + 
           Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
  }
  
  function generateSessionId() {
    return 'sess_' + 
           Date.now() + '_' + 
           Math.random().toString(36).substring(2, 9);
  }
  
  function getUserIdentifier() {
    let userId = localStorage.getItem('samplit_user_id');
    
    if (!userId) {
      userId = generateUserId();
      localStorage.setItem('samplit_user_id', userId);
      log('New user ID generated:', userId.substring(0, 15) + '...');
    } else {
      log('Existing user ID:', userId.substring(0, 15) + '...');
    }
    
    return userId;
  }
  
  function getSessionId() {
    let sessionId = sessionStorage.getItem('samplit_session_id');
    
    if (!sessionId) {
      sessionId = generateSessionId();
      sessionStorage.setItem('samplit_session_id', sessionId);
      log('New session ID:', sessionId.substring(0, 15) + '...');
    }
    
    return sessionId;
  }
  
  const USER_ID = getUserIdentifier();
  const SESSION_ID = getSessionId();
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 4: API CALLS
  // ════════════════════════════════════════════════════════════════════════
  
  async function fetchWithRetry(url, options, retries = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch(url, options);
        return response;
      } catch (error) {
        if (i === retries - 1) throw error;
        
        // Exponential backoff
        const delay = Math.pow(2, i) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  async function getActiveExperiments() {
    try {
      log('Fetching active experiments...');
      
      const response = await fetchWithRetry(
        `${API_ENDPOINT}/experiments/active`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            installation_token: TOKEN,
            page_url: window.location.href
          })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      const experiments = data.experiments || [];
      
      log(`Found ${experiments.length} active experiments`);
      
      return experiments;
    } catch (err) {
      error('Failed to fetch experiments:', err);
      return [];
    }
  }
  
  async function assignVariant(experimentId) {
    try {
      log('Requesting variant assignment for experiment:', experimentId);
      
      const response = await fetchWithRetry(
        `${API_ENDPOINT}/assign`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            installation_token: TOKEN,
            experiment_id: experimentId,
            user_identifier: USER_ID,
            session_id: SESSION_ID,
            context: {
              page_url: window.location.href,
              referrer: document.referrer,
              user_agent: navigator.userAgent,
              screen_width: window.screen.width,
              screen_height: window.screen.height,
              timestamp: Date.now()
            }
          })
        }
      );
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const assignment = await response.json();
      
      log('Variant assigned:', assignment.variant_name);
      
      return assignment;
    } catch (err) {
      error('Assignment failed:', err);
      return null;
    }
  }
  
  async function trackConversion(experimentId, value = 1.0, metadata = {}) {
    try {
      log('Tracking conversion:', experimentId);
      
      const response = await fetch(`${API_ENDPOINT}/convert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          installation_token: TOKEN,
          experiment_id: experimentId,
          user_identifier: USER_ID,
          conversion_value: value,
          metadata: metadata
        })
      });
      
      if (response.ok) {
        log('Conversion tracked successfully');
        return true;
      } else {
        error('Conversion tracking failed:', response.status);
        return false;
      }
    } catch (err) {
      error('Conversion tracking error:', err);
      return false;
    }
  }
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 5: APLICAR VARIANTES
  // ════════════════════════════════════════════════════════════════════════
  
  function applyVariant(assignment) {
    const { content, variant_name } = assignment;
    
    if (!content) {
      log('No content to apply');
      return false;
    }
    
    // Buscar elemento
    const selector = content.selector || content.css_selector;
    
    if (!selector) {
      error('No selector provided in variant content');
      return false;
    }
    
    const element = document.querySelector(selector);
    
    if (!element) {
      error('Element not found:', selector);
      return false;
    }
    
    log('Applying variant to:', selector);
    
    try {
      // Aplicar cambios según el tipo
      if (content.html) {
        element.innerHTML = content.html;
        log('Applied HTML change');
      }
      
      if (content.text) {
        element.textContent = content.text;
        log('Applied text change');
      }
      
      if (content.css) {
        Object.assign(element.style, content.css);
        log('Applied CSS changes');
      }
      
      if (content.attributes) {
        Object.entries(content.attributes).forEach(([key, value]) => {
          element.setAttribute(key, value);
        });
        log('Applied attribute changes');
      }
      
      // Marcar elemento como modificado
      element.setAttribute('data-samplit-variant', variant_name);
      
      log('✅ Variant applied successfully:', variant_name);
      
      return true;
    } catch (err) {
      error('Failed to apply variant:', err);
      return false;
    }
  }
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 6: API PÚBLICA
  // ════════════════════════════════════════════════════════════════════════
  
  const sampitAPI = {
    /**
     * Track conversion manually
     * 
     * @param {string} experimentId - Experiment ID
     * @param {number} value - Conversion value (default: 1.0)
     * @param {object} metadata - Additional metadata
     */
    convert: function(experimentId, value = 1.0, metadata = {}) {
      return trackConversion(experimentId, value, metadata);
    },
    
    /**
     * Re-initialize tracker (refresh experiments)
     */
    refresh: function() {
      return initializeTracker();
    },
    
    /**
     * Get current user ID
     */
    getUserId: function() {
      return USER_ID;
    },
    
    /**
     * Get current session ID
     */
    getSessionId: function() {
      return SESSION_ID;
    },
    
    /**
     * Get tracker version
     */
    version: VERSION,
    
    /**
     * Check if tracker is initialized
     */
    isReady: function() {
      return !!TOKEN;
    }
  };
  
  // Exponer API públicamente
  window.samplit = sampitAPI;
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 7: INICIALIZACIÓN AUTOMÁTICA
  // ════════════════════════════════════════════════════════════════════════
  
  async function initializeTracker() {
    try {
      log('Initializing Samplit Tracker...');
      
      // Obtener experimentos activos
      const experiments = await getActiveExperiments();
      
      if (experiments.length === 0) {
        log('No active experiments for this page');
        return;
      }
      
      log(`Processing ${experiments.length} experiments...`);
      
      // Procesar cada experimento
      for (const experiment of experiments) {
        try {
          // Asignar variante
          const assignment = await assignVariant(experiment.id);
          
          if (assignment) {
            // Aplicar variante
            const applied = applyVariant(assignment);
            
            if (applied) {
              log(`✅ Experiment ${experiment.name} applied`);
            }
          }
        } catch (err) {
          error(`Error processing experiment ${experiment.id}:`, err);
        }
      }
      
      log('✅ Tracker initialization complete');
      
    } catch (err) {
      error('Tracker initialization failed:', err);
    }
  }
  
  // ════════════════════════════════════════════════════════════════════════
  // PASO 8: AUTO-START
  // ════════════════════════════════════════════════════════════════════════
  
  // Inicializar cuando el DOM esté listo
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeTracker);
  } else {
    // DOM ya está listo
    initializeTracker();
  }
  
  // ════════════════════════════════════════════════════════════════════════
  // UTILITIES
  // ════════════════════════════════════════════════════════════════════════
  
  function log(...args) {
    if (DEBUG) {
      console.log('[Samplit]', ...args);
    }
  }
  
  function error(...args) {
    console.error('[Samplit]', ...args);
  }
  
})();
