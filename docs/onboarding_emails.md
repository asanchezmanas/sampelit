# Onboarding Email Sequence (Post-Payment)

**Trigger:** Usuario completa pago  
**Objetivo:** Activación rápida, reducir abandono, crear hábito

---

## Resumen de Secuencia

| # | Email | Trigger | Timing |
|---|-------|---------|--------|
| 1 | Welcome + Quick Start | Pago completado | Inmediato |
| 2 | Tracker Check | Sin datos de tracker | Día 3 |
| 3 | First Experiment | Sin experimentos creados | Día 5 |
| 4 | First Results | Primer resultado O día 14 | Variable |
| 5 | Tips & Best Practices | Día 21 | Día 21 |
| 6 | Check-in + NPS | Día 28 (pre-renewal) | Día 28 |

---

## Email 1: Welcome + Quick Start

**Trigger:** Inmediato después del pago  
**Subject:** You're in. Here's how to start.  
**Preview text:** Setup takes about 10 minutes.

---

Hi,

Your Sampelit account is ready.

Here's what to do next (takes about 10 minutes):

**Step 1: Install the tracker**

Copy one line of code into your site's <head> tag.

```html
<script src="https://cdn.sampelit.com/tracker.js" data-site="YOUR_SITE_ID"></script>
```

→ Full installation guide: [link]

**Step 2: Create your first experiment**

Start with your homepage headline. It's the highest-leverage test for most sites.

→ Create experiment: [link]

**Step 3: Wait for data**

You'll see results within 7-14 days depending on your traffic. The dashboard shows estimated time to significance.

---

Questions? Reply to this email. I read everything.

—  
[Name]  
Sampelit

P.S. — Stuck on installation? Here's a 2-minute walkthrough: [video link]

---

**CTA Button:** Go to Dashboard

---

## Email 2: Tracker Check

**Trigger:** Day 3 AND no tracking data received  
**Subject:** Quick check: is your tracker installed?  
**Preview text:** We haven't received data yet.

---

Hi,

It's been a few days and we haven't received any data from your site yet.

This usually means one of three things:

1. **Tracker not installed yet** — Here's the code: [installation guide]

2. **Tracker on wrong pages** — Make sure it's in the <head> of pages you want to test

3. **Low traffic** — If your site gets <100 visitors/day, data takes longer to appear

**Quick debug:**

Open your browser console on your site and type:
```javascript
window.sampelit
```

If it returns an object, you're good. If undefined, the tracker isn't loading.

---

Need help? Reply with your site URL and I'll take a look.

—  
[Name]  
Sampelit

---

**CTA Button:** Check Installation Guide

---

## Email 3: First Experiment Nudge

**Trigger:** Day 5 AND no experiments created  
**Subject:** Ready to run your first test?  
**Preview text:** Here's a simple way to start.

---

Hi,

You've got the tracker installed. Next step: create your first experiment.

Not sure what to test? Start here:

**Easiest first test: Your headline**

Your homepage headline is seen by every visitor. Small changes often produce measurable results.

Try testing:
- Benefit-focused vs. feature-focused
- Question vs. statement
- Short vs. long

**How to set it up:**

1. Go to Experiments → New
2. Enter your page URL
3. Use Visual Editor to change the headline
4. Set traffic allocation (start with 50/50)
5. Launch

Takes about 5 minutes.

→ Create your first experiment: [link]

---

If you're not sure what to test, reply with your site URL. I'll suggest 2-3 high-impact tests.

—  
[Name]  
Sampelit

---

**CTA Button:** Create First Experiment

---

## Email 4: First Results

**Trigger:** First experiment reaches 95% confidence OR Day 14 (whichever first)  
**Subject A (results ready):** Your first results are in  
**Subject B (day 14, no results):** How's your first experiment going?

---

### Version A: Results Ready

Hi,

Your experiment just hit statistical significance.

**Quick summary:**

- Experiment: {{experiment_name}}
- Duration: {{days}} days
- Visitors: {{total_visitors}}
- Winner: {{winning_variant}}
- Improvement: {{lift_percentage}}%

→ See full results: [link]

**What to do next:**

1. **Implement the winner** — Update your site with the winning variant
2. **Archive the experiment** — Keeps your dashboard clean
3. **Start the next test** — Momentum matters in optimization

Not sure what to test next? Headlines → CTAs → Social proof → Pricing display is a good sequence.

—  
[Name]  
Sampelit

---

### Version B: No Results Yet (Day 14)

Hi,

Your experiment has been running for 2 weeks. Here's the current status:

- Visitors so far: {{total_visitors}}
- Current leader: {{leading_variant}}
- Confidence: {{confidence}}%
- Estimated time to significance: {{estimated_days}} more days

**Why it's taking time:**

Statistical significance requires enough data to be confident the difference isn't random. With your current traffic, this experiment needs approximately {{estimated_days}} more days.

**Options:**

1. **Keep running** — More data = more confidence
2. **Increase traffic allocation** — Send more visitors to the experiment
3. **Test a bigger change** — Larger differences are detected faster

→ View experiment: [link]

Questions about your results? Reply anytime.

—  
[Name]  
Sampelit

---

**CTA Button:** View Results

---

## Email 5: Tips & Best Practices

**Trigger:** Day 21  
**Subject:** 3 ways to get better test results  
**Preview text:** Quick tips from teams that test a lot.

---

Hi,

You've been testing for a few weeks. Here are three things that separate good testing programs from great ones:

**1. Test copy before design**

Copy changes are faster to implement and often produce larger lifts than design changes. Headlines, CTAs, and value propositions first. Colors and layouts later.

**2. Document your hypotheses**

Before each test, write down: "We believe [change] will [outcome] because [reason]." This forces clarity and helps you learn even from inconclusive tests.

**3. Run tests longer than you think**

Most teams stop too early. Even after hitting 95% confidence, consider running another few days to confirm. False positives are common with small sample sizes.

---

Want to go deeper? Here's our guide to avoiding the 7 most common testing mistakes: [link to blog]

—  
[Name]  
Sampelit

---

**CTA Button:** Read the Guide

---

## Email 6: Check-in + NPS

**Trigger:** Day 28 (4 days before renewal)  
**Subject:** Quick question (takes 10 seconds)  
**Preview text:** How's Sampelit working for you?

---

Hi,

You've been using Sampelit for almost a month. Quick question:

**How likely are you to recommend Sampelit to a colleague?**

[1] [2] [3] [4] [5] [6] [7] [8] [9] [10]

(1 = not likely, 10 = very likely)

Just click a number—it takes 2 seconds.

---

Also curious:

- What's working well?
- What's frustrating or missing?

Reply with anything. I read every response and it directly shapes what we build next.

—  
[Name]  
Sampelit

P.S. — Your subscription renews in 4 days. If you have any questions about your plan, just reply.

---

## Conditional Emails (Skip Logic)

| If user has... | Skip email... |
|----------------|---------------|
| Tracker data within 24h | Email 2 |
| Created experiment within 48h | Email 3 |
| No experiments after 14 days | Email 4 (send re-engagement instead) |

---

## Email Design Specs

**From:** name@sampelit.com  
**Reply-to:** name@sampelit.com (personal inbox)  
**Format:** Plain text preferred, minimal HTML

**If using HTML:**
- Max width: 600px
- Font: System font stack (-apple-system, sans-serif)
- Background: White
- Text color: #1a1a1a
- Link color: #2563eb
- No images in body (except logo in footer)
- Unsubscribe link in footer

---

## Metrics to Track

| Email | Key Metric | Target |
|-------|------------|--------|
| Email 1 | Open rate | >60% |
| Email 1 | Click rate (dashboard) | >40% |
| Email 2 | Tracker installed within 24h | >50% |
| Email 3 | Experiment created within 48h | >30% |
| Email 4 | Click to view results | >50% |
| Email 5 | Click to blog | >15% |
| Email 6 | NPS response rate | >20% |

---

## Implementation Checklist

- [ ] Create email templates in Resend
- [ ] Set up trigger conditions in backend
- [ ] Add dynamic fields (experiment name, metrics, etc.)
- [ ] Test each email with real account
- [ ] Set up NPS tracking endpoint
- [ ] Configure skip logic
- [ ] Test unsubscribe flow
- [ ] A/B test subject lines (future)
