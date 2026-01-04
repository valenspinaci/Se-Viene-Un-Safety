import fastf1
import pandas as pd
import datetime

# Setup cache
fastf1.Cache.enable_cache('cache')

def debug_partners():
    year = 2023
    event = "Bahrain"
    session_type = "Q"
    
    print(f"Loading {year} {event} {session_type}...")
    try:
        session = fastf1.get_session(year, event, session_type)
        session.load()
    except Exception as e:
        print(f"Failed to load: {e}")
        return

    print("Session loaded.")
    
    # Check for Q split
    has_q_split = False
    if 'Q1' in session.results.columns:
        has_q_split = True
    print(f"Has Q split: {has_q_split}")
    
    team_drivers = {}
    for d in session.drivers:
        try:
            drv = session.get_driver(d)
            team = drv['TeamName']
            if not team: continue
            if team not in team_drivers:
                team_drivers[team] = []
            team_drivers[team].append(d)
        except Exception as e:
            print(f"Error getting driver {d}: {e}")
            
    print(f"Teams found: {list(team_drivers.keys())}")
    
    for team, drivers in team_drivers.items():
        if len(drivers) < 2:
            continue
            
        print(f"\nProcessing Team: {team} (Drivers: {drivers})")
        
        phases = ['Q1', 'Q2', 'Q3'] if has_q_split else ['ALL']
        
        for d_code in drivers:
            drv_info = session.get_driver(d_code)
            d_laps = session.laps.pick_driver(d_code)
            
            for phase in phases:
                if phase == 'ALL':
                    target_lap = d_laps.pick_fastest()
                    print(f"  {d_code} ALL: Fastest lap found? {target_lap is not None}")
                else:
                    q_time = drv_info.get(phase)
                    print(f"  {d_code} {phase} Time in Results: {q_time}")
                    
                    if pd.isna(q_time):
                        print(f"    Skipping {phase} (No time)")
                        continue
                        
                    # Exact match check
                    candidates = d_laps[d_laps['LapTime'] == q_time]
                    print(f"    Exact match candidates: {len(candidates)}")
                    
                    if candidates.empty:
                        # Try fuzzy
                        delta = pd.Timedelta(milliseconds=1)
                        fuzzy = d_laps[(d_laps['LapTime'] >= q_time - delta) & (d_laps['LapTime'] <= q_time + delta)]
                        print(f"    Fuzzy match candidates: {len(fuzzy)}")


if __name__ == "__main__":
    debug_partners()
