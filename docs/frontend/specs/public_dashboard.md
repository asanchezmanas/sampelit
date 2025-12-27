# UI Specs - Public Dashboard (Demo en Vivo)

**Archivo**: Template `templates/pages/public/dashboard.html`  
**Endpoints**:
- `GET /public-dashboard/{experiment_id}` - HTML renderizado
- `GET /public-dashboard/api/{experiment_id}` - JSON

---

## Propósito (Transparencia)

> **Los usuarios pueden ver experimentos REALES corriendo en samplit.com, con datos REALES pero información privada ofuscada. Esto demuestra que el sistema funciona.**

---

## Job del Usuario

> "Quiero ver que esto funciona de verdad, no solo demos con datos fake"

---

## Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔴 EN VIVO                                     samplit.com/public  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  EXPERIMENTO EN CURSO                                        │  │
│  │  "Homepage Optimization"                                     │  │
│  │  Iniciado: 20 Dic 2024 • Estado: Activo                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  📊 RENDIMIENTO EN TIEMPO REAL                                      │
│                                                                     │
│  ┌────────────────────┐  ┌────────────────────┐                    │
│  │  Control           │  │  Variante B 🏆     │                    │
│  │                    │  │                    │                    │
│  │  Visitantes: 5,234 │  │  Visitantes: 5,198 │                    │
│  │  Conversiones: 267 │  │  Conversiones: 342 │                    │
│  │  Tasa: 5.1%        │  │  Tasa: 6.6%        │                    │
│  │                    │  │  +28% vs control   │                    │
│  │  ████████████░░░░  │  │  █████████████████ │                    │
│  └────────────────────┘  └────────────────────┘                    │
│                                                                     │
│  ⚡ El algoritmo está enviando 67% del tráfico a la variante       │
│     que está funcionando mejor.                                    │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ⏱️ Última actualización: hace 12 segundos                   │  │
│  │  [🔄 Actualizar ahora]                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Qué SÍ se muestra (Público)

| Dato | Ejemplo | Por qué |
|------|---------|---------|
| Nombre del experimento | "Homepage Optimization" | Genérico, no revela detalles |
| Número de visitantes | 5,234 | Muestra escala real |
| Número de conversiones | 267 | Prueba resultados reales |
| Tasa de conversión | 5.1% | Métrica verificable |
| Variante ganadora | "Variante B" | Demuestra que hay diferencias |
| Fecha de inicio | 20 Dic 2024 | Contexto temporal |

---

## Qué NO se muestra (Privado)

| Dato | Por qué ocultar |
|------|-----------------|
| Texto de las variantes | "Comprar ahora" vs "Añadir al carrito" 🚫 |
| URL del sitio | cliente.com 🚫 |
| Valor de las conversiones | €45.00 🚫 |
| ID del cliente | UUID 🚫 |
| Revenue total | €12,000 🚫 |
| Nombre del cliente | Empresa X 🚫 |

---

## API Response

### `GET /public-dashboard/api/{experiment_id}`

```json
{
  "id": "exp_abc123",
  "name": "Homepage Optimization",
  "description": "Testing CTA button placement",
  "status": "active",
  "started_at": "2024-12-20T10:00:00Z",
  "has_winner": true,
  "variants": [
    {
      "id": "var_001",
      "name": "Control",
      "allocations": 5234,
      "conversions": 267,
      "conversion_rate": 0.051,
      "is_winner": false
    },
    {
      "id": "var_002",
      "name": "Variante B",
      "allocations": 5198,
      "conversions": 342,
      "conversion_rate": 0.066,
      "is_winner": true
    }
  ]
}
```

**Notas:**
- No incluye el contenido de las variantes
- No incluye información del cliente
- No incluye valores monetarios
- Solo nombres genéricos de variantes

---

## Implementación: Ofuscación en Backend

```python
async def fetch_sanitized_experiment(experiment_id: str, db: DatabaseManager):
    """Retrieves experiment data filtered for public consumption"""
    
    # Solo campos NO sensibles
    exp = await conn.fetchrow("""
        SELECT id, name, description, status, started_at 
        FROM experiments 
        WHERE id = $1 AND is_public = true  -- Solo experimentos marcados públicos
    """, experiment_id)
    
    variants = await conn.fetch("""
        SELECT ev.id, ev.name, ev.total_allocations, ev.total_conversions, ev.conversion_rate 
        FROM element_variants ev
        -- NO incluir: ev.content, ev.original_value, ev.css_selector
    """)
    
    return {
        'id': str(exp['id']),
        'name': exp['name'],  # Nombre genérico
        'variants': [
            {
                'name': v['name'],  # "Control", "Variante B"
                'allocations': v['total_allocations'],
                'conversions': v['total_conversions'],
                'conversion_rate': float(v['conversion_rate']),
                # NO incluir: v['content'], v['value']
            }
            for v in variants
        ]
    }
```

---

## Lista de Experimentos Públicos

Crear endpoint para listar todos los experimentos públicos disponibles:

```
┌─────────────────────────────────────────────────────────────────────┐
│  🔴 DEMOS EN VIVO                                                   │
│  Experimentos reales de Samplit                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Homepage Optimization          🟢 Activo    Ver →           │  │
│  │  5,234 visitantes • Variante B ganando                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CTA Test                       ✓ Completado    Ver →        │  │
│  │  12,847 visitantes • Variante A ganó (+34%)                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Pricing Page                   🟢 Activo    Ver →           │  │
│  │  3,102 visitantes • Sin ganador claro aún                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Componente Alpine.js (Widget Embebible)

```javascript
function publicDashboard() {
  return {
    experiment: null,
    loading: true,
    error: null,
    lastUpdate: null,
    
    async init() {
      await this.loadData();
      // Auto-refresh cada 30 segundos
      setInterval(() => this.loadData(), 30000);
    },
    
    async loadData() {
      try {
        const id = new URLSearchParams(location.search).get('id');
        const res = await fetch(`/public-dashboard/api/${id}`);
        this.experiment = await res.json();
        this.lastUpdate = new Date();
      } catch (e) {
        this.error = 'No se pudo cargar el experimento';
      } finally {
        this.loading = false;
      }
    },
    
    get leader() {
      return this.experiment?.variants.find(v => v.is_winner);
    },
    
    get control() {
      return this.experiment?.variants.find(v => v.name === 'Control');
    },
    
    get uplift() {
      if (!this.leader || !this.control) return 0;
      return ((this.leader.conversion_rate - this.control.conversion_rate) 
              / this.control.conversion_rate * 100).toFixed(1);
    },
    
    formatTime(date) {
      const seconds = Math.floor((Date.now() - date) / 1000);
      if (seconds < 60) return `hace ${seconds} segundos`;
      return `hace ${Math.floor(seconds/60)} minutos`;
    }
  }
}
```

---

## Uso Principal

1. **Demos de ventas**: Mostrar experimento real corriendo
2. **Transparencia**: Probar que el sistema funciona
3. **Confianza**: Datos reales > datos fake
4. **Marketing**: Compartir en redes sociales
