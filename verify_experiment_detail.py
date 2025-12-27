import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from public_api.routers.analytics import get_experiment_analytics
from orchestration.services.analytics_service import AnalyticsService
from data_access.database import DatabaseManager
from unittest.mock import MagicMock, AsyncMock

async def verify_experiment_detail():
    print("Verifying Experiment Detail V2 Endpoint...")
    
    # Needs DB dependency, but we can verify the Service logic directly
    # or try to integration test if we had a running DB.
    # Let's verify the SERVICE logic first as it's the core change.
    
    service = AnalyticsService()
    
    # Mock data structure
    elements_data = [{
        "id": "elem1",
        "name": "Hero CTA",
        "variants": [
            {'id': 'v1', 'name': 'A', 'total_allocations': 1000, 'total_conversions': 100},
            {'id': 'v2', 'name': 'B', 'total_allocations': 1000, 'total_conversions': 130} 
        ]
    }]
    
    try:
        print("Running analyze_hierarchical_experiment...")
        result = await service.analyze_hierarchical_experiment('exp1', elements_data)
        
        print("\n✅ Service Analysis Successful!")
        element = result['elements'][0]
        
        print(f"Element: {element['name']}")
        
        if 'bayesian_stats' in element:
            print("✅ 'bayesian_stats' found in element result.")
            winner = element['bayesian_stats']['winner']
            print(f"Winner: {winner['variant_name']}")
            print(f"Probability Best: {winner['probability_best']:.4f}")
        else:
            print("❌ 'bayesian_stats' MISSING in element result.")

        if 'daily_stats' in element and element['daily_stats']:
            print(f"✅ 'daily_stats' generated: {len(element['daily_stats'])} days found.")
            print(f"Sample Day 1 Stats: {element['daily_stats'][0]['variant_stats'][0]['conversion_rate']:.4f}")
        else:
            print("❌ 'daily_stats' MISSING or empty.")

        if 'traffic_breakdown' in element and element['traffic_breakdown']:
            print(f"✅ 'traffic_breakdown' generated: {len(element['traffic_breakdown'])} sources found.")
            print(f"Sample Source: {element['traffic_breakdown'][0]['source']} - {element['traffic_breakdown'][0]['visitors']} visitors")
        else:
            print("❌ 'traffic_breakdown' MISSING or empty.")
    
        print("\nVerification Complete.")
            
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_experiment_detail())
