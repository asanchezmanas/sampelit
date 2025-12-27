# 📦 JavaScript Modules

**Versión**: 2.0

---

## 📁 Estructura

```
js/
├── include.js              # Sistema de <include> tags
├── core/
│   ├── api.js              # Cliente HTTP para la API
│   ├── app.js              # Inicialización global
│   ├── state.js            # Estado global compartido
│   ├── utils.js            # Utilidades (formatters, helpers)
│   ├── performance.js      # Métricas y optimizaciones
│   └── event-bus.js        # Comunicación entre componentes
└── components/
    └── *.js                # Componentes JavaScript específicos
```

---

## 🔷 include.js

**Propósito**: Procesa tags `<include>` y carga contenido HTML

**Uso**: Cargar automáticamente en `<head>`
```html
<script src="js/include.js"></script>
```

**Cómo funciona**:
1. Al cargar la página, busca todos los `<include>`
2. Fetch del archivo especificado en `src`
3. Reemplaza el tag con el contenido
4. Ejecuta scripts inline del partial
5. Dispara evento `include-loaded`

---

## 🔷 core/api.js

**Propósito**: Cliente HTTP para comunicarse con el backend

**Uso**:
```javascript
// Crear instancia
const client = new APIClient();

// GET
const experiments = await client.get('/experiments');

// POST
const created = await client.post('/experiments', {
    name: 'Test',
    variants: [...]
});

// PATCH
await client.patch(`/experiments/${id}`, { status: 'active' });

// DELETE
await client.delete(`/experiments/${id}`);
```

**Características**:
- Añade automáticamente `Authorization: Bearer <token>`
- Base URL configurable
- Manejo de errores estandarizado
- Retry automático en errores de red

---

## 🔷 core/state.js

**Propósito**: Estado global compartido entre componentes

**Uso**:
```javascript
// Leer estado
const user = State.get('user');

// Escribir estado
State.set('user', { name: 'John', email: 'john@example.com' });

// Suscribirse a cambios
State.subscribe('user', (newValue) => {
    console.log('User changed:', newValue);
});
```

---

## 🔷 core/utils.js

**Propósito**: Funciones de utilidad

**Funciones disponibles**:
```javascript
// Formatear números
formatNumber(1234567);  // "1,234,567"

// Formatear porcentajes
formatPercent(0.1234);  // "12.34%"

// Formatear fechas
formatDate(new Date()); // "Dec 27, 2024"

// Debounce
const debouncedFn = debounce(myFunction, 300);

// Throttle
const throttledFn = throttle(myFunction, 100);
```

---

## 🔷 core/event-bus.js

**Propósito**: Comunicación entre componentes desacoplados

**Uso**:
```javascript
// Emitir evento
EventBus.emit('experiment-created', { id: '123', name: 'Test' });

// Escuchar evento
EventBus.on('experiment-created', (data) => {
    console.log('New experiment:', data);
});

// Escuchar una vez
EventBus.once('user-loaded', (user) => {
    initializeDashboard(user);
});

// Dejar de escuchar
EventBus.off('experiment-created', myHandler);
```

---

## 📝 Patrón de uso en páginas

```html
<!-- Al final del body, antes de los includes -->
<script src="js/core/api.js"></script>
<script>
function miComponente() {
    return {
        data: [],
        loading: false,
        
        async init() {
            this.client = new APIClient();
            await this.loadData();
        },
        
        async loadData() {
            this.loading = true;
            try {
                const response = await this.client.get('/mi-endpoint');
                this.data = response.data;
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        }
    };
}
</script>

<include src="./partials/toast_v2.html"></include>
<include src="./partials/modals_v2.html"></include>
```

---

## ⚠️ Reglas

1. **Siempre** cargar `api.js` antes de usarlo
2. **No** crear nuevos clientes de API - usa `APIClient`
3. **Preferir** Alpine.js para estado local de componente
4. **Usar** `state.js` solo para estado que debe compartirse entre páginas

