import requests
import pandas as pd
import io

# Test parameters
YEAR = 2025
EVENT = "Abu Dhabi Grand Prix"
SESSION = "R" # Race
TYPE = "team_partners"

url = f"http://127.0.0.1:8000/export.csv"
params = {
    "year": YEAR,
    "event": EVENT,
    "session": SESSION,
    "type": TYPE
}

print(f"Testing {url} with params: {params}")

try:
    response = requests.get(url, params=params)
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if not content:
            print("Response is empty.")
        else:
            try:
                df = pd.read_csv(io.StringIO(content))
                print("Columns:", df.columns)
                print("Row Count:", len(df))
                print(df.head())
            except Exception as parse_err:
                print(f"Failed to parse CSV: {parse_err}")
                print("Content preview:", content[:500])
    else:
        print(f"Failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
