# Pricing Page Copy

**URL:** `/pricing`

---

## Hero Section

### Headline

Simple pricing. No surprises.

### Subheadline

Start testing in minutes. Scale when you're ready.
No sales calls. No enterprise negotiations.

---

## Pricing Toggle

[Monthly] / [Annual — Save 20%]

---

## Tiers

### Starter — €149/month (Annual: €119/month)

**For:** Solo founders and small teams getting started with testing.

**Includes:**
- 5 active experiments
- 25,000 monthly visitors
- 1 website
- Visual Editor
- Bayesian analytics
- Email support (48h response)

**CTA:** Start testing →

---

### Professional — €399/month (Annual: €319/month)

**Badge:** Most Popular

**For:** Growing teams running continuous optimization programs.

**Includes:**
- 25 active experiments
- 100,000 monthly visitors
- 3 websites
- Visual Editor
- Bayesian analytics
- Priority support (24h response)
- API access
- Export data (CSV/JSON)
- Custom conversion goals

**CTA:** Start testing →

---

### Scale — €999/month (Annual: €799/month)

**For:** Teams with high traffic and advanced requirements.

**Includes:**
- Unlimited experiments
- 500,000 monthly visitors
- 10 websites
- Everything in Professional
- Dedicated account manager
- White-label reports
- Advanced segmentation
- Webhooks & integrations
- 99.9% uptime SLA

**CTA:** Start testing →

---

### Enterprise — €2,499/month

**For:** Organizations requiring custom solutions and compliance.

**Includes:**
- Unlimited everything
- Unlimited visitors
- Unlimited websites
- Everything in Scale
- Custom integrations
- On-premise option
- SSO / SAML
- Custom contracts
- Phone support
- Dedicated infrastructure

**CTA:** Contact us →

---

## Early Adopter Notice (Temporary)

**Banner above pricing:**

```
Early adopter pricing: 50% off your first year.
Limited to the first 100 customers.
```

**With discount:**
- Starter: €74.50/month (first year)
- Professional: €199.50/month (first year)
- Scale: €499.50/month (first year)

---

## Feature Comparison Table

| Feature | Starter | Professional | Scale | Enterprise |
|---------|---------|--------------|-------|------------|
| Active experiments | 5 | 25 | Unlimited | Unlimited |
| Monthly visitors | 25k | 100k | 500k | Unlimited |
| Websites | 1 | 3 | 10 | Unlimited |
| Visual Editor | ✓ | ✓ | ✓ | ✓ |
| Bayesian analytics | ✓ | ✓ | ✓ | ✓ |
| API access | — | ✓ | ✓ | ✓ |
| Data export | — | ✓ | ✓ | ✓ |
| Custom goals | — | ✓ | ✓ | ✓ |
| White-label | — | — | ✓ | ✓ |
| Webhooks | — | — | ✓ | ✓ |
| SSO / SAML | — | — | — | ✓ |
| On-premise | — | — | — | ✓ |
| SLA | — | — | 99.9% | Custom |
| Support | Email (48h) | Priority (24h) | Dedicated | Phone |

---

## FAQ Section

### General

**Q: Can I change plans later?**

Yes. Upgrade or downgrade anytime from your dashboard. Changes take effect on your next billing cycle. No penalties.

---

**Q: What counts as a "monthly visitor"?**

A unique visitor who sees at least one experiment. Visitors who don't participate in experiments don't count against your limit. Repeat visits from the same visitor in a month count as one.

---

**Q: What happens if I exceed my visitor limit?**

We don't cut off your experiments mid-month. You'll receive a notification when you reach 80% and 100% of your limit. If you consistently exceed, we'll recommend upgrading.

---

**Q: Do you offer refunds?**

No refunds for partial months. You can cancel anytime and your access continues until the end of your billing period.

---

### Testing & Features

**Q: How many variants can I test per experiment?**

Up to 10 variants per experiment on all plans. We recommend 2-4 for faster, cleaner results.

---

**Q: Does Sampelit slow down my website?**

No. The tracker script is <15KB, loads asynchronously, and is served from a global CDN. Typical load time: <50ms.

---

**Q: What platforms does Sampelit work with?**

Any website. WordPress, Shopify, Webflow, custom code, React, Vue—if it runs in a browser, Sampelit works.

---

**Q: How long until I see results?**

Depends on your traffic and the size of the difference between variants. Typically 1-4 weeks. The dashboard shows estimated time to significance.

---

### Billing & Security

**Q: How does billing work?**

Monthly plans are billed on the same date each month. Annual plans are billed upfront for the full year (with 20% discount).

---

**Q: Is my data secure?**

Yes. All data is encrypted in transit (TLS 1.3) and at rest. We're GDPR compliant. We don't sell your data. See our [Privacy Policy](/privacy).

---

**Q: Can I pay annually?**

Yes. Annual billing saves 20%—equivalent to 2+ months free.

---

**Q: Do you offer discounts for startups?**

Our early adopter pricing (50% off first year) is the best deal available. We don't offer additional discounts.

---

## Bottom CTA

### Headline

Not sure which plan fits?

### Body

Start with Starter. Upgrade when you need to.
No commitment, cancel anytime.

### CTA

Start your first experiment →

---

## Social Proof (Optional)

**Below pricing, above FAQ:**

> "Setup took 10 minutes. First meaningful results in 12 days."
> — Alex P., SaaS Founder

> "Finally, testing without the enterprise sales process."
> — Jordan K., Growth Lead

---

## Trust Badges

- 🔒 SSL Encrypted
- 🇪🇺 GDPR Compliant
- 💳 Powered by Stripe
- 🌍 Built in Barcelona

---

## Microcopy

**Under monthly/annual toggle:**
```
Annual billing saves 20% (2+ months free)
```

**Under each CTA:**
```
No credit card required for 14-day trial
```

**Under Enterprise "Contact us":**
```
Typical response time: 24 hours
```

---

## Technical Notes

### Stripe Product IDs (to create)

| Plan | Monthly ID | Annual ID |
|------|------------|-----------|
| Starter | `price_starter_monthly` | `price_starter_annual` |
| Professional | `price_pro_monthly` | `price_pro_annual` |
| Scale | `price_scale_monthly` | `price_scale_annual` |
| Enterprise | Custom invoicing | Custom invoicing |

### URL Structure

```
/pricing                    — Main pricing page
/pricing?plan=starter       — Pre-select Starter
/pricing?plan=professional  — Pre-select Professional
/pricing?annual=true        — Pre-select annual toggle
```

---

## Checklist Before Publishing

- [ ] All prices correct (€149/€399/€999/€2,499)
- [ ] Annual prices calculated (20% off)
- [ ] Early adopter banner active (50% off first year)
- [ ] All CTAs link to signup flow
- [ ] FAQ answers complete
- [ ] Mobile responsive
- [ ] Stripe products created
- [ ] Analytics tracking on CTA clicks
