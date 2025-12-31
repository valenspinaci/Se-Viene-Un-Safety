import fastf1

try:
    # Try to access a session with 'Q1'
    # Use a known event, e.g., Bahrain 2023
    session = fastf1.get_session(2023, 'Bahrain Grand Prix', 'Q1')
    print("SUCCESS: 'Q1' is a valid session identifier.")
    print(f"Session name: {session.name}")
except Exception as e:
    print(f"FAILED: 'Q1' not supported directly. Error: {e}")

try:
    session = fastf1.get_session(2023, 'Bahrain Grand Prix', 'Q')
    print("Loading 'Q' session to check splits...")
    session.load(laps=True, telemetry=False)
    # Check if we can identify Q1 laps
    # Usually 'Split' column or similar? Or just by time?
    print(f"Laps columns: {session.laps.columns}")
except Exception as e:
    print(f"Error loading Q: {e}")
