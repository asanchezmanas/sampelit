# Visual Editor Guide

> **Sampelit A/B Testing Platform**  
> Create experiments without writing code

---

## Table of Contents

1. [Overview](#overview)
2. [Accessing the Visual Editor](#accessing-the-visual-editor)
3. [The Editor Interface](#the-editor-interface)
4. [Selecting Elements](#selecting-elements)
5. [Creating Variations](#creating-variations)
6. [Editing Content](#editing-content)
7. [Advanced Editing](#advanced-editing)
8. [Saving and Launching](#saving-and-launching)
9. [Tips and Best Practices](#tips-and-best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Visual Editor is a point-and-click tool that lets you create A/B test variations without writing code. Simply load your website, click on elements, and modify them visually.

### Key Features

- **Point-and-click selection**: Click any element to select it
- **Live preview**: See changes in real-time
- **Multiple element testing**: Test several elements at once
- **CSS/HTML editing**: For advanced customization
- **Undo/Redo**: Easily revert changes

---

## Accessing the Visual Editor

### From the Dashboard

1. Click **Visual Editor** in the sidebar
2. Or go to **Experiments** → **Create New** → **Use Visual Editor**

### Enter Your Page URL

1. In the input field, enter the URL you want to test:
   ```
   https://yoursite.com/landing-page
   ```
2. Click **Load Page**
3. Wait for your page to load in the editor frame

---

## The Editor Interface

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VISUAL EDITOR                                         [Save] [Cancel] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐  ┌─────────────────────────────────────────────┐  │
│  │ ELEMENTS        │  │                                             │  │
│  │                 │  │      [Your Website Preview]                  │  │
│  │ • Headline      │  │                                             │  │
│  │ • CTA Button    │  │   ┌─────────────────────────────┐           │  │
│  │ • Hero Image    │  │   │ Welcome to Our Site        │           │  │
│  │                 │  │   │                             │           │  │
│  │ [+ Add Element] │  │   │ [Get Started] ← selected   │           │  │
│  │                 │  │   │                             │           │  │
│  ├─────────────────┤  │   └─────────────────────────────┘           │  │
│  │ VARIATIONS      │  │                                             │  │
│  │                 │  │                                             │  │
│  │ ○ Control       │  │                                             │  │
│  │ ● Variant A     │  │                                             │  │
│  │ ○ Variant B     │  │                                             │  │
│  │                 │  │                                             │  │
│  │ [+ Add Variant] │  │                                             │  │
│  │                 │  │                                             │  │
│  ├─────────────────┤  └─────────────────────────────────────────────┘  │
│  │ EDIT PANEL      │                                                   │
│  │                 │                                                   │
│  │ Text: [Buy Now]│                                                   │
│  │ Color: [Green] │                                                   │
│  │ Size:  [Large] │                                                   │
│  │                 │                                                   │
│  │ [CSS] [HTML]   │                                                   │
│  └─────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Panel Breakdown

| Panel | Purpose |
|-------|---------|
| **Elements** | List of elements you're testing |
| **Variations** | Different versions for each element |
| **Preview** | Live view of your website |
| **Edit Panel** | Modify the selected element |

---

## Selecting Elements

### Click to Select

1. Move your mouse over the page preview
2. Elements become highlighted as you hover
3. Click to select an element

### Selection Indicators

- **Blue dashed outline**: Hover state
- **Blue solid outline**: Selected element
- **Blue glow**: Currently editing

### What You Can Select

✅ **Recommended for testing**:
- Headlines (H1, H2, H3)
- Buttons
- Call-to-action links
- Images
- Form elements
- Text paragraphs
- Entire sections

⚠️ **Use caution with**:
- Navigation menus
- Footer elements
- Third-party widgets
- Dynamically loaded content

### CSS Selector Display

When you select an element, you'll see its CSS selector:

```
Selector: button.cta-primary
Type: Button
```

This helps you understand exactly what you're modifying.

---

## Creating Variations

### Adding Your First Variation

1. Select an element
2. Click **+ Add Variation** in the Variations panel
3. A new variation (Variant A) is created

### Naming Variations

By default, variations are named:
- Control (original)
- Variant A
- Variant B
- Variant C
- etc.

To rename:
1. Double-click the variation name
2. Enter a descriptive name (e.g., "Orange Button", "Shorter Headline")
3. Press Enter

### Switching Between Variations

- Click on a variation name to switch to it
- The preview updates to show that variation
- Make edits while viewing any variation

### Deleting Variations

1. Hover over the variation
2. Click the **×** icon
3. Confirm deletion

> **Note**: You cannot delete the Control variation.

---

## Editing Content

### Text Editing

1. Select a text element
2. In the Edit Panel, modify the text field
3. Press Enter or click outside to apply

**Example**:
```
Original: "Sign Up Now"
Variant A: "Get Started Free"
Variant B: "Join Today"
```

### Button Styling

For buttons, you can modify:

| Property | Example Values |
|----------|----------------|
| **Text** | "Buy Now", "Add to Cart" |
| **Color** | #3B82F6 (blue), #10B981 (green) |
| **Size** | Small, Medium, Large |
| **Border** | Rounded, Square, Pill |

### Image Swapping

1. Select an image
2. In the Edit Panel, click **Change Image**
3. Upload a new image or enter a URL
4. Adjust sizing if needed

### Hiding Elements

To test removing an element:

1. Select the element
2. Click **Hide Element**
3. The element is hidden for this variation

---

## Advanced Editing

### Custom CSS

For precise styling control:

1. Select an element
2. Click the **CSS** tab in the Edit Panel
3. Add custom CSS:

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: white;
padding: 16px 32px;
border-radius: 8px;
font-weight: bold;
text-transform: uppercase;
```

4. Click **Apply**

### Custom HTML

To completely replace an element:

1. Select an element
2. Click the **HTML** tab
3. Edit the HTML:

```html
<button class="cta-primary">
  <span class="icon">🚀</span>
  <span class="text">Launch Your Project</span>
</button>
```

4. Click **Apply**

### Using Custom JavaScript

For dynamic variations (advanced):

1. Click **Code Editor** mode
2. Add JavaScript:

```javascript
// Change button text based on time of day
const hour = new Date().getHours();
const button = document.querySelector('.cta-primary');
if (hour < 12) {
    button.textContent = "Good Morning! Get Started";
} else {
    button.textContent = "Start Your Journey";
}
```

---

## Saving and Launching

### Saving Your Experiment

1. Review all variations by clicking through them
2. Click **Save** in the top-right corner
3. Enter experiment details:
   - **Name**: Descriptive name for your test
   - **Traffic Allocation**: Percentage of visitors who see the test
   - **Goals**: What counts as a conversion

### Preview Mode

Before launching:

1. Click **Preview**
2. Test each variation in a new tab
3. Check on different devices (desktop, mobile)

### Launching

1. Click **Launch Experiment**
2. Confirm your settings
3. The experiment goes live immediately

### Post-Launch

- View real-time data in the results dashboard
- You cannot edit variations after launching
- You can pause or stop the experiment anytime

---

## Tips and Best Practices

### Design Tips

| ✅ Do | ❌ Don't |
|-------|---------|
| Test one element type at a time | Change everything at once |
| Use clear, readable fonts | Make text too small |
| Maintain brand consistency | Stray too far from your style |
| Keep CTAs above the fold | Hide important elements |
| Test on mobile too | Only check desktop |

### Selection Tips

1. **Be specific**: Select the exact element, not a parent container
2. **Check the selector**: Verify the CSS selector matches what you intended
3. **Test dynamically loaded content**: Wait for the page to fully load

### Variation Tips

1. **Start small**: 2-3 variations is usually optimal
2. **Make meaningful changes**: Subtle tweaks may not show significant results
3. **Keep notes**: Document what each variation is testing

### Performance Tips

- Large images slow down loading—optimize them
- Avoid too many variations (splits traffic too thin)
- Complex JavaScript may cause flicker

---

## Troubleshooting

### Issue: Page Not Loading

**Possible causes**:
- URL is incorrect
- Site blocks iframes
- SSL/HTTPS issues

**Solutions**:
1. Verify the URL is correct and accessible
2. Check if your site has X-Frame-Options restrictions
3. Ensure the URL uses HTTPS

### Issue: Can't Select Elements

**Possible causes**:
- Element is inside an iframe
- Element is dynamically generated
- JavaScript prevents selection

**Solutions**:
1. Wait for the page to fully load
2. Try selecting a parent element
3. Use the CSS Selector input instead of clicking

### Issue: Changes Not Showing

**Possible causes**:
- Cache is serving old version
- JavaScript error preventing injection
- Selector is too specific

**Solutions**:
1. Hard refresh your page (Ctrl+Shift+R)
2. Check browser console for errors
3. Use a more general CSS selector

### Issue: Flicker on Page Load

**What is flicker?**: Visitors briefly see the original before the variation loads.

**Solutions**:
1. Add anti-flicker snippet (provided in Installations)
2. Ensure tracker loads early in `<head>`
3. Minimize heavy JavaScript in variations

### Issue: Editor Shows Error Message

If you see "Proxy Error":
1. The target site may be blocking requests
2. Check if the site requires authentication
3. Try a different page on your site

---

## FAQ

### Can I test elements in the header/footer?

Yes, but be cautious. Header/footer elements may affect many pages. Consider testing on a specific page first.

### How many elements can I test at once?

Technically unlimited, but we recommend 1-3 elements per experiment for cleaner data.

### Can I test on mobile specifically?

Currently, the Visual Editor shows the desktop view. For mobile-specific tests, use device targeting in experiment settings.

### Will changes affect my live site?

Only for visitors who are part of the experiment. Your actual website code is unchanged.

### How do I edit the same element on multiple pages?

Create a separate experiment for each page, or use URL pattern matching in advanced settings.

---

## Support

Need help with the Visual Editor?

- 📖 **Knowledge Base**: [help.Sampelit.com](https://help.Sampelit.com)
- 📧 **Email**: support@Sampelit.com
- 💬 **Live Chat**: Available in dashboard

---

*Create, test, optimize—no code required.*
