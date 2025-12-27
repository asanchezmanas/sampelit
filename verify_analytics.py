import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from data_access.database import DatabaseManager
from config.settings import get_settings
from public_api.routers.analytics import get_global_analytics

async def verify_global_analytics():
    print("Verifying Global Analytics Endpoint...")
    
    # Mock dependencies
    class MockDB:
        def __init__(self):
            self.pool = self
            
        def acquire(self):
            return self
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
            
        async def fetch(self, query, *args):
            print(f"Executing fetch: {query[:50]}...")
            # Return fake experiment IDs
            return [{'id': 'exp-123'}, {'id': 'exp-456'}]
            
        async def fetchrow(self, query, *args):
            print(f"Executing fetchrow: {query[:50]}...")
            if "experiments" in query:
                 return {'id': 'exp-123'}
            # Return fake metrics
            return {
                'visitors': 5000,
                'conversions': 250
            }

    mock_db = MockDB()
    user_id = "user-123"
    
    try:
        response = await get_global_analytics(
            user_id=user_id,
            db=mock_db,
            period="30d"
        )
        
        print("\n✅ Verification Successful!")
        print(f"Data received: {response.data}")
        
        if response.data['total_visitors'] == 5000 and response.data['total_conversions'] == 250:
            print("Values match expected mock data.")
        else:
            print(f"❌ Value mismatch. Expected 5000/250, got {response.data['total_visitors']}/{response.data['total_conversions']}")
            
    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_global_analytics())
