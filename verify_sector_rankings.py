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
            expected_cols = ['driver_code', 'best_s1', 'rank_best_s1', 'lap_time']
            missing = [c for c in expected_cols if c not in df.columns]
            if missing:
                print(f"FAILED: Missing columns: {missing}")
            else:
                print("PASSED: Expected columns present.")
                
            # strict validation: check if sum of sectors approx equals lap time
            # helper to parse "0 days 00:01:30.123"
            def parse_time(t_str):
                if pd.isna(t_str) or t_str == "": return None
                # t_str example: "00:01:30.123" (since we strip 'days')
                # Actually main.py does: str(x).split('days')[-1].strip()
                # fastf1 output usually: "0 days 00:01:30.123000" -> "00:01:30.123000"
                try:
                    parts = t_str.split(':')
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = float(parts[2])
                    return hours*3600 + minutes*60 + seconds
                except:
                    return None

            print("Verifying Sector Sums...")
            for idx, row in df.head().iterrows():
                s1 = parse_time(row['best_s1'])
                s2 = parse_time(row['best_s2'])
                s3 = parse_time(row['best_s3'])
                total = parse_time(row['lap_time'])
                
                if s1 and s2 and s3 and total:
                    # Tolerance: 0.001s
                    diff = abs((s1 + s2 + s3) - total)
                    if diff < 0.002:
                        print(f"Row {idx} OK: {s1}+{s2}+{s3} = {s1+s2+s3:.3f} ~= {total}")
                    else:
                        print(f"Row {idx} MISMATCH: {s1}+{s2}+{s3} = {s1+s2+s3:.3f} != {total} (diff {diff:.4f})")
                else:
                    print(f"Row {idx} SKIPPED (missing data)")
                
        else:
            print(f"FAILED: Status Code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sector_rankings()
