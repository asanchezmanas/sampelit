# Lifecycle Email Sequence

> **Purpose:** Retain users, prevent churn, win back churned users
> **Complement to:** onboarding_emails.md (first 28 days)

---

## Email 1: Experiment Completed

**Trigger:** Experiment reaches 95% confidence  
**Subject:** [Experiment name] has a winner

---

Hi,

Your experiment **"[Experiment name]"** just reached statistical significance.

**Results:**
- Winner: [Variant name]
- Confidence: [X]%
- Conversion uplift: [+X.X]%
- Traffic tested: [X,XXX] visitors

→ [View complete results](link)

**Recommended next steps:**
1. Implement the winner permanently
2. Archive this experiment
3. Start testing your next element

What to test next? [Here are 5 high-impact ideas](link)

—
Sampelit

---

## Email 2: Inactivity Warning

**Trigger:** 14 days since last login  
**Subject:** Your experiments miss you

---

Hi,

It's been 2 weeks since you logged in to Sampelit.

**Your account status:**
- Active experiments: [X]
- Experiments waiting for review: [X]
- Unused capacity: [X] experiments available

If you're busy—totally fine. Your experiments are still running.

If something's not working—tell me. Just reply.

→ [Back to dashboard](link)

—
[Founder name]

P.S. — If you're stuck on what to test next, [here's a 3-minute guide](link).

---

## Email 3: Churn Prevention

**Trigger:** Cancellation initiated (before confirmed)  
**Subject:** Before you go...

---

Hi,

I saw you started canceling your Sampelit subscription.

Before you confirm, I have one question:

**What could we have done differently?**

Your feedback helps us improve—even if you leave.

**Common reasons people cancel:**
- [ ] Not enough traffic to test
- [ ] Too complex to set up
- [ ] Results weren't clear
- [ ] Budget constraints
- [ ] Switched to another tool
- [ ] Something else

Click any option above to respond (or just reply).

**If it's budget:** We have a 50% discount for startups. Reply and I'll check if you qualify.

**If it's complexity:** Book a [15-min walkthrough](link) with me. Free.

No hard feelings either way.

—
[Founder name]

---

## Email 4: Win-Back

**Trigger:** 30 days post-cancellation  
**Subject:** Things have changed

---

Hi,

It's been a month since you left Sampelit.

A few things have improved since then:

**Recent updates:**
- [New feature 1]
- [New feature 2]
- [Bug fix / improvement]

**Special offer:**
Come back with 30% off your first 3 months.

Use code: COMEBACK30 at checkout.
→ [Reactivate account](link)

Valid for 7 days.

No pressure. If now's not the right time, I understand.

—
[Founder name]

---

## Email 5: Upgrade Nudge

**Trigger:** Usage at 80% of plan limit  
**Subject:** You're growing fast

---

Hi,

Your experiments are doing well.

**Your usage this month:**
- Visitors tested: [X] of [limit] (80%)
- Experiments: [X] of [limit]

At this pace, you'll hit your limit in ~[X] days.

**What happens at the limit:**
- Experiments keep running
- New experiments paused until next billing cycle
- No data lost

**Upgrade options:**
- Professional: 100k visitors, 25 experiments — €399/mo
- Scale: 500k visitors, unlimited experiments — €999/mo

→ [Upgrade now](link)

Or reply if you have questions about which plan fits.

—
Sampelit

---

## Summary Table

| Email | Trigger | Purpose | Tone |
|-------|---------|---------|------|
| 1 | Experiment complete | Celebrate + next steps | Positive |
| 2 | 14 days inactive | Re-engage | Gentle |
| 3 | Cancel initiated | Save the customer | Understanding |
| 4 | 30 days post-cancel | Win back | Humble offer |
| 5 | 80% usage | Upsell | Helpful |

---

## Technical Triggers

```python
# Email 1 - Experiment Completed
if experiment.confidence >= 0.95 and not experiment.result_email_sent:
    send_email("experiment_completed", user)
    experiment.result_email_sent = True

# Email 2 - Inactivity Warning
if days_since_login >= 14 and not user.inactive_warning_sent:
    send_email("inactive_warning", user)
    user.inactive_warning_sent = True

# Email 3 - Churn Prevention
on cancel_initiated:
    send_email("churn_prevention", user)

# Email 4 - Win-Back
if days_since_cancel >= 30 and not user.winback_sent:
    send_email("winback_offer", user)
    user.winback_sent = True

# Email 5 - Upgrade Nudge
if usage_percent >= 80 and not user.upgrade_nudge_sent_this_cycle:
    send_email("upgrade_nudge", user)
    user.upgrade_nudge_sent_this_cycle = True
```
