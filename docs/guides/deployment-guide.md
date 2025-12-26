# Deployment Guide (Self-Hosting)

This guide details how to deploy the Sampelit platform on your own infrastructure. Ideal for organizations that require total control over their data.

## Architecture

Sampelit consists of two main components:
1. **Backend**: Python Application (FastAPI).
2. **Database**: PostgreSQL 13+.

## Prerequisites

- Docker and Docker Compose (Recommended)
- Or Python 3.10+ and PostgreSQL installed locally
- Terminal access and Git

---

## Option 1: Docker Deployment (Recommended)

This is the easiest way to spin up the entire platform.

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd Sampelit
   ```

2. **Create `.env` file**:
   Create a `.env` file in the root directory with the following content:
   ```env
   DATABASE_URL=postgres://postgres:password@db:5432/Sampelit
   SECRET_KEY=change_this_to_something_secure_and_long
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

3. **Create `docker-compose.yml`**:
   Create this file in the root to orchestrate the services:
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

4. **Start services**:
   ```bash
   docker-compose up -d
   ```

---

## Option 2: Render / Railway (PaaS)

The repository includes a `render.yaml` file ready for use on Render.com.

1. Fork the repository on GitHub/GitLab.
2. In Render, create a new "Blueprint Instance".
3. Connect your repository.
4. Render will detect the configuration and automatically provision the database and web service.

---

## Tracker Configuration for Self-Hosting

The `t.js` file (the tracker) is configured by default to point to the Sampelit cloud (`api.Sampelit.com`). 

**IMPORTANT:** If hosting your own instance, you must tell the tracker where to send the data. You have two options:

### A) Configuration via window (Recommended)

On your website, configure the endpoint before loading the script:

```html
<script>
  window.Sampelit_CONFIG = {
    // Replace with your instance URL
    apiEndpoint: "https://your-domain.com/api/v1/tracker"
  };
</script>
<script src="https://your-domain.com/static/tracker/t.js?token=TOKEN" async></script>
```

### B) Modify the source code

Edit the file `/static/tracker/t.js` and change the default `API_ENDPOINT` constant:

```javascript
/* static/tracker/t.js */
const API_ENDPOINT = (window.Sampelit_CONFIG && window.Sampelit_CONFIG.apiEndpoint) ||
    'https://your-new-domain.com/api/v1/tracker';
```

---

## Maintenance

### Updates
To update to the latest version:
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Backups
It is recommended to set up automatic backups for the PostgreSQL database.
