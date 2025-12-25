# Samplit - Intelligent A/B Testing Platform

> **Adaptive Multi-Armed Bandit Optimization for Modern Web Applications**

Samplit is a production-ready A/B testing platform that combines traditional experimentation with adaptive optimization algorithms. Built with FastAPI, PostgreSQL, and Alpine.js, it provides transparent, verifiable experiment tracking with state-of-the-art Bayesian analysis.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Node.js 16+ (for package management)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/sampelit.git
cd sampelit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python scripts/migrate_audit.py

# Start server
python main.py
```

Access the platform at `http://localhost:8000`

---

## 📋 Features

### Core Capabilities
- **Visual Editor**: Point-and-click experiment creation with live preview
- **Multi-Element Testing**: Test multiple page elements simultaneously
- **Adaptive Optimization**: Thompson Sampling for automatic traffic allocation
- **Bayesian Analysis**: Real-time probability calculations and confidence metrics
- **Audit Trail**: Cryptographic hash chain for verifiable fairness
- **Data Export**: CSV/Excel exports with professional formatting

### Advanced Analytics
- Monte Carlo simulation with adaptive sampling
- Wilson confidence intervals
- Expected loss calculations
- Automated recommendations engine

---

## 🏗️ Architecture

### Backend Stack
- **Framework**: FastAPI 0.100+
- **Database**: PostgreSQL 13+ (with asyncpg)
- **Cache**: Redis (optional, falls back to PostgreSQL)
- **Authentication**: JWT with role-based access control

### Frontend Stack
- **Core**: Vanilla JavaScript + Alpine.js 3.x
- **Styling**: Tailwind CSS 3.x (CDN)
- **Charts**: Chart.js 4.x
- **Component System**: Custom `<include>` tag processor

### Directory Structure
```
sampelit/
├── public_api/          # FastAPI routers and models
│   ├── routers/         # API endpoints
│   ├── models/          # Pydantic schemas
│   └── middleware/      # Error handling, rate limiting
├── orchestration/       # Business logic services
│   └── services/        # Analytics, Audit, Experiment services
├── data_access/         # Database layer
├── static/              # Frontend assets
│   ├── js/              # JavaScript modules
│   ├── partials/        # Reusable HTML components
│   └── *.html           # Page templates
├── database/            # SQL schemas and migrations
└── main.py              # Application entry point
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/sampelit

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### Database Setup
```sql
-- Create database
CREATE DATABASE sampelit;

-- Run schema migrations
\i database/schema/schema_phase1_PRODUCTION_READY.sql
\i database/schema/schema_audit.sql
\i database/schema/schema_leads.sql
\i database/schema/migration_01_add_roles.sql
```

---

## 📊 API Documentation

### Authentication
```bash
# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### Experiments
```bash
# Create experiment
POST /api/v1/experiments
Authorization: Bearer {token}
{
  "name": "Homepage CTA Test",
  "url": "https://example.com",
  "elements": [...]
}

# Get analytics
GET /api/v1/analytics/experiment/{id}
Authorization: Bearer {token}

# Export audit trail
GET /api/v1/audit/experiments/{id}/export/csv
Authorization: Bearer {token}
```

Full API documentation: `http://localhost:8000/docs`

---

## 🎨 Frontend Architecture

### Component System
HTML components use custom `<include>` tags:
```html
<include src="./partials/sidebar.html"></include>
```

Processed by `static/js/include.js` at runtime.

### State Management
Global state via `MABApp` singleton:
```javascript
// Initialize
const app = new MABApp();

// API calls
const response = await app.api.get('/experiments');

// UI helpers
app.ui.showToast('Success!', 'success');
```

### Alpine.js Components
```html
<div x-data="experimentResults()" x-init="init()">
  <div x-text="stats.total_visitors"></div>
</div>
```

---

## 🔐 Security

### Authentication Flow
1. User registers/logs in via `/api/v1/auth`
2. Server returns JWT token
3. Frontend stores token in `localStorage`
4. `APIClient` attaches token to all requests
5. Backend validates via `get_current_user` dependency

### Role-Based Access
- **Client**: Standard user, can create/view own experiments
- **Admin**: Full access, can view all users and experiments

### Audit Trail Integrity
- Each decision logged with SHA-256 hash
- Hash chain prevents retroactive tampering
- Timestamps prove decision-before-conversion order

---

## 🧪 Testing

### Manual Testing
```bash
# Start development server
python main.py

# Navigate to Visual Editor
http://localhost:8000/static/visual-editor.html

# Create experiment
1. Enter target URL
2. Click elements to test
3. Add variants
4. Save experiment
```

### Integration Tests
```bash
# Run test suite (when available)
pytest tests/

# Specific test
pytest tests/test_analytics.py -v
```

---

## 📦 Deployment

### Production Checklist
- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong `SECRET_KEY` (32+ characters)
- [ ] Enable HTTPS (configure reverse proxy)
- [ ] Set up PostgreSQL connection pooling
- [ ] Configure Redis for caching
- [ ] Enable rate limiting
- [ ] Set up monitoring (Sentry, DataDog, etc.)

### Docker Deployment
```bash
# Build image
docker build -t sampelit:latest .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e SECRET_KEY=... \
  sampelit:latest
```

### Render.com Deployment
See [`deployment_ops.md`](file:///C:/Users/Artur/.gemini/antigravity/brain/8a137b1c-02f5-4886-8132-955f3e1ead9d/deployment_ops.md) for detailed instructions.

---

## 📚 Additional Documentation

- [Backend Architecture Guide](file:///C:/Users/Artur/.gemini/antigravity/brain/8a137b1c-02f5-4886-8132-955f3e1ead9d/backend_architecture_guide.md)
- [Frontend Architecture Guide](file:///C:/Users/Artur/.gemini/antigravity/brain/8a137b1c-02f5-4886-8132-955f3e1ead9d/frontend_architecture_guide.md)
- [Master Integration Plan](file:///C:/Users/Artur/.gemini/antigravity/brain/8a137b1c-02f5-4886-8132-955f3e1ead9d/master_integration_plan.md)
- [Analytics Walkthrough](file:///C:/Users/Artur/.gemini/antigravity/brain/8a137b1c-02f5-4886-8132-955f3e1ead9d/walkthrough_analytics.md)

---

## 🛠️ Development

### Code Style
- Python: PEP 8 (enforced via Black)
- JavaScript: Standard JS
- SQL: Lowercase keywords, snake_case identifiers

### Git Workflow
```bash
# Feature branch
git checkout -b feature/new-analytics

# Commit
git commit -m "feat: add segment-based analysis"

# Push
git push origin feature/new-analytics
```

### Adding New Endpoints
1. Create router in `public_api/routers/`
2. Define Pydantic models in `public_api/models/`
3. Register router in `main.py`
4. Update API documentation

---

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
pg_isready

# Test connection
psql -U postgres -d sampelit -c "SELECT 1;"
```

### Frontend Not Loading
- Clear browser cache
- Check console for JavaScript errors
- Verify `include.js` is loaded before other scripts

### Audit Trail Errors
```bash
# Verify table exists
psql -d sampelit -c "\dt algorithm_audit_trail"

# Check integrity
SELECT * FROM verify_audit_chain('{experiment_id}', 1, NULL);
```

---

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 📧 Support

- **Email**: support@sampelit.com
- **Documentation**: https://docs.sampelit.com
- **Issues**: https://github.com/yourusername/sampelit/issues

---

**Built with ❤️ by the Sampelit Team**