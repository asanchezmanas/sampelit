# Future Improvements (v2.0+)

> Roadmap of enhancements for future Sampelit versions.

> **Note**: Command Palette, Toast Stack, Skeleton Loaders, Empty States, and Auto-Save were implemented in v2.0. 
> See [Migration Plan](./frontend/migration_plan.md) for the complete **SOTA UX Matrix**.

---

## 1. Visual Editor Robustness

### Firecrawl Integration
**Problem**: Current visual editor may struggle with complex single-page apps (SPAs), shadow DOM, or heavily dynamic frameworks.

**Proposed Solution**: Integrate [Firecrawl](https://firecrawl.dev/) for robust element selection.

**Benefits**:
- Works across any tech stack (React, Vue, Angular, Svelte, etc.)
- Better handling of dynamic content
- More reliable CSS selector generation
- Improved iframe traversal

**Implementation Notes**:
- Use Firecrawl's scraping API to get clean DOM structure
- Parse elements for visual editor overlay
- Generate robust, unique selectors
- Fallback to current implementation if Firecrawl unavailable

---

## 2. Enhanced Analytics

### Bayesian Multi-Armed Bandit
- Auto-optimize traffic allocation during experiment
- Route more traffic to winning variations automatically
- Reduce opportunity cost of testing

### Funnel Analysis
- Multi-step conversion tracking
- Drop-off visualization between steps
- Automatic funnel suggestions based on common paths

### Segmentation
- Post-hoc segment analysis
- Device, geo, referrer breakdowns
- Custom attribute filtering

---

## 3. Advanced Targeting

### Behavioral Targeting
- Target based on user behavior (pages visited, time on site)
- Exclude returning users who already saw experiment
- Session-based rules

### Cookie/Local Storage Targeting
- Read existing cookies for targeting
- Integration with existing user segments

---

## 4. Developer Experience

### SDK v2
- Smaller bundle size (<5KB)
- Tree-shakeable modules
- TypeScript native
- Server-side rendering support

### CLI Tool
- `sampelit init` - setup project
- `sampelit deploy` - push experiments
- `sampelit status` - check running experiments

---

## 5. Collaboration Features

### Comments & Approvals
- Comment on experiments before launch
- Approval workflow for enterprise teams
- Activity feed per experiment

### Templates
- Save experiment configurations as templates
- Share templates across team
- Pre-built templates for common use cases

---

## 6. Infrastructure

### Edge Computing
- Run targeting logic at edge (Cloudflare Workers, Vercel Edge)
- Zero cold-start latency
- Geo-based serving

### Data Pipeline
- Webhook integrations (Zapier, Segment)
- Real-time data streaming to data warehouses
- BigQuery/Snowflake native connectors

---

## 7. SEO & Performance

### Page Titling Optimization
- Implement dynamic titling based on active experiments (canonical handles)
- Automatic meta-description generation for variations
- SSR (Server Side Rendering) friendly tracker for minimal CLS (Cumulative Layout Shift)

### Core Web Vitals Monitoring
- Track impact of experiments on page load speed
- Automatic warning if a variation degrades performance significantly
- LCP (Largest Contentful Paint) optimization for injected images

---

## Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Firecrawl Visual Editor | High | Medium | P1 |
| CLI Tool | Medium | Low | P2 |
| Bayesian MAB | High | High | P2 |
| Edge Computing | High | High | P2 |
| Comments & Approvals | Medium | Medium | P3 |
| SDK v2 | Medium | High | P3 |
