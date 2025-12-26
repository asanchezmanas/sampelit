# WordPress Integration Guide

> **Samplit A/B Testing Platform**  
> Complete integration guide for WordPress websites

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Integration Options](#integration-options)
4. [WordPress.com Integration](#wordpresscom-integration)
5. [Self-Hosted WordPress Integration](#self-hosted-wordpress-integration)
6. [OAuth Authentication](#oauth-authentication)
7. [Webhook Configuration](#webhook-configuration)
8. [Running Experiments](#running-experiments)
9. [WooCommerce Integration](#woocommerce-integration)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Overview

The Samplit WordPress integration allows you to run A/B tests on your WordPress website with automatic tracking and real-time webhooks. This integration supports both WordPress.com hosted sites and self-hosted WordPress installations.

### What You Can Test

- Homepage layouts and hero sections
- Blog post titles and featured images
- Call-to-action buttons and forms
- Navigation menus and sidebars
- Landing page variations
- WooCommerce product pages (with WooCommerce add-on)
- Checkout flows (WooCommerce)
- Pricing page variations

### Key Features

- **OAuth 2.0 authentication**: Secure, no passwords stored
- **Real-time webhooks**: Instant tracking of content changes
- **WooCommerce support**: Full e-commerce conversion tracking
- **Theme-agnostic**: Works with any WordPress theme
- **Gutenberg compatible**: Works with block editor

---

## Prerequisites

Before starting, ensure you have:

### For WordPress.com:

- [ ] WordPress.com account (Free, Personal, Premium, or Business)
- [ ] Admin access to your WordPress.com site
- [ ] A Samplit account

### For Self-Hosted WordPress:

- [ ] WordPress 5.0 or higher
- [ ] PHP 7.4 or higher
- [ ] Admin access to WordPress dashboard
- [ ] Ability to install plugins
- [ ] SSL certificate (HTTPS) - recommended
- [ ] A Samplit account

---

## Integration Options

Choose the integration method that matches your WordPress setup:

| Your Setup | Integration Method | Recommended For |
|------------|-------------------|-----------------|
| WordPress.com | OAuth Connect | WordPress.com hosted sites |
| Self-Hosted | Plugin Install | Full control, WooCommerce |
| Self-Hosted | Manual Script | Minimal footprint |

---

## WordPress.com Integration

### Step 1: Initiate Connection

1. Log into [Samplit Dashboard](https://app.samplit.com)
2. Go to **Integrations** → **Add Integration**
3. Select **WordPress**
4. Choose **WordPress.com**
5. Click **Connect with WordPress.com**

### Step 2: Authorize Application

You'll be redirected to WordPress.com to authorize:

1. Log into your WordPress.com account if prompted
2. Review the permissions requested:
   - Read your sites
   - Manage your posts
   - Access site settings
3. Click **Approve**

### Step 3: Select Your Site

If you have multiple sites, select which one to connect:

1. Choose your site from the dropdown
2. Click **Connect This Site**

### Step 4: Verify Installation

After connection, verify in Samplit:

- ✅ Site connected: [yoursite.wordpress.com]
- ✅ Tracker installed
- ✅ Webhooks configured

---

## Self-Hosted WordPress Integration

For self-hosted WordPress installations, you have two options:

### Option A: Plugin Installation (Recommended)

#### Step 1: Download the Plugin

1. Log into Samplit Dashboard
2. Go to **Integrations** → **WordPress**
3. Click **Download Plugin**
4. Save `samplit-ab-testing.zip` to your computer

#### Step 2: Install the Plugin

**Method 1: WordPress Admin Upload**

1. Log into your WordPress admin
2. Go to **Plugins** → **Add New** → **Upload Plugin**
3. Choose the `samplit-ab-testing.zip` file
4. Click **Install Now**
5. Click **Activate Plugin**

**Method 2: FTP Upload**

1. Extract the zip file
2. Upload the `samplit-ab-testing` folder to `/wp-content/plugins/`
3. Go to **Plugins** in WordPress admin
4. Find "Samplit A/B Testing" and click **Activate**

#### Step 3: Configure the Plugin

1. Go to **Settings** → **Samplit A/B Testing**
2. Enter your **Installation Token** (from Samplit dashboard)
3. Enter your **API Endpoint**: `https://api.samplit.com`
4. Click **Save Settings**

#### Step 4: Verify Installation

1. Click **Test Connection**
2. You should see: "✅ Connection successful!"
3. Visit your site and check page source for:

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

### Option B: Manual Script Installation

For minimal footprint or custom setups:

#### Step 1: Get Your Tracker Code

1. Log into Samplit Dashboard
2. Go to **Integrations** → **WordPress** → **Manual Install**
3. Copy the tracker code snippet

#### Step 2: Add to Theme

**Method 1: Theme Header (header.php)**

1. Go to **Appearance** → **Theme Editor**
2. Select `header.php`
3. Paste the tracker code before `</head>`
4. Click **Update File**

**Method 2: Using a Plugin**

Install "Insert Headers and Footers" plugin:

1. **Plugins** → **Add New** → Search "Insert Headers and Footers"
2. Install and activate
3. Go to **Settings** → **Insert Headers and Footers**
4. Paste tracker code in "Scripts in Header"
5. Save

**Method 3: Child Theme (Recommended)**

For theme update safety:

1. Create a child theme if you don't have one
2. Add to your child theme's `functions.php`:

```php
function samplit_add_tracker() {
    ?>
    <!-- Samplit A/B Testing Tracker -->
    <script>
    (function() {
        window.SAMPLIT_CONFIG = {
            installationToken: 'YOUR_TOKEN_HERE',
            apiEndpoint: 'https://api.samplit.com/api/v1/tracker'
        };
    })();
    </script>
    <script src="https://api.samplit.com/static/tracker/t.js?token=YOUR_TOKEN_HERE" async></script>
    <!-- End Samplit Tracker -->
    <?php
}
add_action('wp_head', 'samplit_add_tracker');
```

---

## OAuth Authentication

### Understanding the OAuth Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Samplit App    │────▶│  WordPress.com  │────▶│   Your Site     │
│                 │     │   OAuth Server  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │  1. Auth Request      │                       │
         │──────────────────────▶│                       │
         │                       │                       │
         │                       │  2. User Login        │
         │                       │◀─────────────────────▶│
         │                       │                       │
         │  3. Auth Code         │                       │
         │◀──────────────────────│                       │
         │                       │                       │
         │  4. Exchange Token    │                       │
         │──────────────────────▶│                       │
         │                       │                       │
         │  5. Access Token      │                       │
         │◀──────────────────────│                       │
```

### CSRF Protection

The integration uses state tokens for CSRF protection:

- A unique state token is generated for each OAuth request
- The token is verified when you return from WordPress
- This prevents authorization code injection attacks

### Token Security

- Tokens are encrypted at rest
- Tokens are transmitted only over HTTPS
- Tokens can be revoked at any time
- We don't store your WordPress password

### Revoking Access

**From Samplit:**

1. Dashboard → Integrations → WordPress
2. Click **Disconnect**

**From WordPress.com:**

1. Go to [WordPress.com Settings](https://wordpress.com/me/security/connected-applications)
2. Find "Samplit A/B Testing"
3. Click **Revoke Access**

---

## Webhook Configuration

### Automatic Webhook Registration

When using the plugin or OAuth connection, webhooks are registered automatically for:

| Event | Triggered When | Purpose |
|-------|----------------|---------|
| `post_published` | New post goes live | Track content experiments |
| `page_updated` | Page is modified | Sync experiment variations |
| `comment_posted` | New comment added | Engagement tracking |
| `user_registered` | New user signs up | Conversion tracking |

### Manual Webhook Setup (Self-Hosted)

If using manual installation, configure webhooks:

#### Step 1: Create Webhook Endpoint

Add to your theme's `functions.php` or plugin:

```php
add_action('rest_api_init', function() {
    register_rest_route('samplit/v1', '/webhook', array(
        'methods' => 'POST',
        'callback' => 'samplit_handle_webhook',
        'permission_callback' => '__return_true'
    ));
});

function samplit_handle_webhook($request) {
    $payload = $request->get_body();
    $signature = $request->get_header('X-Signature');
    
    // Verify signature
    if (!samplit_verify_signature($payload, $signature)) {
        return new WP_REST_Response('Invalid signature', 401);
    }
    
    // Process webhook
    $data = json_decode($payload, true);
    
    // Forward to Samplit
    wp_remote_post('https://api.samplit.com/webhooks/wordpress', array(
        'body' => $payload,
        'headers' => array('Content-Type' => 'application/json')
    ));
    
    return new WP_REST_Response('OK', 200);
}
```

#### Step 2: Configure WordPress Hooks

```php
// Post published webhook
add_action('publish_post', function($post_id) {
    $post = get_post($post_id);
    samplit_send_webhook('post_published', array(
        'post_id' => $post_id,
        'title' => $post->post_title,
        'url' => get_permalink($post_id)
    ));
});

// Page updated webhook
add_action('save_post_page', function($post_id) {
    samplit_send_webhook('page_updated', array(
        'page_id' => $post_id,
        'url' => get_permalink($post_id)
    ));
});
```

### Webhook Signature Verification

All webhooks are signed using HMAC-SHA256. Always verify before processing:

```php
function samplit_verify_signature($payload, $signature) {
    $secret = get_option('samplit_client_secret');
    
    if (empty($secret) || empty($signature)) {
        return false;
    }
    
    // Handle "sha256=" prefix if present
    if (strpos($signature, '=') !== false) {
        list(, $signature) = explode('=', $signature, 2);
    }
    
    $expected = hash_hmac('sha256', $payload, $secret);
    
    return hash_equals($expected, $signature);
}
```

> ⚠️ **Security**: Always verify webhook signatures BEFORE parsing the payload. Never trust unverified webhooks.

---

## Running Experiments

### Creating an Experiment

1. **Log into Samplit Dashboard**
   
2. **Go to Experiments → Create New**

3. **Select Your WordPress Site**

4. **Choose Experiment Type**:
   - **Visual Editor**: Point-and-click changes
   - **Code Editor**: HTML/CSS/JS modifications
   - **Split URL**: Test different pages

5. **Set Targeting Rules**:

   | Rule Type | Example |
   |-----------|---------|
   | URL Match | `/blog/*` |
   | Device | Mobile only |
   | Referrer | From Google |
   | Cookie | `returning_visitor=true` |
   | Time | Weekdays only |

6. **Create Variations**:

   Example: Testing a CTA button:
   
   | Variation | Button Text | Color |
   |-----------|-------------|-------|
   | Control | "Learn More" | Blue |
   | Variant A | "Get Started" | Green |
   | Variant B | "Try Free" | Orange |

7. **Set Goals**:
   - Click on button
   - Form submission
   - Page view
   - Custom event

8. **Launch**

### WordPress-Specific Tips

#### Testing Blog Post Titles

1. Create your variations in Samplit
2. Use the visual editor to modify `<h1>` or `.entry-title`
3. Set goal: Time on page, scroll depth, or share clicks

#### Testing Sidebar Widgets

1. Target specific page types (archive, single, page)
2. Use code editor to inject/modify widget HTML
3. Track clicks or conversions

#### Testing Theme Elements

1. Use CSS selectors specific to your theme
2. Test one element at a time
3. Consider mobile vs desktop variations

---

## WooCommerce Integration

If you're running WooCommerce, additional tracking is available.

### Enable WooCommerce Tracking

1. **Samplit Dashboard** → **Integrations** → **WordPress**
2. Click **Settings**
3. Enable **WooCommerce Tracking**
4. Save

### Tracked Events

| Event | Triggered | Use For |
|-------|-----------|---------|
| `product_viewed` | Product page visit | Awareness |
| `add_to_cart` | Add to cart click | Intent |
| `checkout_started` | Checkout page | Funnel |
| `order_completed` | Order placed | Conversion |
| `coupon_applied` | Coupon used | Promotions |

### WooCommerce Experiments

You can test:

- Product page layouts
- Add to cart button text/color
- Product image galleries
- Related products sections
- Checkout form fields
- Cart page design
- Upsell/cross-sell widgets

### Revenue Attribution

Orders are attributed to experiments automatically:

1. User enters experiment variation
2. User's variation is stored in session/cookie
3. When order is placed, conversion is attributed
4. Revenue is calculated from order total

View revenue data in:

**Experiments → [Your Experiment] → Results → Revenue**

---

## Troubleshooting

### Common Issues

#### Issue: Tracker not loading

**Symptoms**: No Samplit script in page source

**Solutions**:

1. **Plugin method**: 
   - Verify plugin is activated
   - Check Settings → Samplit for correct token
   - Clear all caches (WordPress, hosting, CDN)

2. **Manual method**:
   - Verify code is in header.php before `</head>`
   - Check for PHP errors in error log
   - Ensure no caching is serving old pages

3. **Check for conflicts**:
   ```javascript
   // In browser console
   console.log(window.SAMPLIT_CONFIG);
   // Should show your configuration
   ```

#### Issue: OAuth fails with "Invalid state"

**Cause**: CSRF token mismatch

**Solutions**:
1. Clear browser cookies
2. Try in incognito mode
3. Ensure system time is correct
4. Try a different browser

#### Issue: Webhooks not receiving events

**Symptoms**: Changes not reflected in Samplit

**Solutions**:

1. **Verify webhook URL**:
   - Must be HTTPS
   - Must be publicly accessible
   - Test with: `curl -X POST https://your-webhook-url`

2. **Check signature**:
   - Verify client secret is correct
   - Ensure payload isn't being modified

3. **Check logs**:
   ```php
   // Add to webhook handler temporarily
   error_log('Webhook received: ' . print_r($payload, true));
   ```

#### Issue: Visual editor not loading site

**Cause**: X-Frame-Options or CSP blocking

**Solutions**:

1. Add to `.htaccess`:
   ```apache
   Header set X-Frame-Options "ALLOW-FROM https://app.samplit.com"
   ```

2. Or in WordPress:
   ```php
   remove_action('admin_init', 'send_frame_options_header');
   ```

#### Issue: Experiments not showing to visitors

**Possible causes**:

1. **Traffic allocation**: Check percentage is > 0%
2. **Targeting rules**: Verify rules match test conditions
3. **Caching**: Disable page cache during testing
4. **JavaScript errors**: Check browser console

### Debug Mode

Enable debug mode for troubleshooting:

**Plugin Settings → Advanced → Enable Debug Mode**

This will:
- Log all tracker events to browser console
- Show experiment assignments
- Display API requests/responses

To view: Open browser DevTools → Console → Filter by "Samplit"

### Checking Installation Health

Verify your integration:

**Samplit Dashboard → Integrations → WordPress → Health**

| Check | Status | Action if Failed |
|-------|--------|------------------|
| API Connection | ✅ / ❌ | Verify token/credentials |
| Tracker Loading | ✅ / ❌ | Check script injection |
| Webhooks Active | ✅ / ❌ | Re-register webhooks |
| Last Data Received | Timestamp | Verify tracking works |

---

## FAQ

### Which WordPress version is supported?

WordPress 5.0 and higher. We recommend keeping WordPress updated to the latest version.

### Does this work with page builders?

Yes! The tracker works with:
- Gutenberg (Block Editor)
- Elementor
- Divi
- Beaver Builder
- WPBakery
- And others

### Will this slow down my site?

No. The tracker script:
- Loads asynchronously (doesn't block rendering)
- Is less than 10KB gzipped
- Uses a global CDN for fast delivery

### Can I use this with caching plugins?

Yes, with configuration:

**WP Super Cache / W3 Total Cache / WP Rocket:**
- Exclude the Samplit cookie from cache
- Or disable page caching for experiment pages

### Does it work with WordPress multisite?

Yes! Install the plugin network-wide or per-site. Each site needs its own installation token.

### How do I test on staging before production?

1. Create a separate Samplit project for staging
2. Use that project's token on staging site
3. Test experiments completely
4. Use production token on live site

### Can I export my experiment data?

Yes! Go to Experiments → Select experiment → Export (CSV/JSON)

### What about GDPR compliance?

- Samplit uses first-party cookies only
- No personal data is collected without consent
- Integrate with your consent management platform
- Cookie: `samplit_visitor_id` - can be listed in cookie policy

### How do I handle page variants with caching?

For best results with cached pages:

1. Use client-side variations (JavaScript-based)
2. Exclude experiment pages from cache
3. Use "ESI" if your cache supports it
4. Or use edge-side A/B testing with CloudFlare Workers

---

## Support

Need help? We're here for you:

- 📖 **Knowledge Base**: [help.samplit.com](https://help.samplit.com)
- 📧 **Email Support**: support@samplit.com
- 💬 **Live Chat**: Available in dashboard (9am-6pm EST)
- 🎮 **Discord Community**: [discord.gg/samplit](https://discord.gg/samplit)
- 📹 **Video Tutorials**: [youtube.com/samplit](https://youtube.com/samplit)

For WordPress-specific issues, include:
- WordPress version
- PHP version
- Active theme name
- List of active plugins
- Screenshot of the issue

---

*Last updated: 2024*