# Sampelit UI Components

Reusable UI components migrated from `_template_archive` with Sampelit branding and dual-theme support.

## Usage

Copy the HTML snippets into your pages. All components support:
- ✅ Light mode (default)
- ✅ Dark mode (via `dark:` classes)
- ✅ Responsive design

## Components

### Alerts (`/alerts/`)
| File | Purpose |
|------|---------|
| `alert-success.html` | ✅ Success messages (green) |
| `alert-error.html` | ❌ Error messages (red) |
| `alert-warning.html` | ⚠️ Warning messages (yellow) |
| `alert-info.html` | ℹ️ Info messages (blue) |

### Modals (`/modals/`)
| File | Purpose |
|------|---------|
| `modal-success.html` | Success confirmation with badge icon |
| `modal-confirm.html` | Destructive action confirmation |

> **Note**: Modals require Alpine.js for `x-show` and `x-data`.

### Metrics (`/metrics/`)
| File | Purpose |
|------|---------|
| `metric-cards.html` | Dashboard stat cards with trend indicators |

### Other
| File | Purpose |
|------|---------|
| `otp-input.html` | 6-digit verification code input |

## Dependencies

- **Tailwind CSS** - Core styling
- **Alpine.js** - Modal interactivity (optional)
- **JavaScript** - OTP input auto-focus (included inline)

## Dark Mode

Components automatically adapt when `<html class="dark">` is set.
