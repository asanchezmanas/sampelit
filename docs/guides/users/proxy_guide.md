# Proxy Middleware Integration Guide

> **Samplit A/B Testing Platform**  
> Automatic tracker injection for any web application

---

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Integration Methods](#integration-methods)
7. [Testing Your Integration](#testing-your-integration)
8. [Troubleshooting](#troubleshooting)
9. [Performance Considerations](#performance-considerations)
10. [FAQ](#faq)

---

## Overview

The Proxy Middleware allows you to automatically inject the Samplit A/B testing tracker into your HTML pages without modifying your application code. This is the ideal solution when you want to add A/B testing capabilities to an existing website or application with minimal changes.

### Key Benefits

- **Zero code changes**: No need to modify your existing HTML or JavaScript
- **Automatic injection**: The tracker is injected into every HTML response
- **High performance**: Uses optimized regex-based injection (5-10ms for 1MB HTML)
- **Connection pooling**: Efficient resource management for high-traffic sites
- **Error resilient**: Graceful fallback if injection fails

---

## How It Works

```
┌──────────────┐      ┌─────────────────────┐      ┌──────────────────┐
│              │      │                     │      │                  │
│   Browser    │─────▶│   Proxy Middleware  │─────▶│   Your Server    │
│              │      │                     │      │                  │
└──────────────┘      └─────────────────────┘      └──────────────────┘
       ▲                       │
       │                       │
       │    ┌──────────────────┘
       │    │
       │    ▼
       │  ┌─────────────────────────────────┐
       │  │  HTML Response + Tracker Script │
       │  └─────────────────────────────────┘
       │                 │
       └─────────────────┘
```

1. Browser requests a page through the proxy
2. Proxy forwards the request to your origin server
3. Origin server returns the HTML response
4. Proxy injects the Samplit tracker script into the HTML
5. Modified HTML is returned to the browser

---

## Prerequisites

Before you begin, ensure you have:

- [ ] Python 3.8 or higher installed
- [ ] A Samplit account with an active installation token
- [ ] Access to modify your server configuration or DNS settings
- [ ] The following Python packages:
  - `starlette`
  - `httpx`
  - `uvicorn` (for running the server)

---

## Installation

### Step 1: Install Required Packages

```bash
pip install starlette httpx uvicorn
```

### Step 2: Create Your Proxy Server

Create a new file called `proxy_server.py`:

```python
from fastapi import FastAPI, Request
from starlette.responses import Response
from integration.proxy import ProxyMiddleware

app = FastAPI()

# Initialize the proxy middleware
proxy = ProxyMiddleware(
    api_url="https://api.samplit.com",
    timeout=30,
    max_connections=100
)

@app.get("/{path:path}")
async def proxy_request(request: Request, path: str):
    """
    Proxy all requests and inject the tracker
    """
    # Your installation token from Samplit dashboard
    installation_token = "YOUR_INSTALLATION_TOKEN"
    
    # Original URL to proxy
    original_url = f"https://your-origin-server.com/{path}"
    
    return await proxy.process_request(
        request=request,
        installation_token=installation_token,
        original_url=original_url
    )

@app.on_event("shutdown")
async def shutdown():
    await proxy.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Step 3: Run the Proxy Server

```bash
python proxy_server.py
```

Your proxy is now running on `http://localhost:8000`.

---

## Configuration

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_url` | string | Required | The Samplit API endpoint |
| `timeout` | integer | 30 | Request timeout in seconds |
| `max_connections` | integer | 100 | Maximum concurrent connections to origin |

### Environment Variables

We recommend using environment variables for sensitive configuration:

```bash
export SAMPLIT_API_URL="https://api.samplit.com"
export SAMPLIT_INSTALLATION_TOKEN="your_token_here"
export ORIGIN_SERVER_URL="https://your-origin-server.com"
```

Then in your code:

```python
import os

proxy = ProxyMiddleware(
    api_url=os.getenv("SAMPLIT_API_URL"),
    timeout=30,
    max_connections=100
)

installation_token = os.getenv("SAMPLIT_INSTALLATION_TOKEN")
origin_url = os.getenv("ORIGIN_SERVER_URL")
```

---

## Integration Methods

### Method 1: Standalone Proxy Server

Best for: New deployments, development/staging environments

Set up the proxy as a standalone service that sits between your users and your origin server.

```
User → Proxy Server (port 80/443) → Origin Server (internal)
```

### Method 2: FastAPI/Starlette Middleware

Best for: Existing FastAPI or Starlette applications

Add the middleware directly to your existing application:

```python
from fastapi import FastAPI
from integration.proxy import ProxyMiddleware

app = FastAPI()

# Add as middleware
@app.middleware("http")
async def inject_tracker(request, call_next):
    proxy = ProxyMiddleware(api_url="https://api.samplit.com")
    
    # Check for installation token header
    if request.headers.get("X-Samplit-Installation-Token"):
        return await proxy.dispatch(request, call_next)
    
    return await call_next(request)
```

### Method 3: Reverse Proxy Configuration (Nginx)

Best for: Production deployments with existing Nginx setup

Configure Nginx to route traffic through your proxy:

```nginx
upstream proxy_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://proxy_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Testing Your Integration

### Step 1: Verify Proxy is Running

```bash
curl -I http://localhost:8000/
```

You should receive a response from your origin server.

### Step 2: Check Tracker Injection

```bash
curl http://localhost:8000/ | grep "Samplit"
```

You should see the Samplit tracker script in the HTML:

```html
<!-- Samplit A/B Testing Tracker -->
<script>
(function() {
    window.SAMPLIT_CONFIG = {
        installationToken: 'your_token',
        apiEndpoint: 'https://api.samplit.com/api/v1/tracker'
    };
})();
</script>
<script src="https://api.samplit.com/static/tracker/t.js?token=your_token" async></script>
<!-- End Samplit Tracker -->
```

### Step 3: Verify in Browser

1. Open your proxied site in a browser
2. Open Developer Tools (F12)
3. Go to the Network tab
4. Look for `t.js` being loaded
5. Check the Console for any errors

### Step 4: Test in Samplit Dashboard

1. Log into your Samplit dashboard
2. Go to "Installations" → Your installation
3. Check "Live Status" — should show "Connected"
4. Create a test experiment to verify everything works

---

## Troubleshooting

### Common Issues

#### Issue: Tracker not appearing in HTML

**Possible causes:**
- Response is not HTML (check Content-Type header)
- HTML doesn't have `<head>` or `<body>` tags
- Proxy is not receiving requests

**Solution:**
```bash
# Check the Content-Type of your response
curl -I http://localhost:8000/ | grep -i content-type

# Should show: Content-Type: text/html
```

#### Issue: 502 Bad Gateway Error

**Possible causes:**
- Origin server is unreachable
- Timeout exceeded
- Connection refused

**Solution:**
```bash
# Test direct connection to origin
curl -I https://your-origin-server.com/

# Increase timeout if needed
proxy = ProxyMiddleware(
    api_url="https://api.samplit.com",
    timeout=60,  # Increase from 30 to 60
    max_connections=100
)
```

#### Issue: Slow page load times

**Possible causes:**
- High latency to origin server
- Connection pool exhausted
- Large HTML files

**Solution:**
```python
# Increase connection pool
proxy = ProxyMiddleware(
    api_url="https://api.samplit.com",
    timeout=30,
    max_connections=200  # Increase from 100
)
```

#### Issue: Character encoding problems

**Possible causes:**
- Non-UTF-8 encoded pages
- Missing charset declaration

**Solution:**
The proxy automatically falls back to latin-1 encoding. If issues persist, check your origin server's charset configuration.

---

## Performance Considerations

### Injection Performance

| Method | Time (1MB HTML) | Use Case |
|--------|-----------------|----------|
| Regex (default) | 5-10ms | Production |
| BeautifulSoup | 100-300ms | Complex DOM manipulation only |

### Recommended Settings by Traffic Level

| Daily Traffic | max_connections | timeout | Notes |
|---------------|-----------------|---------|-------|
| < 10,000 | 50 | 30 | Default settings work fine |
| 10,000 - 100,000 | 100 | 30 | Standard configuration |
| 100,000 - 1M | 200 | 20 | Consider multiple proxy instances |
| > 1M | 500+ | 15 | Use load balancer with multiple proxies |

### Connection Pooling

The proxy uses connection pooling to efficiently manage connections to your origin server:

```python
# Default pool settings
limits=httpx.Limits(
    max_connections=100,        # Total connections
    max_keepalive_connections=20  # Keep-alive connections
)
```

---

## FAQ

### Can I use this with HTTPS?

Yes! Configure SSL termination at your reverse proxy (Nginx, Cloudflare, etc.) and have the proxy communicate with your origin over HTTPS.

### What happens if the proxy fails?

The proxy is designed to be resilient. If injection fails, it returns the original response unchanged. Your site will continue to work, just without A/B testing.

### Does this work with SPAs (Single Page Applications)?

The proxy injects the tracker on initial page load. For SPAs, the tracker will be present and will handle route changes automatically.

### Can I exclude certain pages from tracking?

Yes, modify your proxy logic:

```python
@app.get("/{path:path}")
async def proxy_request(request: Request, path: str):
    # Skip tracker for admin pages
    if path.startswith("admin/"):
        # Proxy without injection
        return await forward_without_injection(request, path)
    
    # Normal proxy with injection
    return await proxy.process_request(...)
```

### How do I update the installation token?

Simply update the environment variable and restart the proxy:

```bash
export SAMPLIT_INSTALLATION_TOKEN="new_token_here"
# Restart your proxy server
```

---

## Support

If you encounter issues not covered in this guide:

1. Check our [Knowledge Base](https://help.samplit.com)
2. Contact support at support@samplit.com
3. Join our [Discord Community](https://discord.gg/samplit)

---

*Last updated: 2024*