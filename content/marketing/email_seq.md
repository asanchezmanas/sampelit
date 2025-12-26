# Email Sequence — Waitlist to Customer

Premium brand voice. Europa Rica + Anglo target markets.

---

## Trigger

Email captured via `/api/v1/leads/capture` (simulator, landing page, or direct signup).

---

## Sequence Overview

| # | Timing | Subject | Purpose |
|---|--------|---------|---------|
| 1 | Immediate | Welcome + What's next | Set expectations, establish tone |
| 2 | Day 3 | The methodology | Educate, build credibility |
| 3 | Day 7 | Case study or invite | Social proof, conversion |

---

## Email 1: Welcome

**Timing:** Immediate
**Subject:** You're on the list

```
Hi,

You're on the Sampelit waitlist.

Here's what happens next:
- We're in private beta with a limited number of teams
- When a spot opens, we'll email you directly
- Early access includes the first year at a reduced rate

In the meantime, you might find these useful:

→ How the system works [link to /about]
→ Live demo (the one you saw) [link to /simulator]

No newsletters. No "we miss you" emails. Just the invite when it's ready.

—
Sampelit
Barcelona
```

**Notes:**
- No exclamation marks
- No "Welcome to the family!"
- Clear, direct, premium tone

---

## Email 2: The Methodology

**Timing:** 3 days after signup
**Subject:** How we decide which copy wins

```
Hi,

You signed up for the Sampelit waitlist. Here's a bit more about how the system works.

Most A/B testing tools split traffic 50/50 and wait. That's inefficient. Visitors who see underperforming variants are wasted opportunities.

We use adaptive allocation:

1. All variants start with equal traffic
2. As data accumulates, better-performing variants receive more traffic
3. Underperforming variants fade out automatically
4. Results are evaluated only when statistically meaningful

The result: faster decisions, less wasted traffic.

Every allocation decision is logged with a cryptographic hash. You can verify that results weren't manipulated after the fact.

More details: [link to methodology page or blog post]

—
Sampelit
```

**Notes:**
- Educational, not promotional
- Establishes technical credibility
- No call to action (yet)

---

## Email 3: The Invite (or Case Study)

**Timing:** 7 days after signup
**Subject:** [If invite available] Your spot is ready / [If waitlist] How a SaaS increased conversions 23%

### Version A: Invite Available

```
Hi,

A spot opened up. You can now access Sampelit.

What you get:
- Full access to the testing platform
- Visual Editor for non-technical setup
- Adaptive allocation from day one
- Audit trail for all decisions

Pricing:
- Starter: €149/month (5 experiments, 25k visitors)
- Professional: €399/month (25 experiments, 100k visitors)

Early adopters receive 50% off the first year.

Set up your account: [link]

If you have questions before starting, reply to this email.

—
Sampelit
```

### Version B: Still on Waitlist

```
Hi,

Still working through the waitlist. Here's something while you wait.

Case Study: [Company Name]

They were testing headlines manually. Picking based on team opinions. Running one test every few months.

After switching to adaptive testing:
- 23% increase in landing page conversions
- Test cycles reduced from 4 weeks to 10 days
- 3x more tests per quarter

The methodology is documented here: [link]

You're still on the list. We'll reach out when a spot opens.

—
Sampelit
```

---

## Technical Implementation

### Database Schema (leads table)

```sql
CREATE TABLE leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    source VARCHAR(50) DEFAULT 'simulator',
    variant VARCHAR(50),
    status VARCHAR(20) DEFAULT 'waitlist',
    email_1_sent_at TIMESTAMP,
    email_2_sent_at TIMESTAMP,
    email_3_sent_at TIMESTAMP,
    converted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_status ON leads(status);
```

### Email Service Integration

**Recommended:** Resend (€20/month, developer-friendly)
**Alternative:** ConvertKit, Postmark

```python
# Example: Send email via Resend
import resend

resend.api_key = os.getenv("RESEND_API_KEY")

def send_welcome_email(email: str):
    resend.Emails.send({
        "from": "Sampelit <hello@Sampelit.com>",
        "to": email,
        "subject": "You're on the list",
        "html": render_template("emails/welcome.html")
    })
```

### Cron Job (Email Scheduler)

```python
# Run daily at 10:00 UTC
async def send_scheduled_emails():
    leads = await get_leads_needing_emails()
    
    for lead in leads:
        if needs_email_2(lead):
            send_methodology_email(lead.email)
            mark_email_2_sent(lead.id)
        
        if needs_email_3(lead):
            send_invite_or_casestudy(lead.email)
            mark_email_3_sent(lead.id)
```

---

## Metrics to Track

| Metric | Target |
|--------|--------|
| Email 1 open rate | >50% |
| Email 2 open rate | >40% |
| Email 3 click rate | >15% |
| Waitlist → Customer | >8% |

---

## A/B Tests to Run

1. Subject line: "You're on the list" vs "Sampelit: You're in"
2. Email 3 timing: Day 7 vs Day 5
3. Case study inclusion vs no case study
4. Sender name: "Sampelit" vs "Name from Sampelit"
