import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from public_api.routers.simulator import forecast_convergence, ForecastRequest

async def verify_simulator():
    print("Verifying Simulator Forecast Endpoint...")
    
    req = ForecastRequest(
        traffic_daily=5000,
        baseline_cr=0.05,
        uplift=0.15,
        confidence_target=0.95
    )
    
    try:
        response = await forecast_convergence(req)
        
        print("\n✅ Simulator Verification Successful!")
        print(f"Days simulated: {response['days']}")
        print(f"Forecast points: {len(response['forecast'])}")
        print(f"First 5 projected p-values: {response['forecast'][:5]}")
        
        if len(response['forecast']) == response['days']:
            print("Output length matches simulation days.")
        else:
            print("❌ Mismatch in output length.")
            
    except Exception as e:
        print(f"\n❌ Simulator Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_simulator())
