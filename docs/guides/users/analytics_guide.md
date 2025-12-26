# Analytics Guide

> **Samplit A/B Testing Platform**  
> Understanding your experiment results

---

## Table of Contents

1. [Overview](#overview)
2. [The Results Dashboard](#the-results-dashboard)
3. [Key Metrics Explained](#key-metrics-explained)
4. [Bayesian Statistics in Samplit](#bayesian-statistics-in-samplit)
5. [Reading the Confidence Score](#reading-the-confidence-score)
6. [Understanding Lift](#understanding-lift)
7. [Segment Analysis](#segment-analysis)
8. [Revenue Tracking](#revenue-tracking)
9. [Exporting Data](#exporting-data)
10. [Making Decisions](#making-decisions)

---

## Overview

Samplit uses **Bayesian statistics** to analyze your experiment results. This approach provides:

- **Faster insights**: Get actionable results sooner
- **Probability-based decisions**: "There's a 95% chance A is better than B"
- **Expected loss calculation**: Know what you're risking with each decision
- **No fixed sample sizes**: Adapt as data comes in

---

## The Results Dashboard

Navigate to **Experiments** → Select your experiment → **Results**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Homepage CTA Test                                                      │
│  Status: Running │ Started: Dec 20, 2024 │ Duration: 5 days             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │           SUMMARY                                                │   │
│  │  Visitors: 15,234    Conversions: 892    CR: 5.85%              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  VARIATION      VISITORS   CONV    RATE     CONF     CHANGE    │   │
│  │  ─────────────────────────────────────────────────────────────  │   │
│  │  Control         5,089     271    5.32%      —         —        │   │
│  │  Variant A       5,073     342    6.74%    97.2%    +26.7% 🏆   │   │
│  │  Variant B       5,072     279    5.50%    68.4%    +3.4%       │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │          [📊 Chart View]  [📋 Table View]  [📁 Export]          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  AI RECOMMENDATION: Variant A shows a strong improvement. Consider     │
│  implementing after reaching 99% confidence.                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Dashboard Sections

| Section | Contents |
|---------|----------|
| **Summary** | Overall experiment metrics |
| **Variation Table** | Per-variation performance |
| **Charts** | Visual trends over time |
| **Recommendations** | AI-generated insights |

---

## Key Metrics Explained

### Visitors

The number of unique visitors who saw each variation.

```
Visitors = Unique users assigned to this variation
```

Note: A visitor is counted once, even if they return multiple times.

### Conversions

The number of visitors who completed your goal.

```
Conversions = Users who triggered the goal event
```

### Conversion Rate

The percentage of visitors who converted.

```
Conversion Rate = (Conversions / Visitors) × 100
```

**Example**:
- Visitors: 1,000
- Conversions: 50
- Rate: 50/1000 × 100 = **5.0%**

### Confidence

The probability that this variation is better than the control.

```
Confidence = Probability(Variant beats Control)
```

**How to interpret**:
| Confidence | Meaning |
|------------|---------|
| 50% | No difference from control (coin flip) |
| 75% | Likely better, but not certain |
| 90% | Probably better, moderate confidence |
| 95% | Very likely better, high confidence |
| 99% | Almost certainly better |

### Lift (Improvement)

The percentage improvement over control.

```
Lift = ((Variant Rate - Control Rate) / Control Rate) × 100
```

**Example**:
- Control: 5.0%
- Variant A: 6.0%
- Lift: (6.0 - 5.0) / 5.0 × 100 = **+20%**

---

## Bayesian Statistics in Samplit

### Traditional vs Bayesian

| Traditional (Frequentist) | Samplit (Bayesian) |
|---------------------------|---------------------|
| "Is A different from B?" | "How likely is A better than B?" |
| P-values and significance | Probability distributions |
| Fixed sample sizes | Continuous monitoring |
| Yes/No answer | Probability with confidence |

### How Bayesian Analysis Works

1. **Start with prior beliefs**: Initially, we assume all variations are equal
2. **Update with data**: As conversions happen, beliefs are updated
3. **Calculate posteriors**: Compute probability distributions for each variation
4. **Compare distributions**: Determine which variation is likely best

### Probability of Being Best

For each variation, we calculate:

```
P(Best) = Probability this variation has the highest true conversion rate
```

**Interpretation**:
- Variant A: 85% probability of being best
- Variant B: 10% probability of being best
- Control: 5% probability of being best

This means: If you had to choose now, Variant A is most likely the winner.

### Expected Loss

Even if Variant A seems best, what do you risk by choosing it?

```
Expected Loss = Average potential regret if you choose this variation
```

**Example**:
| Variation | P(Best) | Expected Loss |
|-----------|---------|---------------|
| Variant A | 92% | 0.02% CR |
| Control | 8% | 0.45% CR |

Choosing Variant A risks losing 0.02% conversion rate if you're wrong.
Choosing Control risks losing 0.45% conversion rate if you're wrong.

This makes the decision clear: Choose Variant A.

---

## Reading the Confidence Score

### What Confidence Means

The confidence score is the probability that the variation beats the control:

```
97.2% Confidence = 97.2% chance this is genuinely better
```

### When to Make Decisions

| Confidence | Action |
|------------|--------|
| < 75% | Wait for more data |
| 75-90% | Promising, but wait |
| 90-95% | Consider implementing if time-sensitive |
| 95-99% | Ready to implement |
| 99%+ | Strong winner, implement |

### Common Questions

**Q: Why not just wait for 100%?**
A: You'll never reach 100%. Even 99.9% leaves room for rare outcomes.

**Q: Can confidence go down?**
A: Yes! If later data contradicts early results, confidence will adjust.

**Q: Is 95% a magic number?**
A: It's a convention. For low-risk changes, 90% may be fine. For critical changes, prefer 99%.

---

## Understanding Lift

### Interpreting Lift Values

| Lift | Interpretation |
|------|----------------|
| +50% or more | Exceptional improvement |
| +20% to +50% | Strong improvement |
| +5% to +20% | Moderate improvement |
| +1% to +5% | Small improvement |
| 0% to +1% | Negligible difference |
| Negative | Variation performs worse |

### Credible Intervals

Lift is an estimate. The true value lies within a range:

```
Lift: +15.2%
95% Credible Interval: [+8.3%, +22.1%]
```

This means: We're 95% sure the true improvement is between 8.3% and 22.1%.

### Lift Over Time

Watch how lift evolves:

```
Day 1:  +35%  (unstable, small sample)
Day 3:  +22%  (more data)
Day 7:  +18%  (stabilizing)
Day 14: +16%  (converging)
```

Early lift values are unreliable. Wait for convergence.

---

## Segment Analysis

### What is Segmentation?

Breaking down results by user characteristics:

- Device type (mobile vs desktop)
- Geography (US vs UK)
- Traffic source (organic vs paid)
- New vs returning visitors

### Viewing Segments

1. In Results, click **Segments**
2. Choose a segment dimension
3. View results for each segment

### Example: Device Segmentation

```
┌─────────────────────────────────────────────────────────┐
│  DESKTOP                                                │
│  Variant A: +28% lift, 97% confidence 🏆                │
├─────────────────────────────────────────────────────────┤
│  MOBILE                                                 │
│  Variant A: -5% lift, 72% confidence                    │
└─────────────────────────────────────────────────────────┘
```

**Insight**: Variant A wins on desktop but may hurt mobile!

### Using Segment Insights

1. **Identify underperforming segments**: Fix issues or target differently
2. **Find winning segments**: Double down on what works
3. **Create segment-specific variations**: Personalize by device/location

---

## Revenue Tracking

### Enabling Revenue Tracking

For e-commerce experiments:

1. Ensure your tracker sends order values
2. Set goal type to **Revenue**
3. Track average order value (AOV) and total revenue

### Revenue Metrics

| Metric | Description |
|--------|-------------|
| **Total Revenue** | Sum of all order values |
| **Revenue per Visitor** | Total Revenue / Visitors |
| **Average Order Value** | Total Revenue / Orders |
| **Revenue Lift** | % improvement in revenue per visitor |

### Example Revenue Results

```
┌─────────────────────────────────────────────────────────────────┐
│  VARIATION      VISITORS   ORDERS   REVENUE      RPV    CONF   │
│  ─────────────────────────────────────────────────────────────  │
│  Control         10,000     320    $32,000    $3.20     —      │
│  Variant A       10,000     385    $42,350    $4.24   95.8%    │
└─────────────────────────────────────────────────────────────────┘

Revenue Lift: +32.4% ($0.89 per visitor)
```

### Revenue vs Conversion Rate

Sometimes these diverge:

| Scenario | Conversion Rate | Revenue |
|----------|-----------------|---------|
| More orders, lower AOV | ⬆ Higher | ⬇ Lower |
| Fewer orders, higher AOV | ⬇ Lower | ⬆ Higher |
| Premium upsell works | Same | ⬆ Higher |

Choose the metric that matches your business goals.

---

## Exporting Data

### Export Options

| Format | Use Case |
|--------|----------|
| **CSV** | Spreadsheet analysis (Excel, Sheets) |
| **JSON** | Programmatic access, APIs |
| **PDF** | Reports for stakeholders |

### How to Export

1. Go to Results page
2. Click **Export**
3. Choose format
4. Download file

### What's Included

- Summary metrics
- Per-variation data
- Daily breakdowns
- Segment data (if available)
- Statistical analysis

---

## Making Decisions

### Decision Framework

```
┌─────────────────────────────────────────────────────────┐
│                CONFIDENCE ≥ 95%?                        │
├──────────────────┬──────────────────────────────────────┤
│       YES        │              NO                      │
│                  │                                      │
│  Is the lift     │   Do you have enough data?          │
│  meaningful?     │                                      │
│                  │   • < 100 conversions? → Wait        │
│  YES → Implement │   • < 7 days running? → Wait         │
│  NO → Consider   │   • Confidence dropping? → May tie   │
│       scale      │                                      │
└──────────────────┴──────────────────────────────────────┘
```

### When to Implement

✅ **Implement when**:
- Confidence ≥ 95%
- Lift is meaningful (worth the effort)
- Expected loss is acceptable
- Ran for at least 1-2 full weeks

### When to Wait

⏳ **Wait when**:
- Confidence is between 80-95%
- You don't have enough conversions
- It hasn't run for a full week
- Results swing back and forth

### When to Stop Without a Winner

⛔ **End the test when**:
- No variation shows meaningful improvement after 4+ weeks
- Confidence stays below 75% indefinitely
- The test is blocking other priorities

**What to do**:
1. Document learnings
2. Form a new hypothesis
3. Try a bigger, bolder change

### AI Recommendations

Samplit provides automated recommendations:

| Recommendation | Meaning |
|----------------|---------|
| "Continue testing" | Not enough data yet |
| "Consider implementing" | Likely winner, verify first |
| "Implement Variant X" | High confidence winner |
| "No clear winner" | Variations are too similar |
| "Variant X is underperforming" | Consider stopping it |

---

## FAQ

### How long should I run an experiment?

At minimum:
- 7 days (to capture weekly patterns)
- 100+ conversions per variation
- Until reaching 95% confidence

### Can I trust early results?

Early results are noisy. A variation showing +50% on day 1 might only be +5% by day 14. Wait for stabilization.

### What if results conflict with intuition?

Trust the data, but:
1. Check for tracking issues
2. Verify the experiment was set up correctly
3. Consider segment analysis—maybe it works for some users

### Why did confidence drop?

New data contradicted earlier data. This is normal and shows the system is working correctly.

### What's a good conversion rate improvement to aim for?

Depends on your baseline:
- High baseline (>20%): 5-10% lift is good
- Medium baseline (5-20%): 10-20% lift is good
- Low baseline (<5%): 20%+ lift is possible

---

## Support

Need help understanding your results?

- 📖 **Knowledge Base**: [help.samplit.com](https://help.samplit.com)
- 📧 **Email**: support@samplit.com
- 💬 **Live Chat**: Available in dashboard

---

*Measure, learn, improve—repeat.*
