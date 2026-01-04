import fastf1
import pandas as pd

YEAR = 2025
EVENT = "Abu Dhabi Grand Prix"
SESSION = "R"

print(f"Loading session {YEAR} {EVENT} {SESSION}")
session = fastf1.get_session(YEAR, EVENT, SESSION)
session.load()

print(f"Drivers: {len(session.drivers)}")

# Check first driver
d1 = session.drivers[0]
print(f"Checking Driver ID: {d1}")
d_laps = session.laps.pick_driver(d1)
print(f"Laps for {d1}: {len(d_laps)}")

fastest = d_laps.pick_fastest()
if fastest is not None:
    print(f"Fastest Lap Time: {fastest['LapTime']}")
    print(f"Is NaT? {pd.isna(fastest['LapTime'])}")
else:
    print("No fastest lap found.")

# Check how many drivers have valid fastest laps
valid_count = 0
for d in session.drivers:
    laps = session.laps.pick_driver(d)
    try:
        f = laps.pick_fastest()
        if f is not None and not pd.isna(f['LapTime']):
            valid_count += 1
    except:
        pass

print(f"Drivers with valid fastest laps: {valid_count}/{len(session.drivers)}")
