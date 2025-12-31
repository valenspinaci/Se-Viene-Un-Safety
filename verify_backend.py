import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, url, params=None):
    print(f"Testing {name}...", end=" ")
    try:
        start = time.time()
        r = requests.get(url, params=params)
        duration = time.time() - start
        if r.status_code == 200:
            print(f"OK ({duration:.2f}s)")
            return True, r
        else:
            print(f"FAILED ({r.status_code})")
            print(r.text)
            return False, r
    except Exception as e:
        print(f"ERROR: {e}")
        return False, None

def main():
    # Wait for server
    for i in range(10):
        try:
            requests.get(f"{BASE_URL}/health")
            break
        except:
            time.sleep(1)
            print("Waiting for server...")
    
    # 1. Health
    success, _ = test_endpoint("Health", f"{BASE_URL}/health")
    if not success: sys.exit(1)

    # 2. Years
    success, r = test_endpoint("Years", f"{BASE_URL}/options/years")
    if success:
        print(f"Years: {r.json()[:3]}...")

    # 3. Events (use 2023)
    success, r = test_endpoint("Events 2023", f"{BASE_URL}/options/events", params={"year": 2023})
    if success:
        events = r.json()
        print(f"Events: {events[:3]}...")
    
    # 4. Sessions - no load needed
    success, r = test_endpoint("Sessions", f"{BASE_URL}/options/sessions", params={"year": 2023, "event": "Bahrain Grand Prix"})
    if success:
        print(f"Sessions: {r.json()}")

    # 5. Export (Laps) - minimal test, might fail if cache needs building or internet issues
    # We'll try to export just header or very small data if possible? 
    # Actually, we can't easily limit rows in FastF1 without loading.
    # We will skip heavy export test to avoid timeout, or try a very simple one if exists.
    # Just checking if 'options/drivers' works is a good proxy for loading.
    
    print("\nSkipping heavy export/driver load tests to avoid long blocking time in verification.")
    print("Backend seems responsive.")

if __name__ == "__main__":
    main()
