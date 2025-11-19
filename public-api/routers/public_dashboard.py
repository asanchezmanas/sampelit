# public-api/routers/public_dashboard.py

@router.get("/public/dashboard/{experiment_id}")
async def public_dashboard(experiment_id: str):
    """
    Public dashboard (limited data)
    
    Shows:
    - ✅ Variant names
    - ✅ Allocation counts
    - ✅ Conversion rates
    - ✅ Winner (if detected)
    - ❌ Individual user data
    - ❌ Revenue numbers
    """
    
    # Get public data only
    data = await get_public_experiment_data(experiment_id)
    
    return templates.TemplateResponse(
        "public_dashboard.html",
        {"data": data}
    )
```

---

## 💡 Onboarding con Expectativas Claras
```
User signs up →
    Welcome email →
        "Before you start: What Samplit CAN and CAN'T do"
        
        ✅ CAN:
        - Find the best of your variants
        - Learn which messaging works
        - Optimize allocation automatically
        
        ❌ CAN'T:
        - Create good copy for you
        - Fix a bad product
        - Replace good marketing strategy
        
        Example: Our landing test
        → Control: 5%
        → Long: 7.8% ✅ Winner
        → Short: 4.9%
        
        Samplit found the winner and gave us +50% more conversions.
        But ALL three variants were well-designed.
        
        Your job: Create good variants
        Our job: Find the best one
