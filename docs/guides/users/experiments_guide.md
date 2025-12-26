# Experiments Guide

> **Sampelit A/B Testing Platform**  
> Complete guide to creating and managing experiments

---

## Table of Contents

1. [Understanding Experiments](#understanding-experiments)
2. [Experiment Types](#experiment-types)
3. [Creating an Experiment](#creating-an-experiment)
4. [Configuring Variations](#configuring-variations)
5. [Traffic Allocation](#traffic-allocation)
6. [Setting Goals](#setting-goals)
7. [Targeting and Segmentation](#targeting-and-segmentation)
8. [Managing Active Experiments](#managing-active-experiments)
9. [Multi-Element Testing](#multi-element-testing)
10. [Best Practices](#best-practices)

---

## Understanding Experiments

An experiment in Sampelit compares different versions of content to determine which performs best. The platform uses **Adaptive Optimization** algorithms to automatically allocate more traffic to better-performing variations while the test runs.

### Experiment Lifecycle

```
DRAFT → ACTIVE → COMPLETED
  │        │
  │        └──▶ PAUSED (temporary)
  │
  └──▶ DELETED (cancelled)
```

| Status | Description |
|--------|-------------|
| **Draft** | Experiment is being configured, not yet live |
| **Active** | Experiment is running, collecting data |
| **Paused** | Temporarily stopped, can resume |
| **Completed** | Winner declared, experiment finished |

---

## Experiment Types

### A/B Test (Simple)

The classic two-variation test:
- Control (original)
- Variant (modified)

**Best for**: Quick tests, clear hypotheses

### A/B/n Test (Multiple Variants)

Testing multiple variations simultaneously:
- Control
- Variant A
- Variant B
- Variant C
- (up to 10 variations)

**Best for**: Testing multiple ideas at once

### Multi-Element Test

Testing multiple elements on the same page:
- Button color (2 variations)
- Headline (3 variations)
- Image (2 variations)

**Best for**: Comprehensive page optimization

### Split URL Test

Sending visitors to completely different pages:
- `yoursite.com/landing-a`
- `yoursite.com/landing-b`

**Best for**: Major redesigns, different page structures

---

## Creating an Experiment

### Step 1: Basic Setup

1. Go to **Experiments** → **Create New**

2. Fill in basic information:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Descriptive name | "Homepage CTA Test Q4" |
| **URL** | Page to test | `https://yoursite.com` |
| **Description** | Notes and hypothesis | "Testing if 'Get Started' converts better than 'Sign Up'" |

### Step 2: Choose Creation Method

**Visual Editor** (Recommended for most users)
- Point-and-click interface
- No coding required
- See [Visual Editor Guide](visual_editor_guide.md)

**Code Editor** (For developers)
- Write custom HTML/CSS/JS
- Full control over variations
- Suitable for complex changes

**Manual Configuration** (API-based)
- Define variations via API
- For programmatic experiment creation

### Step 3: Add Variations

Each element you test needs variations:

```
Element: Hero Button
├── Control: "Sign Up Free" (green)
├── Variant A: "Start Now" (blue)
└── Variant B: "Get Started" (orange)
```

### Step 4: Configure Settings

- Traffic allocation
- Goals and conversions
- Targeting rules
- Schedule (optional)

### Step 5: Review and Launch

1. Preview each variation
2. Verify targeting rules
3. Check goal configuration
4. Click **Launch**

---

## Configuring Variations

### Variation Properties

| Property | Description |
|----------|-------------|
| **Name** | Descriptive identifier |
| **Content** | The actual HTML/text/CSS |
| **Weight** | Initial traffic distribution |
| **Quality** | Bandit algorithm parameter (auto-set) |

### Creating Effective Variations

**Good variation examples**:
- ✅ "Buy Now" vs "Add to Cart" (clear difference)
- ✅ Green button vs Orange button (testable hypothesis)
- ✅ Short headline vs Long headline (measurable)

**Poor variation examples**:
- ❌ Changing font from 14px to 14.5px (too subtle)
- ❌ Testing 10 things at once (too complex)
- ❌ Completely different pages in A/B test (use Split URL)

### Control Variation

The control is special:
- It's the original, unchanged version
- All other variations are compared against it
- Never delete the control

---

## Traffic Allocation

### How Traffic Distribution Works

Traffic allocation determines what percentage of your visitors see the experiment:

| Allocation | Meaning |
|------------|---------|
| **100%** | All visitors participate in the test |
| **50%** | Half of visitors see the test |
| **10%** | Only 10% participate (conservative) |

### Adaptive Traffic Allocation

Sampelit uses **Adaptive Optimization** to automatically adjust traffic:

1. **Initial Phase**: Traffic is split evenly among variations
2. **Learning Phase**: Algorithm identifies better performers
3. **Exploitation Phase**: More traffic goes to likely winners

This means you get more conversions overall compared to traditional 50/50 splits.

### Per-Variation Weights

You can also set initial weights per variation:

```
Control:    30%
Variant A:  35%
Variant B:  35%
```

Use this if you want to expose fewer visitors to a risky variation.

---

## Setting Goals

### Goal Types

| Type | Trigger | Example |
|------|---------|---------|
| **Click** | User clicks an element | Button click, link click |
| **Page View** | User views a page | Thank you page, confirmation |
| **Form Submit** | User submits a form | Signup, contact form |
| **Custom Event** | JavaScript event | Video play, scroll depth |
| **Revenue** | Transaction value | Order total (e-commerce) |

### Primary vs Secondary Goals

- **Primary Goal**: The main metric you're optimizing for
- **Secondary Goals**: Additional metrics to track

Example:
- Primary: Purchase completed
- Secondary: Add to cart, Newsletter signup

### Configuring Goals

1. In experiment settings, scroll to **Goals**
2. Add a new goal:
   - Click **+ Add Goal**
   - Select type (Click, Page View, etc.)
   - Configure the trigger
   - Mark as Primary or Secondary
3. Repeat for additional goals

### Goal Examples

**E-commerce purchase**:
```
Type: Page View
URL contains: /thank-you
Name: Purchase Complete
Primary: Yes
```

**Button click**:
```
Type: Click
Selector: .cta-primary
Name: CTA Click
Primary: No
```

**Custom event**:
```
Type: Custom Event
Event name: video_started
Name: Video Engagement
Primary: No
```

---

## Targeting and Segmentation

### URL Targeting

Test only on specific pages:

| Pattern | Matches |
|---------|---------|
| `https://yoursite.com/` | Exact homepage only |
| `https://yoursite.com/products/*` | All product pages |
| `*checkout*` | Any URL containing "checkout" |

### Device Targeting

Target specific devices:

- **All Devices**: Everyone sees the test
- **Desktop Only**: Tablets and computers
- **Mobile Only**: Phones only
- **Tablet Only**: Tablets only

### User Targeting

Segment by user characteristics:

| Segment | Description |
|---------|-------------|
| **New Visitors** | First-time visitors |
| **Returning Visitors** | Have visited before |
| **Logged In** | Authenticated users |
| **Custom Cookie** | Based on cookie value |

### Geographic Targeting

Target by location:

- Country (US, UK, Germany, etc.)
- Region/State
- City

### Time-Based Targeting

Run experiments at specific times:

- Days of week (weekdays vs weekends)
- Time of day (business hours)
- Date range (holiday campaign)

---

## Managing Active Experiments

### Monitoring Performance

While an experiment runs, monitor:

| Metric | What to look for |
|--------|------------------|
| **Visitors** | Enough sample size? |
| **Conversions** | Goals being triggered? |
| **Confidence** | Reaching 95%? |
| **Data issues** | Any anomalies? |

### Pausing an Experiment

Pause when:
- Technical issues arise
- You need to fix a bug in a variation
- External event affects results (e.g., site down)

To pause:
1. Go to **Experiments** → Select your experiment
2. Click **Pause**
3. Experiment stops immediately
4. Click **Resume** when ready

### Stopping an Experiment

Stop when:
- Results are conclusive
- Experiment ran long enough
- Critical issue requires stopping

To stop:
1. Click **Stop Experiment**
2. Choose to implement winner or just stop
3. Experiment cannot be resumed

### Deleting an Experiment

Delete (archive) when:
- Test was a mistake
- Cleaning up old experiments

To delete:
1. Experiment must be stopped or in draft
2. Click **Delete**
3. Data is archived, not destroyed

---

## Multi-Element Testing

Multi-element experiments test several page elements simultaneously.

### When to Use

- Testing a complete page redesign
- Optimizing multiple CTAs at once
- Testing element interactions

### How It Works

```
Experiment: "Homepage Optimization"
├── Element 1: Hero Headline
│   ├── Control: "Welcome to Our Site"
│   └── Variant A: "Transform Your Business"
├── Element 2: CTA Button
│   ├── Control: "Sign Up"
│   ├── Variant A: "Get Started"
│   └── Variant B: "Try Free"
└── Element 3: Hero Image
    ├── Control: [person-image.jpg]
    └── Variant A: [product-image.jpg]
```

### Combination Tracking

The system tracks all combinations:
- Headline A + Button A + Image Control
- Headline A + Button B + Image A
- etc.

With adaptive allocation, the best **combination** gets more traffic.

### Best Practices for Multi-Element

1. **Limit elements**: 2-3 elements max
2. **Limit variations**: 2-3 per element
3. **More traffic needed**: Combinations multiply required sample size
4. **Longer runtime**: Allow more time for significance

---

## Best Practices

### Before You Start

| ✅ Do | ❌ Don't |
|-------|---------|
| Form a clear hypothesis | Test randomly |
| Calculate required sample size | Run with tiny traffic |
| Document expected outcomes | Forget why you're testing |
| Check tracking is working | Launch without verification |

### During the Experiment

| ✅ Do | ❌ Don't |
|-------|---------|
| Be patient | Stop early on "good" results |
| Monitor for errors | Ignore data issues |
| Keep notes on observations | Forget what you learned |
| Run for at least 7 days | Stop after 2 days |

### After the Experiment

| ✅ Do | ❌ Don't |
|-------|---------|
| Wait for 95% significance | Declare winner at 80% |
| Implement the winner | Ignore results |
| Document learnings | Repeat same mistakes |
| Plan next experiment | Stop testing |

### Statistical Guidelines

| Guideline | Recommendation |
|-----------|----------------|
| **Minimum sample** | 100+ conversions per variation |
| **Running time** | At least 7 days (full weeks) |
| **Significance** | 95% or higher |
| **Minimum lift** | Depends on baseline |

### Common Mistakes to Avoid

1. **Peeking too often**: Checking results hourly leads to false positives
2. **Stopping too early**: Wait for statistical significance
3. **Too many variations**: Dilutes traffic, extends wait time
4. **Not documenting**: You'll forget what you learned
5. **Ignoring segments**: Overall winner may lose in key segments

---

## Support

Need help with experiments?

- 📖 **Knowledge Base**: [help.Sampelit.com](https://help.Sampelit.com)
- 📧 **Email**: support@Sampelit.com
- 💬 **Live Chat**: Available in dashboard

---

*Test smarter, optimize faster.*
