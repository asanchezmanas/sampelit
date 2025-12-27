# UI Specs - Create Experiment

**Archivo**: `experiments_create_v2.html`  
**Endpoint**: `POST /experiments`

---

## Job del Usuario

> "Quiero empezar a probar algo rápido, sin complicaciones técnicas"

---

## Wireframe (3 pasos)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Crear nuevo experimento                                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PASO 1 DE 3: ¿Qué quieres probar?                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Nombre del experimento                                     │   │
│  │  [Test del botón de compra en homepage_________________]    │   │
│  │                                                             │   │
│  │  ¿En qué página?                                            │   │
│  │  [https://mitienda.com/________________________]            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                        [Continuar →]                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PASO 2 DE 3: Crea tus variantes                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  CONTROL (tu versión actual)                                │   │
│  │  [Comprar ahora_________________________________]           │   │
│  │                                                             │   │
│  │  VARIANTE B (tu idea nueva)                                 │   │
│  │  [¡Añadir al carrito!___________________________]           │   │
│  │                                                             │   │
│  │  [+ Añadir otra variante]                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                    [← Atrás]   [Continuar →]                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  PASO 3 DE 3: ¿Qué quieres medir?                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ¿Qué cuenta como éxito?                                    │   │
│  │  ○ Click en un botón                                        │   │
│  │  ● Visita a una página (ej: /gracias)                       │   │
│  │  ○ Envío de formulario                                      │   │
│  │  ○ Compra completada                                        │   │
│  │                                                             │   │
│  │  Página de éxito:                                           │   │
│  │  [https://mitienda.com/gracias___________________]          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                    [← Atrás]   [🚀 Lanzar experimento]              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Mapeo UI → API

### Endpoint: `POST /experiments`

**Request (generado desde el wizard):**
```json
{
  "name": "Test del botón de compra en homepage",
  "url": "https://mitienda.com/",
  "goal_type": "page_visit",
  "goal_url": "https://mitienda.com/gracias",
  "elements": [{
    "name": "CTA Button",
    "element_type": "text",
    "variants": [
      { "name": "Control", "content": "Comprar ahora", "is_control": true },
      { "name": "Variante B", "content": "¡Añadir al carrito!", "is_control": false }
    ]
  }],
  "traffic_allocation": 100,
  "status": "active"
}
```

| Campo UI | Campo API | Notas |
|----------|-----------|-------|
| Nombre | `name` | Requerido |
| URL | `url` | Requerido |
| Tipo de objetivo | `goal_type` | `page_visit`, `click`, `form_submit`, `purchase` |
| Página de éxito | `goal_url` | Solo si goal_type = page_visit |
| Variantes | `elements[0].variants` | Mínimo 2 |

---

## Campos Obligatorios vs Opcionales

| Campo | Obligatorio | Default |
|-------|-------------|---------|
| Nombre | ✅ | — |
| URL | ✅ | — |
| Variantes (mín 2) | ✅ | — |
| Objetivo | ✅ | — |
| Traffic allocation | ❌ | 100% |
| Algoritmo | ❌ | Thompson Sampling (oculto) |

**Regla: Ocultar todo lo que tenga un default sensato.**

---

## Componente Alpine.js

```javascript
function createExperiment() {
  return {
    step: 1,
    saving: false,
    error: null,
    
    // Datos del formulario
    form: {
      name: '',
      url: '',
      goalType: 'page_visit',
      goalUrl: '',
      variants: [
        { name: 'Control', content: '', isControl: true },
        { name: 'Variante B', content: '', isControl: false }
      ]
    },
    
    // Navegación
    nextStep() {
      if (this.validateStep()) this.step++;
    },
    prevStep() {
      this.step--;
    },
    
    validateStep() {
      if (this.step === 1) {
        return this.form.name.trim() && this.form.url.trim();
      }
      if (this.step === 2) {
        return this.form.variants.every(v => v.content.trim());
      }
      return true;
    },
    
    // Variantes
    addVariant() {
      const letter = String.fromCharCode(65 + this.form.variants.length);
      this.form.variants.push({ 
        name: `Variante ${letter}`, 
        content: '', 
        isControl: false 
      });
    },
    removeVariant(index) {
      if (this.form.variants.length > 2 && !this.form.variants[index].isControl) {
        this.form.variants.splice(index, 1);
      }
    },
    
    // Submit
    async submit() {
      this.saving = true;
      this.error = null;
      
      try {
        const payload = {
          name: this.form.name,
          url: this.form.url,
          goal_type: this.form.goalType,
          goal_url: this.form.goalUrl,
          elements: [{
            name: 'Element 1',
            element_type: 'text',
            variants: this.form.variants.map(v => ({
              name: v.name,
              content: v.content,
              is_control: v.isControl
            }))
          }],
          status: 'active'
        };
        
        await APIClient.post('/experiments', payload);
        window.location.href = 'experiments_v2.html?created=true';
      } catch (e) {
        this.error = e.message;
      } finally {
        this.saving = false;
      }
    }
  }
}
```

---

## Validaciones

| Campo | Validación | Mensaje de Error |
|-------|------------|------------------|
| Nombre | No vacío | "Dale un nombre a tu experimento" |
| URL | URL válida | "Ingresa una URL válida" |
| Variantes | Mínimo 2 | "Necesitas al menos 2 variantes" |
| Contenido variante | No vacío | "Cada variante necesita contenido" |
| Goal URL | URL válida si goal_type = page_visit | "Ingresa la página de éxito" |

---

## Estados del Botón Submit

```html
<button 
  @click="submit()"
  :disabled="saving || !validateStep()"
  :class="saving ? 'opacity-50 cursor-wait' : ''">
  <span x-show="!saving">🚀 Lanzar experimento</span>
  <span x-show="saving" class="flex items-center gap-2">
    <svg class="animate-spin h-4 w-4">...</svg>
    Lanzando...
  </span>
</button>
```
