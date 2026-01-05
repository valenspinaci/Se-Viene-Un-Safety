import requests
import pandas as pd
import io

BASE_URL = "http://localhost:8000"

def test_sector_rankings():
    # Use a knwon event: 2023 Bahrain Grand Prix Qualifying
    params = {
        "year": 2023,
        "event": "Bahrain Grand Prix",
        "session": "Q",
        "type": "sector_rankings"
    }
    
    print(f"Requesting {params}...")
    try:
        response = requests.get(f"{BASE_URL}/export.csv", params=params)
        
        if response.status_code == 200:
            print("Success! Response 200 OK.")
            content = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(content))
            print("Columns:", df.columns.tolist())
            print("First 5 rows:")
            print(df.head())
            
            # Basic validation
            expected_cols = ['driver_code', 'best_s1', 'rank_best_s1', 'theoretical_best_lap']
            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                print(f"FAILED: Missing columns: {missing}")
            else:
                print("PASSED: Expected columns present.")
                
        else:
            print(f"FAILED: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sector_rankings()
