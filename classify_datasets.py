
import requests
import pandas as pd
import json
import os
from pprint import pprint

BASE_URL = "http://localhost:8005"
DATA_DIR = r"c:\Users\ibnou\Desktop\DataGovProjetFederateur\datasets\test_data"

DATASETS = [
    "DATAGOV_INTERNATIONAL.csv",
    "DATAGOV_MOROCCO_FULL.csv"
]

def classify_file(filename):
    file_path = os.path.join(DATA_DIR, filename)
    print(f"\n{'='*50}")
    print(f"📂 Processing: {filename}")
    print(f"{'='*50}")
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        print(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns.")
        
        # Prepare Payload
        # robustly replace NaNs
        df_clean = df.astype(object).where(pd.notnull(df), None)
        data_sample = df_clean.to_dict(orient='list')
        
        # Limit sample size if needed (Service usually takes full columns but for speed we can limit if huge)
        # But per requirements we expect full column classification.
        # Ensure we send serializable data
        
        payload = {
            "dataset_id": filename,
            "data_sample": data_sample
        }
        
        print("🚀 Sending request to Classification Service...")
        response = requests.post(f"{BASE_URL}/api/v1/classification/classify", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            classifications = result.get("classifications", {})
            
            print(f"\n📊 Classification Results for {filename}:")
            print(f"{'-'*60}")
            print(f"{'Column Name':<30} | {'Level':<10} | {'Code':<15} | {'Conf':<6}")
            print(f"{'-'*60}")
            
            for col, info in classifications.items():
                print(f"{col:<30} | {info['level']:<10} | {info['code']:<15} | {info['confidence']:<6}")
                
            # Optional: Save results to file
            output_file = f"classification_result_{filename}.json"
            with open(output_file, "w") as f:
                json.dump(result, f, indent=4)
            print(f"\n💾 Results saved to {output_file}")
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    for ds in DATASETS:
        classify_file(ds)
