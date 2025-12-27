# Lifecycle Emails

**Objetivo:** Retención, recuperación, upsell  
**Complementa:** `onboarding_emails.md` (post-signup)

---

## Resumen de Secuencia

| # | Email | Trigger | Objetivo |
|---|-------|---------|----------|
| 1 | Experiment Completed | Exp llega a 95% confidence | Siguiente acción |
| 2 | Inactive Warning | 14 días sin login | Re-engagement |
| 3 | Churn Prevention | Cancellation iniciada | Salvar cliente |
| 4 | Churn Exit Survey | Cancellation completada | Feedback |
| 5 | Win-back | 30 días post-cancel | Re-adquisición |
| 6 | Win-back Reminder | 45 días post-cancel | Último intento |
| 7 | Upgrade Nudge | Hitting plan limits | Upsell |
| 8 | Annual Upsell | 10 meses en plan mensual | Conversión anual |
| 9 | Renewal Reminder | 7 días antes de renovar | Reducir sorpresas |
| 10 | Payment Failed | Pago rechazado | Recuperar pago |

---

## Email 1: Experiment Completed

**Trigger:** Experimento llega a 95%+ confidence  
**Subject:** Your experiment has a winner  
**Preview text:** [Experiment name] just reached statistical significance

---

Hi,

Good news: **{{experiment_name}}** just hit statistical significance.

**Results:**

| Variant | Conversion Rate | vs Control |
|---------|-----------------|------------|
| Control | {{control_rate}}% | — |
| {{winner_name}} | {{winner_rate}}% | **+{{lift}}%** |

Confidence: {{confidence}}%

→ [View full results]

---

**What to do next:**

1. **Implement the winner** — Update your site with {{winner_name}}
2. **Archive this experiment** — Keeps your dashboard clean
3. **Start your next test** — Momentum matters

Not sure what to test next? Here's a good sequence:
Headlines → CTAs → Social proof → Pricing display

→ [Create next experiment]

—
[Name]
Sampelit

---

**Technical notes:**
- Dynamic fields: experiment_name, control_rate, winner_name, winner_rate, lift, confidence
- Only send when confidence ≥ 95%
- Include mini-chart if possible

---

## Email 2: Inactive Warning

**Trigger:** 14 días sin login + tiene experimentos activos  
**Subject:** Your experiments are still running  
**Preview text:** Quick check-in on your tests

---

Hi,

It's been a couple weeks since you logged in.

Just wanted to let you know: **{{active_experiments}} experiment(s)** are still running and collecting data.

**Quick status:**

{{#each experiments}}
- **{{name}}**: {{visitors}} visitors, {{confidence}}% confidence
{{/each}}

→ [Check your dashboard]

---

No action needed if everything's running as planned. But if you meant to pause or adjust anything, now's a good time.

Questions? Just reply.

—
[Name]
Sampelit

---

**Technical notes:**
- Only send if active_experiments > 0
- Skip if user logged in within last 48h
- Max 1 inactive email per 30 days

---

## Email 3: Churn Prevention

**Trigger:** Usuario hace click en "Cancel subscription"  
**Subject:** Before you go...  
**Preview text:** Quick question (and an offer)

---

Hi,

I saw you started to cancel your Sampelit subscription.

Before you go, I'm curious: **what's not working?**

- [ ] Too expensive
- [ ] Not getting results
- [ ] Too complicated
- [ ] Switched to another tool
- [ ] Project ended / don't need it anymore
- [ ] Something else

Just reply with a number (or tell me in your own words). I read every response.

---

**If it's a timing issue:**

You can pause your subscription for up to 3 months instead of canceling. Your experiments and data stay intact.

→ [Pause instead of cancel]

---

**If it's a pricing issue:**

I can offer you **50% off your next 2 months** while you figure things out.

→ [Apply discount]

---

Either way, I'd genuinely like to know what we could do better.

—
[Name]
Sampelit

P.S. — If you do cancel, you'll have access until {{end_date}}. Your data stays available for 30 days after that.

---

**Technical notes:**
- Trigger on cancel button click, NOT on completed cancellation
- Show in-app as interstitial before confirming cancel
- Also send as email if they abandon the cancel flow
- Dynamic: end_date = current period end

---

## Email 4: Churn Exit Survey

**Trigger:** Cancellation completada  
**Subject:** Thanks for trying Sampelit  
**Preview text:** One quick question

---

Hi,

Your subscription has been canceled. You'll have access until {{end_date}}.

I have one quick question that would really help us improve:

**What was the main reason you canceled?**

→ [Too expensive]
→ [Didn't get the results I wanted]
→ [Too hard to use]
→ [Switched to a competitor]
→ [Don't need A/B testing right now]
→ [Other]

Just click one—takes 2 seconds.

---

A few things to know:

- **Your data** stays accessible for 30 days
- **Your experiments** are paused (not deleted)
- **You can reactivate** anytime and pick up where you left off

Thanks for giving Sampelit a try. I hope we cross paths again.

—
[Name]
Sampelit

---

**Technical notes:**
- Send immediately after cancellation confirmed
- Links go to feedback page with pre-selected reason
- Track responses in database for analysis
- No discount offer here (that was in Email 3)

---

## Email 5: Win-back (30 days)

**Trigger:** 30 días después de cancelación  
**Subject:** Things have changed  
**Preview text:** Quick update + an offer

---

Hi,

It's been a month since you left Sampelit.

A few things have changed since then:

- **[New feature 1]** — [One line description]
- **[New feature 2]** — [One line description]
- **[Improvement]** — [One line description]

*(Update this section with actual recent changes)*

---

If you want to give it another try, I'll make it easy:

**Come back at 50% off for 3 months.**

That's {{plan_name}} for just {{discounted_price}}/month.

→ [Reactivate with discount]

Your previous experiments and data are still there—you can pick up right where you left off.

—
[Name]
Sampelit

P.S. — This offer expires in 7 days.

---

**Technical notes:**
- Dynamic: plan_name = their last plan, discounted_price = 50% of that
- Use unique coupon code per user
- Track redemption rate
- Expiration creates urgency

---

## Email 6: Win-back Reminder (45 days)

**Trigger:** 45 días post-cancel + no reactivó  
**Subject:** Last chance: 50% off expires tomorrow  
**Preview text:** Your discount is about to expire

---

Hi,

Quick reminder: your 50% off offer expires tomorrow.

If you've been thinking about coming back to Sampelit, now's the time.

→ [Reactivate at 50% off]

After tomorrow, it's back to regular pricing.

—
[Name]

---

**Technical notes:**
- Only send if they didn't redeem Email 5 offer
- Short and direct
- Last email in win-back sequence

---

## Email 7: Upgrade Nudge

**Trigger:** Usuario alcanza 80% de límites del plan  
**Subject:** You're growing  
**Preview text:** Heads up on your usage

---

Hi,

Good news: you're using Sampelit a lot.

**Your current usage:**

| Limit | Used | Plan Max |
|-------|------|----------|
| Experiments | {{exp_used}} | {{exp_max}} |
| Visitors | {{visitors_used}} | {{visitors_max}} |
| Websites | {{sites_used}} | {{sites_max}} |

You're at **{{usage_percent}}%** of your {{current_plan}} plan.

---

**When you hit the limit:**

- Existing experiments keep running
- You won't be able to create new ones
- No automatic charges or upgrades

---

**If you want more room:**

{{next_plan}} gives you {{next_exp_max}} experiments, {{next_visitors_max}} visitors, and {{next_sites_max}} websites for {{next_price}}/month.

→ [Compare plans]
→ [Upgrade to {{next_plan}}]

No pressure—just wanted you to know before you hit the wall.

—
[Name]
Sampelit

---

**Technical notes:**
- Trigger at 80% of any limit (experiments, visitors, or sites)
- Don't send more than once per 30 days
- Show specific limits they're approaching
- Dynamic pricing based on current plan

---

## Email 8: Annual Upsell

**Trigger:** 10 meses en plan mensual  
**Subject:** You've been with us 10 months  
**Preview text:** Quick way to save {{annual_savings}}

---

Hi,

You've been using Sampelit for 10 months now. Thanks for sticking with us.

Quick thought: you're on monthly billing at {{monthly_price}}/month.

**If you switch to annual:**

- Monthly cost: {{annual_monthly_price}}/month (20% less)
- You'd save: **{{annual_savings}}/year**
- Locks in current pricing

→ [Switch to annual billing]

You can switch anytime. The change applies at your next billing date, and we'll prorate any difference.

—
[Name]
Sampelit

---

**Technical notes:**
- Only for users on monthly plans
- Send at month 10 (gives them 2 months to decide before year mark)
- Calculate actual savings based on their plan
- One-time email, don't repeat

---

## Email 9: Renewal Reminder

**Trigger:** 7 días antes de renovación (annual plans only)  
**Subject:** Your subscription renews in 7 days  
**Preview text:** Just a heads up

---

Hi,

Quick heads up: your Sampelit subscription ({{plan_name}}) renews on **{{renewal_date}}**.

**Amount:** {{price}}
**Card ending:** {{card_last4}}

No action needed if everything looks good.

---

**Need to make changes?**

- [Update payment method]
- [Change plan]
- [Cancel subscription]

Changes made before {{renewal_date}} will apply to your next billing cycle.

—
[Name]
Sampelit

---

**Technical notes:**
- Annual plans only (monthly is predictable enough)
- Send 7 days before renewal
- Include last 4 digits of card for clarity
- Required in some jurisdictions

---

## Email 10: Payment Failed

**Trigger:** Pago rechazado  
**Subject:** Your payment didn't go through  
**Preview text:** Quick fix needed

---

Hi,

We tried to charge your card for Sampelit ({{plan_name}}) but it didn't go through.

**What happened:**
- Amount: {{price}}
- Card ending: {{card_last4}}
- Error: {{error_reason}}

**What to do:**

→ [Update payment method]

We'll retry automatically in 3 days. If the payment fails again, your account will be paused (but not deleted).

---

**Common fixes:**

- Card expired? Update to a new one
- Insufficient funds? We'll retry in 3 days
- Card blocked? Contact your bank and whitelist sampelit.com

Questions? Just reply.

—
[Name]
Sampelit

---

**Technical notes:**
- Send immediately on failed payment
- Retry schedule: Day 0, Day 3, Day 7, Day 14
- After 4 failures, pause account
- error_reason from Stripe: card_declined, insufficient_funds, expired_card, etc.

---

## Dunning Sequence (Payment Recovery)

**Full sequence for failed payments:**

| Day | Action |
|-----|--------|
| 0 | Email 10 (Payment Failed) |
| 3 | Retry charge + Email if still failing |
| 7 | Retry charge + "Account will be paused soon" |
| 14 | Final retry + Pause account if failed |
| 30 | Win-back email with reactivation link |

---

### Dunning Email: Day 3

**Subject:** We'll try your payment again today  
**Preview text:** Just a heads up

---

Hi,

Quick update: we'll retry your payment for Sampelit today.

If your card still doesn't work, you can update it here:

→ [Update payment method]

—
[Name]

---

### Dunning Email: Day 7

**Subject:** Your account will be paused soon  
**Preview text:** Action needed to keep your experiments running

---

Hi,

We've tried to charge your card twice now and it's not going through.

**If we can't process payment by {{pause_date}}:**
- Your account will be paused
- Active experiments will stop collecting data
- Your data won't be deleted

→ [Update payment method now]

This takes 30 seconds and keeps everything running.

—
[Name]
Sampelit

---

### Dunning Email: Day 14 (Account Paused)

**Subject:** Your Sampelit account has been paused  
**Preview text:** Your experiments have stopped

---

Hi,

After several failed payment attempts, your Sampelit account has been paused.

**What this means:**
- Your experiments have stopped collecting data
- Your dashboard is read-only
- Your data is safe (we keep it for 90 days)

**To reactivate:**

→ [Update payment and reactivate]

Once payment goes through, your account is instantly restored and experiments resume.

Questions? Just reply.

—
[Name]
Sampelit

---

## Email Timing Summary

| Email | When | Frequency |
|-------|------|-----------|
| Experiment Completed | On event | Per experiment |
| Inactive Warning | Day 14 no login | Max 1/30 days |
| Churn Prevention | Cancel initiated | Once |
| Exit Survey | Cancel completed | Once |
| Win-back | Day 30 post-cancel | Once |
| Win-back Reminder | Day 45 post-cancel | Once |
| Upgrade Nudge | 80% of limits | Max 1/30 days |
| Annual Upsell | Month 10 | Once |
| Renewal Reminder | 7 days before renewal | Per renewal (annual only) |
| Payment Failed | On event | Per failure + dunning sequence |

---

## Implementation Checklist

- [ ] Set up triggers in backend for each email
- [ ] Create email templates in Resend
- [ ] Add dynamic fields (experiment names, prices, dates)
- [ ] Test each email with real scenarios
- [ ] Set up dunning sequence in Stripe (or manual)
- [ ] Create feedback tracking for exit survey
- [ ] Generate unique coupon codes for win-back
- [ ] Test pause/reactivation flow
- [ ] Set up retry logic for failed payments
- [ ] Add unsubscribe link to all emails
- [ ] Track metrics per email

---

## Metrics to Track

| Email | Key Metric | Target |
|-------|------------|--------|
| Experiment Completed | Click to results | >50% |
| Inactive Warning | Re-login within 48h | >30% |
| Churn Prevention | Cancel prevented | >15% |
| Exit Survey | Response rate | >25% |
| Win-back (30d) | Reactivation rate | >5% |
| Win-back Reminder | Reactivation rate | >3% |
| Upgrade Nudge | Upgrade within 7d | >10% |
| Annual Upsell | Switch to annual | >8% |
| Payment Failed | Payment recovered | >70% |
