# Getting Started with Sampelit

> **Sampelit A/B Testing Platform**  
> Your complete guide to running data-driven experiments

---

## Table of Contents

1. [What is Sampelit?](#what-is-Sampelit)
2. [Key Concepts](#key-concepts)
3. [Quick Start (5 Minutes)](#quick-start-5-minutes)
4. [Dashboard Overview](#dashboard-overview)
5. [Your First Experiment](#your-first-experiment)
6. [Understanding Results](#understanding-results)
7. [Next Steps](#next-steps)

---

## What is Sampelit?

Sampelit is an intelligent A/B testing platform that helps you optimize your website through data-driven experimentation. Unlike traditional A/B testing tools, Sampelit uses **Adaptive Optimization** algorithms that automatically allocate more traffic to better-performing variations, maximizing your conversions while the test runs.

### Key Benefits

| Feature | Benefit |
|---------|---------|
| **Adaptive Algorithms** | Automatically send more traffic to winners |
| **Visual Editor** | Create tests without coding |
| **Multi-Element Testing** | Test multiple elements simultaneously |
| **Real-time Analytics** | See results as they happen |
| **Bayesian Statistics** | Faster, more accurate decisions |

### Use Cases

- **E-commerce**: Test product pages, checkout flows, pricing
- **SaaS**: Optimize signup flows, landing pages, CTAs
- **Content Sites**: Test headlines, layouts, ad placements
- **Marketing**: A/B test landing pages, forms, campaigns

---

## Key Concepts

Before you begin, understand these core concepts:

### Experiments

An **experiment** is a test comparing different versions of content on your website. Each experiment has:

- **A goal** (what you're trying to improve)
- **Variations** (different versions to test)
- **Traffic allocation** (how much traffic sees the test)

### Variations

**Variations** are the different versions you're testing:

- **Control**: The original version (baseline)
- **Variant A, B, C...**: Modified versions

### Elements

**Elements** are the specific parts of a page you're testing:

- Headlines
- Buttons
- Images
- Forms
- Entire sections

### Conversions

A **conversion** is when a visitor completes your goal:

- Makes a purchase
- Signs up for newsletter
- Clicks a button
- Submits a form

### Statistical Significance

**Statistical significance** tells you if the results are reliable (not due to random chance). Sampelit shows this as a percentage—look for 95% or higher before making decisions.

---

## Quick Start (5 Minutes)

### Step 1: Create Your Account

1. Go to [Sampelit.com](https://Sampelit.com)
2. Click **Start for Free**
3. Enter your email and create a password
4. Verify your email

### Step 2: Add Your Website

1. In the dashboard, click **Installations** → **Add New**
2. Enter your website URL
3. Copy the tracker code snippet
4. Add it to your website's `<head>` section

```html
<!-- Sampelit A/B Testing Tracker -->
<script>
(function() {
    window.Sampelit_CONFIG = {
        installationToken: 'YOUR_TOKEN',
        apiEndpoint: 'https://api.Sampelit.com/api/v1/tracker'
    };
})();
</script>
<script src="https://api.Sampelit.com/static/tracker/t.js" async></script>
<!-- End Sampelit Tracker -->
```

> **Tip**: See [Tracker Installation Guide](tracker_guide.md) for detailed instructions.

### Step 3: Verify Installation

1. Visit your website
2. Return to Sampelit dashboard
3. Check that status shows: ✅ **Connected**

### Step 4: Create Your First Test

1. Click **Experiments** → **Create New**
2. Enter a name (e.g., "Homepage CTA Test")
3. Enter the page URL to test
4. Use the Visual Editor to select elements
5. Create your variations
6. Click **Start Experiment**

That's it! You're now running your first A/B test.

---

## Dashboard Overview

After logging in, you'll see the main dashboard:

```
┌─────────────────────────────────────────────────────────────────┐
│  Sampelit                                    [Profile] [Logout]  │
├───────────┬─────────────────────────────────────────────────────┤
│           │                                                     │
│ Dashboard │   📊 Active Experiments: 3                          │
│           │   👥 Total Visitors: 12,450                         │
│ Experiments│   🎯 Total Conversions: 847                         │
│           │   📈 Avg Conversion Rate: 6.8%                      │
│ Visual    │                                                     │
│ Editor    │   ┌─────────────────────────────────────────────┐   │
│           │   │ Recent Experiments                          │   │
│ Analytics │   │                                             │   │
│           │   │ • Homepage CTA Test      ▶ Running          │   │
│ Installations   │ • Pricing Page Layout    ▶ Running          │   │
│           │   │ • Checkout Flow          ■ Completed        │   │
│ Integrations   │                                             │   │
│           │   └─────────────────────────────────────────────┘   │
│ Settings  │                                                     │
│           │                                                     │
└───────────┴─────────────────────────────────────────────────────┘
```

### Navigation

| Section | Description |
|---------|-------------|
| **Dashboard** | Overview of all experiments and key metrics |
| **Experiments** | Create, manage, and analyze experiments |
| **Visual Editor** | Point-and-click experiment builder |
| **Analytics** | Detailed performance reports |
| **Installations** | Manage your website connections |
| **Integrations** | Connect Shopify, WordPress, etc. |
| **Settings** | Account, team, and billing |

---

## Your First Experiment

Let's walk through creating a complete experiment:

### 1. Define Your Goal

Before starting, answer:

- **What are you trying to improve?** (e.g., signup rate)
- **What do you want to test?** (e.g., button color)
- **How will you measure success?** (e.g., form submissions)

### 2. Create the Experiment

1. Go to **Experiments** → **Create New**

2. **Basic Information**:
   - Name: "Signup Button Color Test"
   - URL: `https://yoursite.com/signup`
   - Description: (optional) "Testing if orange converts better than green"

3. **Traffic Settings**:
   - Traffic Allocation: 100% (recommended for most tests)
   - Duration: Let it run until statistically significant

### 3. Add Variations

**Option A: Visual Editor (Recommended)**

1. Click **Open Visual Editor**
2. Your page loads in the editor
3. Click on the element to test (e.g., the signup button)
4. Click **Add Variation**
5. Modify the element (change color, text, size)
6. Repeat for additional variations
7. Click **Save**

**Option B: Code Editor**

For advanced users who want to write custom HTML/CSS/JS.

### 4. Set Goals

Define what counts as a conversion:

| Goal Type | Example |
|-----------|---------|
| Click | Button click, link click |
| Form Submit | Newsletter signup, contact form |
| Page View | Thank you page, confirmation page |
| Custom Event | Download, video play, scroll depth |

### 5. Review and Launch

1. Review your experiment settings
2. Check the preview of each variation
3. Click **Start Experiment**

Your experiment is now live!

---

## Understanding Results

### Reading the Results Dashboard

After your experiment has collected data, the results page shows:

```
┌─────────────────────────────────────────────────────────────────┐
│ Signup Button Color Test                        Status: Running │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  VARIATION      VISITORS    CONVERSIONS    RATE     CONFIDENCE │
│  ───────────────────────────────────────────────────────────── │
│  Control        5,234       312           5.96%     —           │
│  (Green)                                                        │
│                                                                 │
│  Variant A      5,198       391           7.52%     97.8% 🏆    │
│  (Orange)                                                       │
│                                                                 │
│  Variant B      5,201       334           6.42%     72.3%       │
│  (Blue)                                                         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  Improvement: Variant A is 26.2% better than Control            │
│  Recommendation: Deploy Variant A                               │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics Explained

| Metric | What It Means |
|--------|---------------|
| **Visitors** | Number of people who saw this variation |
| **Conversions** | Number who completed the goal |
| **Rate** | Conversions / Visitors × 100 |
| **Confidence** | How sure we are the result is real |

### When to Stop an Experiment

✅ **Stop when**:
- Confidence reaches 95% or higher
- You have at least 100 conversions per variation
- The experiment has run for at least 7 days

⚠️ **Don't stop when**:
- You see early "good" results (wait for significance)
- It's running less than a week (seasonal effects)
- You don't have enough conversions yet

### Implementing the Winner

When a winner is clear:

1. Click **Implement Winner** on the results page
2. Update your actual website with the winning variation
3. Click **Complete Experiment**

---

## Next Steps

### Explore More Guides

| Guide | Description |
|-------|-------------|
| [Visual Editor Guide](visual_editor_guide.md) | Master point-and-click testing |
| [Experiments Guide](experiments_guide.md) | Advanced experiment techniques |
| [Analytics Guide](analytics_guide.md) | Deep dive into metrics |
| [Shopify Guide](shopify_guide.md) | Shopify store integration |
| [WordPress Guide](wordpress_guide.md) | WordPress site integration |

### Best Practices

1. **Test one thing at a time**: Isolate variables for clear insights
2. **Be patient**: Wait for statistical significance
3. **Mobile matters**: Check results by device type
4. **Document everything**: Write notes on what you learned
5. **Keep testing**: Optimization is continuous

### Get Help

- 📖 **Knowledge Base**: [help.Sampelit.com](https://help.Sampelit.com)
- 📧 **Email Support**: support@Sampelit.com
- 💬 **Live Chat**: Available in dashboard
- 🎮 **Discord Community**: [discord.gg/Sampelit](https://discord.gg/Sampelit)

---

*Welcome to Sampelit! Start optimizing today.*
