# Shopify Integration Guide

> **Samplit A/B Testing Platform**  
> Complete integration guide for Shopify stores

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Step-by-Step Installation](#step-by-step-installation)
5. [OAuth Authentication Flow](#oauth-authentication-flow)
6. [Configuring Webhooks](#configuring-webhooks)
7. [Running Experiments](#running-experiments)
8. [Tracking Conversions](#tracking-conversions)
9. [Managing Your Integration](#managing-your-integration)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Overview

The Samplit Shopify integration allows you to run A/B tests on your Shopify store with automatic tracking of conversions, orders, and customer behavior. This integration uses Shopify's OAuth 2.0 authentication and Admin API for seamless connectivity.

### What You Can Test

- Product page layouts and descriptions
- Pricing strategies
- Checkout flow variations
- Homepage banners and CTAs
- Navigation and menu structures
- Product recommendations
- Cart page designs

### Key Features

- **One-click installation**: Connect your store in minutes
- **Automatic conversion tracking**: Orders and checkouts are tracked automatically
- **Real-time webhooks**: Instant updates when events occur
- **No theme modifications required**: Uses Shopify Script Tags for injection
- **Works with all Shopify plans**: Basic, Shopify, Advanced, and Plus

---

## Prerequisites

Before starting, ensure you have:

- [ ] A Shopify store (any plan)
- [ ] Store owner or staff account with app installation permissions
- [ ] A Samplit account (sign up at [samplit.com](https://samplit.com))
- [ ] Your Shopify store's `.myshopify.com` domain

---

## Quick Start

### 1. Get Your Store Domain

Your Shopify store domain is your `.myshopify.com` URL. You can find it in:

**Shopify Admin → Settings → Domains**

Example formats:
- `mystore.myshopify.com` ✓
- `https://mystore.myshopify.com` ✓
- `mystore` (we'll add `.myshopify.com` automatically) ✓

### 2. Connect from Samplit Dashboard

1. Log into [Samplit Dashboard](https://app.samplit.com)
2. Go to **Integrations** → **Add Integration**
3. Select **Shopify**
4. Enter your store domain
5. Click **Connect Store**
6. Authorize the app in Shopify

### 3. Verify Connection

After authorization, you'll be redirected back to Samplit. You should see:
- ✅ Store connected successfully
- ✅ Webhooks registered
- ✅ Tracker installed

---

## Step-by-Step Installation

### Step 1: Prepare Your Store Domain

Find your store's myshopify.com domain:

1. Log into your Shopify admin
2. Go to **Settings** (bottom left)
3. Click **Domains**
4. Look for your `.myshopify.com` domain

> **Note**: Even if you have a custom domain (e.g., `www.mystore.com`), you need the `.myshopify.com` domain for OAuth.

### Step 2: Initiate OAuth Connection

In your Samplit dashboard:

1. Navigate to **Integrations**
2. Click **+ Add New Integration**
3. Choose **Shopify** from the platform list
4. Enter your store domain in the input field:

```
mystore.myshopify.com
```

5. Click **Connect to Shopify**

### Step 3: Authorize in Shopify

You'll be redirected to Shopify to authorize the connection. Review the permissions requested:

| Permission | Purpose |
|------------|---------|
| `read_products` | Read product information for experiments |
| `write_products` | Update product data if needed |
| `read_orders` | Track order conversions |
| `read_customers` | Segment experiments by customer type |
| `write_script_tags` | Install the Samplit tracker on your store |
| `read_themes` | Read theme data for experiments |
| `write_themes` | Optional: Modify theme for advanced experiments |

Click **Install app** to authorize.

### Step 4: Confirm Installation

After authorization, you'll be redirected back to Samplit. Verify:

1. **Connection Status**: Shows "Connected"
2. **Store Information**: Displays your store name, currency, and timezone
3. **Tracker Status**: Shows "Installed"
4. **Webhooks**: Shows "4 webhooks registered"

### Step 5: Test the Tracker

Visit your Shopify store and verify the tracker is working:

1. Open your store's homepage
2. Open browser Developer Tools (F12)
3. Go to the **Network** tab
4. Filter by "samplit" or "t.js"
5. You should see the tracker script loading

Alternatively, view page source and search for:

```html
<!-- Samplit A/B Testing Tracker -->
```

---

## OAuth Authentication Flow

Understanding the OAuth flow helps troubleshoot issues:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Samplit App    │────▶│   Shopify       │────▶│  Your Store     │
│                 │     │   OAuth Server  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                       │
         │  1. Request Auth      │                       │
         │──────────────────────▶│                       │
         │                       │  2. Login & Approve   │
         │                       │──────────────────────▶│
         │                       │                       │
         │                       │  3. Auth Code         │
         │                       │◀──────────────────────│
         │  4. Exchange Code     │                       │
         │◀──────────────────────│                       │
         │                       │                       │
         │  5. Access Token      │                       │
         │◀──────────────────────│                       │
         │                       │                       │
```

### Scopes Explained

The integration requests specific Shopify scopes:

```
read_products,write_products,read_orders,read_customers,write_script_tags,read_themes,write_themes
```

Each scope grants specific permissions:

| Scope | Access Level | Required For |
|-------|--------------|--------------|
| `read_products` | Read only | Viewing products for experiments |
| `write_products` | Read/Write | A/B testing product attributes |
| `read_orders` | Read only | Conversion tracking |
| `read_customers` | Read only | Customer segmentation |
| `write_script_tags` | Read/Write | Installing tracker script |
| `read_themes` | Read only | Reading theme configuration |
| `write_themes` | Read/Write | Advanced theme experiments |

---

## Configuring Webhooks

Webhooks enable real-time tracking of important events. The integration automatically registers these webhooks:

### Registered Webhooks

| Webhook Topic | Event | Purpose |
|---------------|-------|---------|
| `orders/create` | New order placed | Track purchase conversions |
| `checkouts/create` | Checkout initiated | Track checkout funnel |
| `products/update` | Product modified | Sync experiment data |
| `app/uninstalled` | App removed | Cleanup integration |

### Webhook Verification

All webhooks are verified using HMAC-SHA256 signatures to ensure they come from Shopify:

```
X-Shopify-Hmac-SHA256: [base64-encoded-signature]
```

### Webhook Endpoints

Webhooks are sent to:

```
https://api.samplit.com/webhooks/shopify
```

> **Note**: You don't need to configure anything — webhooks are registered automatically during installation.

### Re-registering Webhooks

If webhooks stop working:

1. Go to **Samplit Dashboard** → **Integrations** → **Shopify**
2. Click **Settings** (gear icon)
3. Click **Re-register Webhooks**
4. Verify all 4 webhooks show "Active"

---

## Running Experiments

### Creating Your First Experiment

1. **Go to Experiments**
   - Samplit Dashboard → **Experiments** → **Create New**

2. **Select Your Shopify Store**
   - Choose your connected Shopify store as the target

3. **Define Experiment Type**
   - **A/B Test**: Two variations
   - **Multivariate**: Multiple elements
   - **Split URL**: Different pages

4. **Set Targeting Rules**

   ```
   Page URL contains: /products/
   Device: All devices
   Traffic allocation: 50%
   ```

5. **Create Variations**

   Example: Testing a product page CTA button:
   
   | Variation | Button Text | Button Color |
   |-----------|-------------|--------------|
   | Control | "Add to Cart" | Green |
   | Variant A | "Buy Now" | Orange |
   | Variant B | "Get Yours" | Blue |

6. **Set Goals**
   - Primary: Order completed
   - Secondary: Add to cart, Checkout initiated

7. **Launch Experiment**
   - Review settings
   - Click **Start Experiment**

### Experiment Sync

When you create or update an experiment, Samplit automatically:

1. Creates/updates a **Script Tag** in your Shopify store
2. Stores experiment metadata in **Shopify Metafields**
3. Configures the tracker to run the experiment

You can verify in Shopify Admin:

**Settings → Apps and sales channels → Samplit → Script tags**

---

## Tracking Conversions

### Automatic Conversion Tracking

The following events are tracked automatically:

| Event | Triggered When | Tracked As |
|-------|----------------|------------|
| `order_completed` | Order is created | Primary conversion |
| `checkout_started` | Checkout begins | Micro-conversion |
| `add_to_cart` | Product added to cart | Micro-conversion |
| `product_viewed` | Product page loaded | Engagement |
| `page_view` | Any page loaded | Engagement |

### Revenue Attribution

Orders are attributed to experiments based on:

1. **Session-based**: User was in experiment during the session
2. **Cookie-based**: User was assigned to a variation
3. **Time-windowed**: Conversion within 7 days of experiment exposure

### Viewing Conversion Data

In your Samplit dashboard:

1. Go to **Experiments** → Select your experiment
2. Click **Results** tab
3. View:
   - Conversion rate by variation
   - Revenue by variation
   - Statistical significance
   - Confidence intervals

---

## Managing Your Integration

### Viewing Store Information

**Samplit Dashboard → Integrations → Shopify → Store Info**

Displays:
- Store name
- Store email
- Currency
- Timezone
- Shopify plan
- Primary domain

### Updating Connection

If you need to reconnect:

1. Go to **Integrations** → **Shopify**
2. Click **Disconnect**
3. Follow the installation steps again

### Removing an Experiment

When you stop or delete an experiment:

1. Script tags for that experiment are removed from Shopify
2. Metafields are cleaned up
3. No residual code remains in your store

### Uninstalling Completely

To remove Samplit from your store:

**Option 1: From Samplit**
1. Dashboard → Integrations → Shopify
2. Click **Disconnect**
3. Confirm removal

**Option 2: From Shopify**
1. Shopify Admin → Settings → Apps and sales channels
2. Find Samplit
3. Click **Uninstall**

Both methods will:
- Remove all script tags
- Clear metafields
- Delete webhooks
- Revoke access tokens

---

## Troubleshooting

### Common Issues

#### Issue: "Shop domain not configured" error

**Cause**: Store domain wasn't saved correctly during setup.

**Solution**:
1. Disconnect the integration
2. Reconnect with the correct `.myshopify.com` domain
3. Ensure the domain format is correct:
   - ✅ `mystore.myshopify.com`
   - ❌ `www.mystore.com`

#### Issue: Tracker not appearing on store

**Cause**: Script tag wasn't created or was removed.

**Solution**:
1. Check script tags in Shopify:
   - Admin → Settings → Apps and sales channels → Samplit
2. If missing, go to Samplit → Integrations → Shopify → **Re-sync**
3. Verify in browser DevTools that script is loading

#### Issue: Webhooks not receiving events

**Cause**: Webhook registration failed or was deleted.

**Solution**:
1. Go to Samplit → Integrations → Shopify → Settings
2. Click **Re-register Webhooks**
3. Check Shopify Admin → Settings → Notifications → Webhooks
4. Verify the Samplit webhook URL is listed

#### Issue: Orders not tracking as conversions

**Cause**: Webhook signature verification failing or user not in experiment.

**Solution**:
1. Verify webhooks are registered (see above)
2. Check that the order was from a user in an active experiment
3. Review the experiment's conversion settings
4. Check the experiment's date range

#### Issue: "Token exchange failed" during OAuth

**Cause**: OAuth credentials misconfigured or network issue.

**Solution**:
1. Wait a few minutes and try again
2. Clear browser cookies and cache
3. Try in incognito/private mode
4. Contact support if issue persists

#### Issue: Access token expired

**Note**: Shopify access tokens don't expire. If you see this error:

**Solution**:
1. The store may have revoked access
2. The app may have been uninstalled
3. Reconnect the integration

### Checking Connection Health

Verify your integration is healthy:

```
Samplit Dashboard → Integrations → Shopify → Health Check
```

Shows:
- ✅ API Connection: Connected
- ✅ Webhooks: 4/4 Active
- ✅ Tracker: Installed
- ✅ Last sync: X minutes ago

### Debug Mode

Enable debug logging for troubleshooting:

1. Dashboard → Integrations → Shopify → Settings
2. Enable **Debug Mode**
3. Reproduce the issue
4. Download debug logs
5. Contact support with logs attached

---

## FAQ

### Does this work with Shopify Plus?

Yes! The integration works with all Shopify plans including Plus. Plus stores can also use additional features like checkout.liquid modifications.

### Will this slow down my store?

No. The tracker script is loaded asynchronously and is optimized for performance:
- Script size: < 10KB gzipped
- Load time: < 50ms
- No render blocking

### Can I run experiments on the checkout page?

On standard Shopify plans, checkout customization is limited. On Shopify Plus, you can customize checkout.liquid for experiments.

### How long is data retained?

Experiment data is retained for:
- Active experiments: Unlimited
- Completed experiments: 2 years
- Raw event data: 90 days

### Can I use this with a headless Shopify setup?

Yes, but you'll need to manually install the tracker in your custom frontend. Contact support for headless implementation guidance.

### What happens to running experiments if I disconnect?

If you disconnect the integration:
1. Experiments will stop immediately
2. No new data will be collected
3. Historical data is preserved
4. You can download results before disconnecting

### Can multiple team members manage experiments?

Yes! Add team members in:
- Samplit Dashboard → Settings → Team
- Assign roles: Admin, Editor, Viewer

### Is my store data secure?

Yes. We follow industry best practices:
- OAuth 2.0 authentication
- HMAC webhook verification
- Encrypted data storage
- GDPR and CCPA compliant

---

## Support

Need help? We're here for you:

- 📖 **Knowledge Base**: [help.samplit.com](https://help.samplit.com)
- 📧 **Email Support**: support@samplit.com
- 💬 **Live Chat**: Available in dashboard (9am-6pm EST)
- 🎮 **Discord Community**: [discord.gg/samplit](https://discord.gg/samplit)

For urgent issues, email priority-support@samplit.com with your store domain.

---

*Last updated: 2024*