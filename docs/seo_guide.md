# SEO & Page Titling Guide

> Standards for consistent, SEO-optimized page titles and metadata across Sampelit.

---

## Title Tag Format

### Public Pages
```
[Page Name] | Sampelit - [Tagline/Description]
```

**Examples**:
- `Sampelit | Intelligent A/B Testing for Growth Teams`
- `Pricing | Sampelit - Plans for Every Business`
- `Blog | Sampelit - A/B Testing Insights & Best Practices`

### App Pages
```
[Page/Feature Name] | Sampelit
```

**Examples**:
- `Dashboard | Sampelit`
- `Create Experiment | Sampelit`
- `Analytics: Homepage Test | Sampelit`

### Error Pages
```
[Error Code] - [Message] | Sampelit
```

**Examples**:
- `404 - Page Not Found | Sampelit`
- `500 - Server Error | Sampelit`

---

## Meta Description Guidelines

| Length | 150-160 characters max |
|--------|------------------------|
| Format | Action-oriented, benefit-focused |
| Keywords | Include primary keyword naturally |

**Template**:
```
[Action verb] [benefit/feature]. Sampelit helps [target user] [achieve goal] with [unique value].
```

**Example**:
```html
<meta name="description" content="Run smarter A/B tests with Sampelit. Our visual editor and Bayesian analytics help growth teams optimize conversions without writing code.">
```

---

## Open Graph Tags

Include on all public pages:

```html
<meta property="og:title" content="[Page Title]">
<meta property="og:description" content="[Meta description]">
<meta property="og:image" content="https://sampelit.com/og-image.png">
<meta property="og:url" content="https://sampelit.com/[path]">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
```

---

## URL Structure

| Pattern | Example |
|---------|---------|
| Public pages | `/about`, `/pricing`, `/contact` |
| Blog | `/blog/[slug]` |
| Help Center | `/help-center/[category]/[article-slug]` |
| App pages | `/app/dashboard`, `/app/experiments/[id]` |

**Rules**:
- Lowercase only
- Hyphens for word separation (no underscores)
- No trailing slashes
- Canonical URLs on all pages

---

## Heading Hierarchy

Each page should have exactly **one `<h1>`** tag.

```html
<h1>Main Page Title (matches title tag)</h1>
  <h2>Section heading</h2>
    <h3>Subsection</h3>
  <h2>Another section</h2>
```

---

## Structured Data

### Organization (homepage)
```json
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "Sampelit",
  "applicationCategory": "BusinessApplication",
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
```

### Article (blog posts)
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "[Title]",
  "author": "[Author name]",
  "datePublished": "[ISO date]"
}
```

---

## Checklist for New Pages

- [ ] Unique, descriptive `<title>` tag (50-60 chars)
- [ ] Meta description (150-160 chars)
- [ ] Single `<h1>` matching page purpose
- [ ] Canonical URL
- [ ] Open Graph tags
- [ ] Alt text on all images
- [ ] Internal links to related content
