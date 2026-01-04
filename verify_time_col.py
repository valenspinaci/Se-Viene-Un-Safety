
import requests
import pandas as pd
import io

BASE_URL = "http://127.0.0.1:8000"

def test_pole_microsectors_time():
    print("\n[TEST] Task: Pole Microsectors Time Column Check")
    params = {
        "year": 2024,
        "event": "Bahrain",
        "session": "Q",
        "type": "pole_microsectors"
    }
    try:
        r = requests.get(f"{BASE_URL}/export.csv", params=params)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            print("Status: SUCCESS")
            print("Columns:", df.columns.tolist())
            if 'time_elapsed_seconds' in df.columns:
                print("Validation: PASSED (Column found)")
                print("First row time:", df.iloc[0]['time_elapsed_seconds'])
            else:
                print("Validation: FAILED (Column missing)")
        else:
            print(f"Status: FAILED ({r.status_code})")
            print(r.text)
    except Exception as e:
        print(f"Exception: {e}")
if __name__ == "__main__":
    test_pole_microsectors_time()
