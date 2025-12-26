# Tracker Snippet Installation Guide

> **Samplit A/B Testing Platform**  
> Universal installation guide for any website

---

## Table of Contents

1. [Overview](#overview)
2. [Get Your Tracker Snippet](#get-your-tracker-snippet)
3. [Installation Options](#installation-options)
4. [Option A: Self-Installation (DIY)](#option-a-self-installation-diy)
5. [Option B: Request Installation from Your Hosting Provider](#option-b-request-installation-from-your-hosting-provider)
6. [Option C: Hire a Freelancer or Web Agency](#option-c-hire-a-freelancer-or-web-agency)
7. [Verifying Your Installation](#verifying-your-installation)
8. [Platform-Specific Instructions](#platform-specific-instructions)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## Overview

The Samplit tracker snippet is a small piece of JavaScript code that enables A/B testing on your website. This guide covers all the ways you can install it, whether you do it yourself or get help from your hosting provider or a web professional.

### What is the Tracker Snippet?

It's a small JavaScript code that you add to your website's HTML. It looks like this:

```html
<!-- Samplit A/B Testing Tracker -->
<script>
(function() {
    window.SAMPLIT_CONFIG = {
        installationToken: 'YOUR_TOKEN_HERE',
        apiEndpoint: 'https://api.samplit.com/api/v1/tracker'
    };
})();
</script>
<script src="https://api.samplit.com/static/tracker/t.js" async></script>
<!-- End Samplit Tracker -->
```

### Installation Time

| Method | Time Required | Technical Skill |
|--------|---------------|-----------------|
| Self-Installation | 5-15 minutes | Basic |
| Hosting Provider | 1-2 business days | None |
| Freelancer/Agency | 1-3 business days | None |

---

## Get Your Tracker Snippet

Before installation, you need your personalized tracker code:

1. Log into [Samplit Dashboard](https://app.samplit.com)
2. Go to **Installations** → **Add New Installation**
3. Enter your website name and URL
4. Click **Create Installation**
5. Copy your tracker snippet code

Your snippet will have a unique `installationToken` — this is specific to your website.

> ⚠️ **Important**: Keep your installation token private. Don't share it publicly.

---

## Installation Options

Choose the option that works best for you:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     INSTALLATION OPTIONS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │             │    │             │    │             │             │
│  │  OPTION A   │    │  OPTION B   │    │  OPTION C   │             │
│  │    DIY      │    │   HOSTING   │    │ FREELANCER  │             │
│  │             │    │  PROVIDER   │    │  / AGENCY   │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│        │                  │                  │                      │
│        ▼                  ▼                  ▼                      │
│   You install        They install       Professional               │
│   it yourself        it for you         installs it                │
│                                                                     │
│   ✓ Free             ✓ Free/Low cost    ✓ Full service            │
│   ✓ Immediate        ✓ No tech skills   ✓ Additional help         │
│   ✓ Full control     ✓ Quick support    ✓ Ongoing support         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Option A: Self-Installation (DIY)

Best for: Website owners comfortable with basic HTML or using website builders.

### Requirements

- Access to your website's admin panel or hosting file manager
- Ability to edit HTML or use a code injection feature
- 5-15 minutes of time

### General Instructions

The tracker snippet must be placed in the `<head>` section of every page on your website.

```html
<!DOCTYPE html>
<html>
<head>
    <title>Your Website</title>
    
    <!-- Samplit A/B Testing Tracker -->
    <script>
    (function() {
        window.SAMPLIT_CONFIG = {
            installationToken: 'YOUR_TOKEN_HERE',
            apiEndpoint: 'https://api.samplit.com/api/v1/tracker'
        };
    })();
    </script>
    <script src="https://api.samplit.com/static/tracker/t.js" async></script>
    <!-- End Samplit Tracker -->
    
</head>
<body>
    <!-- Your website content -->
</body>
</html>
```

### Quick Links by Platform

Jump to specific instructions:
- [WordPress](#wordpress)
- [Wix](#wix)
- [Squarespace](#squarespace)
- [Webflow](#webflow)
- [Shopify](#shopify)
- [Google Tag Manager](#google-tag-manager)
- [Custom HTML Site](#custom-html-site)

---

## Option B: Request Installation from Your Hosting Provider

Best for: Non-technical users who want a simple solution.

Many hosting providers offer free or low-cost assistance with adding tracking codes. Here's how to request it:

### Step 1: Find Your Provider's Support

Contact your hosting provider through:
- Live chat (fastest)
- Support ticket
- Phone support
- Email

**Popular hosting providers and their support:**

| Provider | Support URL | Method |
|----------|-------------|--------|
| GoDaddy | support.godaddy.com | Chat, Phone |
| Bluehost | bluehost.com/contact | Chat, Phone |
| SiteGround | siteground.com/help | Chat, Ticket |
| HostGator | hostgator.com/contact | Chat, Phone |
| Hostinger | hostinger.com/contact | Chat |
| Wix | support.wix.com | Ticket |
| Squarespace | support.squarespace.com | Chat, Email |
| DreamHost | dreamhost.com/support | Chat, Ticket |
| Namecheap | namecheap.com/support | Chat, Ticket |
| OVH | help.ovhcloud.com | Ticket |
| Ionos | ionos.com/help | Chat, Phone |

### Step 2: Send This Message

Copy, customize, and send to your hosting provider:

---

**Subject: Request to Add Tracking Code to Website Header**

Hello,

I would like to request assistance adding a tracking code snippet to my website.

**Website:** [YOUR WEBSITE URL]  
**Account/Username:** [YOUR ACCOUNT NAME]

Please add the following code to the `<head>` section of ALL pages on my website:

```html
<!-- Samplit A/B Testing Tracker -->
<script>
(function() {
    window.SAMPLIT_CONFIG = {
        installationToken: 'YOUR_TOKEN_HERE',
        apiEndpoint: 'https://api.samplit.com/api/v1/tracker'
    };
})();
</script>
<script src="https://api.samplit.com/static/tracker/t.js" async></script>
<!-- End Samplit Tracker -->
```

This code should be placed:
- Before the closing `</head>` tag
- On every page of my website
- Including the homepage

Please let me know when this has been completed so I can verify the installation.

Thank you,  
[YOUR NAME]

---

### Step 3: Verify Installation

Once your provider confirms the installation, follow the [Verifying Your Installation](#verifying-your-installation) section.

### Expected Response Time

| Provider Type | Typical Response |
|---------------|------------------|
| Managed Hosting | 1-4 hours |
| Shared Hosting | 24-48 hours |
| Website Builders | Same day (chat) |

### If They Charge for This Service

Some providers may charge a small fee (typically $10-50). Alternatives:
- Ask if they have a free code injection feature in your control panel
- Consider Option C (freelancer) for more comprehensive help
- Try Option A if you're comfortable with basic steps

---

## Option C: Hire a Freelancer or Web Agency

Best for: Users who want professional help or have complex websites.

### Where to Find Help

**Freelance Platforms:**

| Platform | Typical Cost | URL |
|----------|--------------|-----|
| Fiverr | $5-50 | fiverr.com |
| Upwork | $20-100 | upwork.com |
| Freelancer | $15-75 | freelancer.com |
| Toptal | $100+ | toptal.com |
| PeoplePerHour | $15-75 | peopleperhour.com |

**Local Options:**
- Your existing web developer/designer
- Local web agencies
- Digital marketing agencies
- IT support companies

### What to Ask For

When posting a job or contacting a professional:

---

**Job Title:** Add Tracking Script to Website Header

**Description:**

I need help adding a JavaScript tracking snippet to my website. The task involves:

1. Adding a small script to the `<head>` section of my website
2. Ensuring the script loads on ALL pages
3. Verifying the installation works correctly

**Website Platform:** [WordPress/Wix/Squarespace/Custom/etc.]  
**Website URL:** [YOUR URL]

**The code to be added:**

```html
<!-- Samplit A/B Testing Tracker -->
<script>
(function() {
    window.SAMPLIT_CONFIG = {
        installationToken: 'YOUR_TOKEN_HERE',
        apiEndpoint: 'https://api.samplit.com/api/v1/tracker'
    };
})();
</script>
<script src="https://api.samplit.com/static/tracker/t.js" async></script>
<!-- End Samplit Tracker -->
```

**Deliverables:**
- Script installed on all pages
- Screenshot showing script in page source
- Brief verification that it's loading correctly

**Timeline:** Within 24-48 hours preferred

---

### What to Provide the Freelancer

1. ✅ The tracker snippet code (from your Samplit dashboard)
2. ✅ Admin access to your website (create a temporary account if possible)
3. ✅ Instructions on which pages need the tracker (usually ALL pages)
4. ❌ DON'T share your Samplit account password

### Security Tips

When giving access to freelancers:

- **Create temporary credentials** — Delete them after the job is done
- **Use a separate admin account** — Don't share your main login
- **Change passwords after** — Good practice after any third-party access
- **Check their reviews** — Look for verified reviews and completed jobs
- **Use platform payments** — Pay through the freelance platform for protection

### Typical Costs

| Complexity | Price Range | Includes |
|------------|-------------|----------|
| Simple (WordPress/Wix) | $10-30 | Installation + verification |
| Standard | $30-75 | Installation + testing + minor fixes |
| Complex (custom site) | $75-150 | Full installation + documentation |

---

## Verifying Your Installation

After installation (regardless of method), verify it works:

### Method 1: Browser Check (Easiest)

1. Open your website in Chrome or Firefox
2. Right-click anywhere and select **View Page Source**
3. Press `Ctrl+F` (or `Cmd+F` on Mac)
4. Search for `Samplit`
5. You should find the tracker code in the `<head>` section

### Method 2: Developer Tools

1. Open your website
2. Press `F12` to open Developer Tools
3. Go to the **Network** tab
4. Refresh the page
5. Filter by "samplit" or "t.js"
6. You should see the tracker script loading (status 200)

### Method 3: Console Check

1. Open your website
2. Press `F12` to open Developer Tools
3. Go to the **Console** tab
4. Type: `window.SAMPLIT_CONFIG`
5. Press Enter
6. You should see your configuration object

### Method 4: Samplit Dashboard

1. Log into [Samplit Dashboard](https://app.samplit.com)
2. Go to **Installations**
3. Find your website
4. Check the status indicator:
   - 🟢 **Connected**: Working correctly
   - 🟡 **Pending**: Waiting for first data
   - 🔴 **Not Connected**: Installation issue

---

## Platform-Specific Instructions

### WordPress

**Method 1: Theme Customizer**
1. Go to **Appearance** → **Customize**
2. Look for "Additional CSS" or "Header Scripts"
3. If available, paste the tracker code
4. Save/Publish

**Method 2: Plugin (Recommended)**
1. Install "Insert Headers and Footers" plugin
2. Go to **Settings** → **Insert Headers and Footers**
3. Paste tracker code in "Scripts in Header"
4. Save

**Method 3: Theme Editor**
1. Go to **Appearance** → **Theme File Editor**
2. Select `header.php`
3. Find `</head>` and paste the code BEFORE it
4. Update File

### Wix

1. Go to your Wix Dashboard
2. Click **Settings** → **Custom Code**
3. Click **+ Add Custom Code**
4. Paste your tracker snippet
5. Name it "Samplit Tracker"
6. Set placement to "Head"
7. Apply to "All Pages"
8. Click **Apply**

### Squarespace

1. Go to **Settings** → **Advanced** → **Code Injection**
2. In the "Header" section, paste your tracker code
3. Click **Save**

### Webflow

1. Go to **Project Settings** → **Custom Code**
2. In "Head Code", paste your tracker snippet
3. Save and publish

### Shopify

1. Go to **Online Store** → **Themes**
2. Click **Actions** → **Edit Code**
3. Open `theme.liquid`
4. Find `</head>` and paste the code BEFORE it
5. Save

### Google Tag Manager

1. Log into Google Tag Manager
2. Create a new **Tag**
3. Choose **Custom HTML**
4. Paste your tracker snippet
5. Set trigger to "All Pages"
6. Name it "Samplit Tracker"
7. Submit and publish

### Custom HTML Site

1. Open your HTML files in a text editor
2. Find the `</head>` closing tag
3. Paste the tracker code BEFORE `</head>`
4. Save and upload to your server
5. Repeat for ALL HTML pages

> **Tip**: If you have many HTML files, consider using a templating system or include file.

---

## Troubleshooting

### Issue: Script not appearing in page source

**Possible causes:**
- Code wasn't saved properly
- Code is in the wrong location
- Caching is serving old pages

**Solutions:**
1. Clear your browser cache and refresh
2. Clear your website's cache (if using caching plugin/service)
3. Verify the code is in the `<head>` section
4. Wait 5-10 minutes for cache to expire

### Issue: Dashboard shows "Not Connected"

**Possible causes:**
- Installation token is incorrect
- Script is blocked by ad blocker
- Script has a typo or modification

**Solutions:**
1. Re-copy the tracker code from your dashboard
2. Ensure the installation token matches exactly
3. Disable ad blocker and refresh
4. Check browser console for errors

### Issue: Script loads but experiments don't work

**Possible causes:**
- Experiment not started
- Targeting rules not matching
- Traffic allocation set to 0%

**Solutions:**
1. Verify experiment is set to "Running" in dashboard
2. Check targeting rules match your test conditions
3. Ensure traffic allocation is greater than 0%

### Issue: Hosting provider says they can't add the code

**Possible responses:**
- Ask if they have a "Custom Code" or "Script Injection" feature
- Request access to file manager to do it yourself
- Consider upgrading your hosting plan
- Use Google Tag Manager as an alternative

---

## FAQ

### Do I need technical skills to install this?

For Option A (DIY), basic familiarity with your website's admin panel is helpful. Options B and C require no technical skills at all.

### Is there a cost for installation?

- **Self-installation**: Free
- **Hosting provider**: Usually free, some may charge $10-50
- **Freelancer**: Typically $10-75 depending on complexity

### How long does installation take?

- **Self-installation**: 5-15 minutes
- **Hosting provider**: 1-2 business days
- **Freelancer**: 1-3 business days

### Will this slow down my website?

No. The tracker script:
- Loads asynchronously (doesn't block page loading)
- Is less than 10KB in size
- Is served from a fast CDN

### Does the tracker work on all pages automatically?

Yes, once installed in the `<head>` section, it tracks all pages on your website.

### What if I have multiple websites?

Create a separate installation in Samplit for each website. Each will have its own unique installation token.

### Can I install on a staging/test site first?

Yes! Create a separate installation for your staging site to test before going live.

### What happens if I install it wrong?

The worst case is that tracking won't work. It won't break your website. You can always reinstall or ask for help.

### Do I need to update the code?

No. The tracker automatically loads the latest version from our servers.

### Can I remove it later?

Yes. Simply delete the tracker code from your website to stop tracking.

---

## Need Help?

If you're stuck at any point:

- 📖 **Knowledge Base**: [help.samplit.com](https://help.samplit.com)
- 📧 **Email Support**: support@samplit.com
- 💬 **Live Chat**: Available in dashboard (9am-6pm EST)
- 🎮 **Discord Community**: [discord.gg/samplit](https://discord.gg/samplit)

### Installation Assistance

If none of the options work for you, contact us at **support@samplit.com** with:
- Your website URL
- Your website platform (WordPress, Wix, etc.)
- What you've tried so far

We'll help you find the best solution for your situation.

---

*Last updated: 2024*