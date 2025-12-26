# Sampelit Frontend Structure

> Quick reference for developers working on the frontend.

## 📁 Folder Structure

```
static/
├── css/
│   └── sampelit.css       # Centralized design tokens & reusable classes
├── js/
│   ├── include.js         # Handles <include> tags for partials
│   └── theme.js           # Dark mode toggle logic
├── partials/
│   ├── header_landing.html   # Public pages header
│   ├── header.html           # App pages header (Alpine.js)
│   └── footer_landing.html   # Public pages footer
├── components/
│   ├── alerts/            # Success, error, warning, info alerts
│   ├── modals/            # Success, confirm modals
│   ├── metrics/           # Dashboard stat cards
│   └── otp-input.html     # 6-digit verification input
├── help-center/           # Help documentation pages
├── new/                   # ⚠️ STAGING - Work-in-progress pages
│   ├── crm_*.html         # CRM admin pages (being migrated)
│   └── user_demo_*.html   # Algorithm simulator (being migrated)
└── *.html                 # ✅ PRODUCTION pages (index, about, faq, etc.)
```

## 🎨 Design System

### Colors (use CSS variables or Tailwind config)
| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary` | `#0f172a` | Dark navy, buttons, text |
| `--color-accent` | `#1e3a8a` | Interactive elements, links |
| `--color-text-main` | `#1E293B` | Body text |
| `--color-text-muted` | `#64748B` | Secondary text |
| `--color-surface` | `#FAFAFA` | Card backgrounds |
| `--color-border` | `#E2E8F0` | Borders, dividers |

### Fonts
- **Display**: Manrope (headings, bold text)
- **Body**: Inter (paragraphs, UI text)

### Shadows
- `shadow-soft`: Subtle elevation
- `shadow-card`: Card hover states

## 🔧 How to Add a New Page

1. **Create HTML file** in `static/` (or `static/new/` for WIP)
2. **Include Tailwind config** (copy from index.html head section)
3. **Add partials**:
   ```html
   <include src="./partials/header_landing.html"></include>
   <!-- content -->
   <include src="./partials/footer_landing.html"></include>
   ```
4. **Include scripts** before `</body>`:
   ```html
   <script src="js/include.js"></script>
   ```
5. **Use components** - copy from `/components/` folder

## 📦 Include.js

The `include.js` script enables HTML includes:

```html
<include src="./partials/header_landing.html"></include>
```

It also executes inline `<script>` tags within partials.

## 🌙 Dark Mode

- Uses `darkMode: 'class'` Tailwind config
- Toggle adds/removes `dark` class on `<html>`
- Use `dark:` prefix for dark variants: `bg-white dark:bg-gray-900`

## 📋 Staging → Production Workflow

Pages start in `/new/` (staging) and are migrated to `/static/` (production) only when ready:

### Workflow:
1. **Create/modify in `/new/`** - All work happens here first
2. **Apply Sampelit branding** - Title, logo, colors, design tokens
3. **Test thoroughly** - Light/dark mode, responsive, links
4. **Copy to `/static/`** - Only when fully ready
5. **Update paths** - Adjust any relative paths if needed

### Status of `/new/` pages:
| Page | Status | Ready for prod? |
|------|--------|-----------------|
| `crm_dasboard_br.html` | Branding done | ⏳ Testing |
| `crm_dashboard_d.html` | Branding done | ⏳ Testing |
| `crm_*_contactos.html` | Pending | ❌ |
| `user_demo_simulator_*.html` | Pending | ❌ |

> ⚠️ **Do NOT move to production until fully tested!**

## 🔗 Key Files

| File | Purpose |
|------|---------|
| `index.html` | Homepage with design system |
| `css/sampelit.css` | Centralized styles |
| `js/include.js` | HTML includes |
| `partials/header_landing.html` | Public header with dark toggle |
