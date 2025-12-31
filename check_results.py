import fastf1
import pandas as pd

try:
    session = fastf1.get_session(2023, 'Bahrain Grand Prix', 'Q')
    session.load(laps=False, telemetry=False) # Load results only
    print("Results columns:", session.results.columns)
    
    if 'Q1' in session.results.columns:
        print("Q1 column found.")
        print(session.results[['Abbreviation', 'Q1', 'Q2', 'Q3']].head())
    else:
        print("Q1 column NOT found.")

except Exception as e:
    print(f"Error: {e}")
