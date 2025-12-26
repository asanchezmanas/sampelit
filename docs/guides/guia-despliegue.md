# Guía de Despliegue (Self-Hosting)

Esta guía detalla cómo desplegar la plataforma Sampelit en tu propia infraestructura. Ideal para empresas que requieren control total sobre sus datos.

## Arquitectura

Sampelit consta de dos componentes principales:
1. **Backend**: Aplicación Python (FastAPI).
2. **Base de Datos**: PostgreSQL 13+.

## Requisitos Previos

- Docker y Docker Compose (Recomendado)
- O Python 3.10+ y PostgreSQL instalados localmente
- Acceso a terminal y Git

---

## Opción 1: Despliegue con Docker (Recomendado)

Esta es la forma más sencilla de levantar la plataforma completa.

1. **Clonar el repositorio**:
   ```bash
   git clone <repo-url>
   cd Sampelit
   ```

2. **Crear archivo `.env`**:
   Crea un archivo `.env` en la raíz con lo siguiente:
   ```env
   DATABASE_URL=postgres://postgres:password@db:5432/Sampelit
   SECRET_KEY=cambia_esto_por_algo_seguro_y_largo
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

3. **Crear `docker-compose.yml`**:
   Crea este archivo en la raíz para orquestar los servicios:
   ```yaml
   version: '3.8'
   services:
     web:
       build: .
       command: uvicorn main:app --host 0.0.0.0 --port 8000
       ports:
         - "8000:8000"
       environment:
         - DATABASE_URL=postgres://postgres:password@db:5432/Sampelit
         - SECRET_KEY=${SECRET_KEY}
       depends_on:
         - db
     
     db:
       image: postgres:13
       environment:
         - POSTGRES_USER=postgres
         - POSTGRES_PASSWORD=password
         - POSTGRES_DB=Sampelit
       volumes:
         - postgres_data:/var/lib/postgresql/data

   volumes:
     postgres_data:
   ```

4. **Iniciar servicios**:
   ```bash
   docker-compose up -d
   ```

---

## Opción 2: Render / Railway (PaaS)

El repositorio incluye un archivo `render.yaml` listo para usar en Render.com.

1. Haz fork del repositorio en GitHub/GitLab.
2. En Render, crea un nuevo "Blueprint Instance".
3. Conecta tu repositorio.
4. Render detectará la configuración y provisionará la base de datos y el servicio web automáticamente.

---

## Configuración del Tracker para Self-Hosting

El archivo `t.js` (el tracker) está configurado por defecto para apuntar a la nube de Sampelit (`api.Sampelit.com`). 

**IMPORTANTE:** Si alojas tu propia instancia, debes indicar al tracker dónde enviar los datos. Tienes dos opciones:

### A) Configuración vía window (Recomendado)

En tu sitio web, configura el endpoint antes de cargar el script:

```html
<script>
  window.Sampelit_CONFIG = {
    // Reemplaza con la URL de tu instancia
    apiEndpoint: "https://tu-dominio.com/api/v1/tracker"
  };
</script>
<script src="https://tu-dominio.com/static/tracker/t.js?token=TOKEN" async></script>
```

### B) Modificar el código fuente

Edita el archivo `/static/tracker/t.js` y cambia la constante `API_ENDPOINT` por defecto:

```javascript
/* static/tracker/t.js */
const API_ENDPOINT = (window.Sampelit_CONFIG && window.Sampelit_CONFIG.apiEndpoint) ||
    'https://tu-nuevo-dominio.com/api/v1/tracker';
```

---

## Mantenimiento

### Actualizaciones
Para actualizar a la última versión:
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Backups
Se recomienda configurar backups automáticos de la base de datos PostgreSQL.
