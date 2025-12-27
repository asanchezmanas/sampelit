# Onboarding Email Sequence

> **Trigger:** User completes payment and creates account
> **Goal:** Activate users quickly and reduce churn

---

## Email 1: Welcome + Quick Start

**Trigger:** Immediate post-payment  
**Subject:** You're in. Here's how to start.

---

Hi,

Your Sampelit account is ready.

Here's what to do next (takes ~10 minutes):

**1. Install the tracker**
Copy one line of code into your site's <head>.
→ [Installation guide](link)

**2. Create your first experiment**
Start with your homepage headline—it's the highest-leverage test.
→ [Create experiment](link)

**3. Wait for data**
You'll see results within 7-14 days depending on your traffic.

Questions? Reply to this email. I read everything.

—
[Founder name]
Sampelit

P.S. — Stuck on installation? Here's a 2-minute video: [link]

---

## Email 2: Tracker Check

**Trigger:** Day 3 if no data received  
**Subject:** Quick check: is your tracker installed?

---

Hi,

I noticed we haven't received any data from your site yet.

This usually means one of three things:

1. **Tracker not installed** — [Check installation guide](link)
2. **Wrong domain configured** — Verify in [Settings](link)
3. **Low traffic** — Just needs more time

**Quick diagnostic:**
Open your browser console on your site and type: `window.sampelit`
If you see an object, you're connected.

Still stuck? Just reply to this email with your site URL and I'll check it personally.

—
[Founder name]

---

## Email 3: First Experiment Nudge

**Trigger:** Day 5 if no experiment created  
**Subject:** Ready to run your first experiment?

---

Hi,

Your tracker is working. Now let's put it to use.

**The best first experiment:**
Test your homepage headline. It's seen by everyone and has the highest impact.

**Quick setup (2 minutes):**
1. Go to [Create Experiment](link)
2. Enter your URL
3. Select your headline
4. Add 2-3 variants
5. Launch

**Variant inspiration:**
- Original: "The best tool for X"
- Variant A: "Stop doing X the hard way"
- Variant B: "X made simple"

Don't overthink it. The test will tell you what works.

→ [Create your first experiment](link)

—
[Founder name]

---

## Email 4: First Results Celebration

**Trigger:** First experiment reaches 95% confidence  
**Subject:** Your first result is in 🎉

---

Hi,

Congratulations—your first experiment has a result.

**Quick summary:**
- Experiment: [Experiment name]
- Winner: [Variant name]
- Confidence: [X]%
- Uplift: [+X.X]%

→ [View full results](link)

**What to do next:**
1. Implement the winning variant permanently
2. Archive the experiment
3. Start testing your next element

**Pro tip:** Now test your CTA button. Headlines get attention, CTAs drive action.

Keep testing,
[Founder name]

---

## Email 5: Tips for Better Tests

**Trigger:** Day 21  
**Subject:** 3 tips to get more from your experiments

---

Hi,

You've been using Sampelit for 3 weeks. Here are patterns we see in successful tests:

**1. Test bigger changes first**
"Sign Up" vs "Get Started" is a small change.
"Sign Up" vs "Start Your Free Trial Today" is bigger and easier to detect.

**2. Run tests for full cycles**
Don't stop on Monday. Weekend traffic behaves differently.
Minimum 7 days, ideally 14.

**3. Test one thing at a time**
Changing headline AND button text = you won't know which caused the change.

**Your stats so far:**
- Experiments run: [X]
- Tests completed: [X]
- Biggest win: [X]%

→ [View your dashboard](link)

Keep optimizing,
[Founder name]

---

## Email 6: Check-in + NPS

**Trigger:** Day 28 (pre-renewal)  
**Subject:** Quick question (takes 10 seconds)

---

Hi,

You're about to complete your first month with Sampelit.

I have one question for you:

**On a scale of 0-10, how likely are you to recommend Sampelit to a colleague?**

[0] [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]

Click a number above to respond.

Why? I want to know if we're building something useful.

If you have specific feedback (good or bad), just reply. I read every response.

Thank you,
[Founder name]

P.S. — If anything is frustrating or confusing, tell me. I'd rather fix it than have you leave silently.

---

## Sequence Diagram

```
Payment → Email 1 (Welcome)
              ↓
         Day 3: No data?
              ↓
         Email 2 (Tracker Check)
              ↓
         Day 5: No experiment?
              ↓
         Email 3 (First Experiment)
              ↓
         First result?
              ↓
         Email 4 (Results)
              ↓
         Day 21
              ↓
         Email 5 (Tips)
              ↓
         Day 28
              ↓
         Email 6 (NPS)
```

---

## Technical Triggers

| Email | Condition | Delay |
|-------|-----------|-------|
| 1 | payment_completed | Immediate |
| 2 | days_since_signup >= 3 AND events_received = 0 | — |
| 3 | days_since_signup >= 5 AND experiments_created = 0 | — |
| 4 | experiment_confidence >= 95% | Immediate |
| 5 | days_since_signup >= 21 | — |
| 6 | days_since_signup >= 28 | — |
