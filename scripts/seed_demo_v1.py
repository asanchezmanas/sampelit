
import json
import random
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Force Development mode to see errors in response
os.environ['IS_DEVELOPMENT'] = 'True'

try:
    from fastapi.testclient import TestClient
    from main import app
    from config.settings import get_settings
    from data_access.database import DatabaseManager
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

# Initialize Client
client = TestClient(app)
settings = get_settings()
API_PREFIX = settings.API_V1_PREFIX # e.g. /api/v1

# Configuration
USER_EMAIL = "demo@sampelit.com"
USER_PASS = "demo12345"
ORG_NAME = "Sampelit Demo Org"
EXPERIMENT_NAME = "Landing Page Optimization (3x3)"
VISITORS = 10000
TARGET_UPLIFT = 0.25

class DemoSeeder:
    def __init__(self):
        self.user_token = None
        self.installation_token = None
        self.experiment_id = None
        self.combinations = []
        
        # 3x3 Elements (2 elements with 3 variants each = 9 combos)
        # Matches Simulator Logic
        self.elements = [
            {
                "name": "CTA Button",
                "category": "visual",
                "selector": {"type": "css", "query": ".cta-primary"},
                "variations": [
                    {"name": "A", "content": "Unlock Growth", "description": "Status Quo"},
                    {"name": "B", "content": "Scale Now", "description": "Action Oriented"},
                    {"name": "C", "content": "Try Samplit", "description": "Brand Focused"}
                ]
            },
            {
                "name": "Hero Copy",
                "category": "content",
                "selector": {"type": "css", "query": ".hero-text"},
                "variations": [
                    {"name": "X", "content": "Scientific Conversion Optimization", "description": "Technical"},
                    {"name": "Y", "content": "Data-Driven Growth", "description": "Benefit Driven"},
                    {"name": "Z", "content": "Maximize Revenue", "description": "Outcome Focused"}
                ]
            }
        ]
        
        # Latent Probabilities (Truth Matrix)
        # B+Y is winner
        self.probs = {
            'A-X': 0.025, 'A-Y': 0.038, 'A-Z': 0.028,
            'B-X': 0.042, 'B-Y': 0.055, 'B-Z': 0.045, # B-Y is clear winner (5.5%)
            'C-X': 0.021, 'C-Y': 0.031, 'C-Z': 0.036,
        }
        self.stats = {k: {'visions': 0, 'conversions': 0} for k in self.probs}
        self.session_logs = {"samplit": {"total_conversions": 0, "combination_stats": []}, "comparison": 0, "traditional": {"total_conversions": 0}}

    def login_or_create_user(self):
        print("Authenticating...")
        # 1. Login
        resp = client.post(f"{API_PREFIX}/auth/token", data={"username": USER_EMAIL, "password": USER_PASS})
        if resp.status_code == 200:
            self.user_token = resp.json()["access_token"]
            print("   Logged in successfully.")
        else:
            print("   User not found, creating...")
            # 2. Register
            reg = client.post(f"{API_PREFIX}/auth/register", json={
                "email": USER_EMAIL, "password": USER_PASS, "name": "Demo User", "organization_name": ORG_NAME
            })
            if reg.status_code != 201:
                print(f"   Registration failed: {reg.text}")
                sys.exit(1)
            # Login again
            resp = client.post(f"{API_PREFIX}/auth/token", data={"username": USER_EMAIL, "password": USER_PASS})
            if resp.status_code != 200:
                print(f"   Login after registration failed: {resp.text}")
                sys.exit(1)
            self.user_token = resp.json()["access_token"]
            print("   Registered and logged in.")
            
        # Get Installation Token via Integrations or Installations endpoint
        headers = {"Authorization": f"Bearer {self.user_token}"}
        inst_resp = client.get(f"{API_PREFIX}/installations", headers=headers)
        if inst_resp.status_code == 200:
            insts = inst_resp.json()
            # The list might be inside a key or direct list. Assuming list based on typical API.
            if isinstance(insts, dict) and 'items' in insts:
                insts = insts['items']
            
            if insts:
                self.installation_token = insts[0]['installation_token']
                # Ensure active (patch if needed)
                if insts[0]['status'] != 'active':
                     client.patch(f"{API_PREFIX}/installations/{insts[0]['id']}", headers=headers, json={"status": "active"})
                print(f"   Installation Token: {self.installation_token}")
            else:
                print("   No installation found! Creating one...")
                new_inst = client.post(f"{API_PREFIX}/installations", headers=headers, json={"site_url": "https://sampelit.demo", "platform": "custom"})
                if new_inst.status_code in [200, 201]:
                    self.installation_token = new_inst.json()['installation_token']
                    print(f"   Created Installation: {self.installation_token}")
                else:
                    print(f"   Failed to create installation: {new_inst.text}")
                    sys.exit(1)

    def create_experiment(self):
        print("Creating Factorial Experiment...")
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Check existing logic... requires list endpoint.
        # Check existing experiments to avoid duplicates
        existing = client.get(f"{API_PREFIX}/experiments", headers=headers)
        if existing.status_code == 200:
            exps = existing.json()
            if isinstance(exps, dict) and 'items' in exps: exps = exps['items']
                
            for exp in exps:
                if exp['name'] == EXPERIMENT_NAME:
                    print("   Experiment already exists. Using it.")
                    self.experiment_id = exp['id']
                    # Ensure active
                    client.patch(f"{API_PREFIX}/experiments/{self.experiment_id}", headers=headers, json={"status": "active"})
                    return

        payload = {
            "name": EXPERIMENT_NAME,
            "description": "Orchestrated via Seed Script",
            "target_url": "https://sampelit.demo/landing",
            "protocol": "factorial",
            "allocation": 1.0,
            "elements": self.elements
        }
        
        # Use CORRECT endpoint for Multi-Element: /orchestration/orchestrate
        resp = client.post(f"{API_PREFIX}/orchestration/orchestrate", headers=headers, json=payload)
        if resp.status_code not in [200, 201]:
            print(f"   Creation failed: {resp.text}")
            sys.exit(1)
            
        data = resp.json()
        self.experiment_id = data['experiment_id']
        print(f"   Created Experiment ID: {self.experiment_id}")
        
        # Activate via standard experiment endpoint
        client.patch(f"{API_PREFIX}/experiments/{self.experiment_id}", headers=headers, json={"status": "active"})
        print("   Experiment Activated.")

    def run_simulation(self):
        print(f"Simulating {VISITORS} visitors...")
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Pre-calculate variants mapping if possible
        # We need to know what ID corresponds to what combination
        # But we'll just parse the assignment response
        
        for i in range(VISITORS):
            uid = f"sim_user_{i}"
            sid = f"sess_{i}_{random.randint(1000,9999)}"
            
            # 1. Assign
            # Use CORRECT endpoint: /orchestration/assign/{experiment_id}
            assign_resp = client.post(
                f"{API_PREFIX}/orchestration/assign/{self.experiment_id}?uid={uid}&sid={sid}",
                headers=headers
            )
            
            if assign_resp.status_code != 200:
                # print(f"Assignment error: {assign_resp.text}")
                continue
                
            allocation = assign_resp.json()
            # allocation contains 'combination_id' and 'variants' (list of dicts)
            
            # Identify the combination key (A-X, B-Y, etc.) from the response
            # Response: { "combination_id": "...", "variants": [ {"element": "CTA Button", "variant_name": "B", ...}, ... ] }
            
            variants_assigned = allocation.get('variants', [])
            # Map element name to variant name
            var_map = {v['element_name']: v['variant_name'] for v in variants_assigned}
            
            cta_var = var_map.get("CTA Button", "A")
            hero_var = var_map.get("Hero Copy", "X")
            
            combo_key = f"{cta_var}-{hero_var}"
            
            # 2. Determine Outcome
            prob = self.probs.get(combo_key, 0.03) # Default 3%
            converted = random.random() < prob
            
            self.stats[combo_key]['visions'] += 1
            if converted:
                self.stats[combo_key]['conversions'] += 1
                self.session_logs['samplit']['total_conversions'] += 1
                
                # 3. Convert
                # Use CORRECT endpoint: /orchestration/conversion
                conv_resp = client.post(
                    f"{API_PREFIX}/orchestration/conversion",
                    headers=headers,
                    json={
                        "experiment_id": self.experiment_id,
                        "user_identifier": uid,
                        "combination_id": allocation['combination_id'],
                        "value": max(10.0, float(random.gauss(50.0, 15.0))) # 50 EUR +/-
                    }
                )
            
            # Console progress
            if (i+1) % 1000 == 0:
                print(f"   Processed {i+1} visitors...")

    def export_artifacts(self):
        print("\nExporting Artifacts...")
        
        # 1. Truth Matrix CSV
        print("   Generating Truth Matrix (10k simulated rows)...")
        cols = sorted(self.probs.keys())
        matrix_rows = []
        # We generate a representative matrix based on probabilities
        for _ in range(VISITORS):
            row = {}
            for k in cols:
                # Each cell in truth matrix represents "Would this user have converted on this variant?"
                # Independent probability per variant
                row[k] = 1 if random.random() < self.probs[k] else 0
            matrix_rows.append(row)
        
        df = pd.DataFrame(matrix_rows)
        # Rename columns to match what audit expects? usually just headers
        csv_path = Path("scripts/data/truth_matrix.csv")
        csv_path.parent.mkdir(exist_ok=True, parents=True)
        df.to_csv(csv_path, index=False)
        print(f"   Saved {csv_path}")

        # 2. Session Logs JSON
        # Update logs structure
        self.session_logs['samplit']['combination_stats'] = [
            {"combination": k, "allocated": v['visions'], "conversions": v['conversions']}
            for k, v in self.stats.items()
        ]
        
        baseline_conv = sum(int((VISITORS/9) * p) for p in self.probs.values())
        self.session_logs['traditional']['total_conversions'] = baseline_conv
        self.session_logs['comparison'] = self.session_logs['samplit']['total_conversions'] - baseline_conv
        
        json_path = Path("scripts/data/session_logs.json")
        with open(json_path, 'w') as f:
            json.dump(self.session_logs, f, indent=2)
        print(f"   Saved {json_path}")

    def verify(self):
        print("\nVerifying Integrity API...")
        # Use CORRECT endpoint: /verify/verify-integrity
        files = {
            'matrix': ('truth_matrix.csv', open('scripts/data/truth_matrix.csv', 'rb'), 'text/csv'),
            'session_logs': ('session_logs.json', open('scripts/data/session_logs.json', 'rb'), 'application/json')
        }
        headers = {"Authorization": f"Bearer {self.user_token}"}
        resp = client.post(f"{API_PREFIX}/verify/verify-integrity", headers=headers, files=files)
        
        if resp.status_code == 200:
            cert = resp.json()
            uplift = cert.get('performance_benchmark', {}).get('uplift', 'N/A')
            print(f"   Integrity Verified! Uplift: +{uplift} conversions detected.")
            print(f"   Certificate ID: {cert.get('certificate_id')}")
        else:
            print(f"   Verification Failed ({resp.status_code}): {resp.text}")

def main():
    print(f"Starting Seeding Demo v1 | API Prefix: {API_PREFIX}")
    try:
        seeder = DemoSeeder()
        seeder.login_or_create_user()
        seeder.create_experiment()
        seeder.run_simulation()
        seeder.export_artifacts()
        seeder.verify()
        print("\nDATA GENERATION COMPLETE. Dashboard is ready.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
