import os
import io
import datetime
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
import fastf1
import pandas as pd

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to enable cache
@app.on_event("startup")
def startup_event():
    cache_dir = os.path.join(os.getcwd(), 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    fastf1.Cache.enable_cache(cache_dir)

@app.get("/")
def read_root():
    return {
        "message": "FastF1 CSV Exporter API is running.",
        "docs_url": "http://127.0.0.1:8000/docs"
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/options/years")
def get_years():
    # Return 2018 to current year - 1
    current_year = datetime.datetime.now().year
    # If it's early in the year, maybe we want previous full season?
    # Prompt says 2018..current-1.
    # Logic: range(2018, current_year)
    # User requested 2025 support.
    return list(range(2018, current_year + 1))

@app.get("/options/events")
def get_events(year: int):
    try:
        schedule = fastf1.get_event_schedule(year)
        # Filter for official events if needed, but schedule usually contains them.
        # Returning list of event names.
        return schedule['EventName'].tolist()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/options/sessions")
def get_sessions(year: int, event: str):
    # Returning common set as requested for simplicity, 
    # but strictly speaking validation by loading would be ideal.
    # To keep it fast/simple:
    return ["FP1", "FP2", "FP3", "Q", "S", "R"]

@app.get("/options/drivers")
def get_drivers(year: int, event: str, session: str):
    try:
        f1_session = fastf1.get_session(year, event, session)
        f1_session.load(laps=False, telemetry=False, weather=False, messages=False) 
        # minimal load to get drivers? 
        # fastf1 3.0+ loading might require at least something. 
        # 'drivers' property is populated after basic load.
        # Actually session.drivers is available after load().
        # We need to load drivers.
        
        # Mapping driver numbers/codes to names might require accessing session.results if available
        # or session.drivers which is a list of numbers.
        # session.get_driver(number) returns info.
        
        drivers_info = []
        for driver_id in f1_session.drivers:
            # get_driver returns dictionary-like object
            d = f1_session.get_driver(driver_id)
            drivers_info.append({
                "id": driver_id,
                "code": d['Abbreviation'],
                "name": d['BroadcastName'] or d['FullName'] or str(driver_id)
            })
            
        return drivers_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export.csv")
def export_csv(
    year: int,
    event: str,
    session: str,
    drivers: Optional[str] = Query(None), # comma separated
    type: str = Query(..., regex="^(laps|telemetry|compare|team_partners|final_speed|race_pace|pole_microsectors)$"),
    lap: Optional[str] = Query('fastest', regex="^(fastest|lap_number)$"),
    lap_number: Optional[int] = None
):
    try:
        f1_session = fastf1.get_session(year, event, session)
        # Load necessary data based on type
        # For 'laps', we need laps.
        # For 'telemetry', we need laps and telemetry.
        
        f1_session.load()
        
        selected_drivers = []
        if drivers:
            # Clean up comma separated list
            selected_drivers = [d.strip() for d in drivers.split(',') if d.strip()]
        
        output_df = pd.DataFrame()
        filename = f"export_{year}_{event.replace(' ', '_')}_{session}_{type}.csv"

        if type == 'laps':
            if selected_drivers:
                laps = f1_session.laps.pick_drivers(selected_drivers)
            else:
                laps = f1_session.laps
            
            output_df = laps
            
        elif type == 'telemetry':
            # drivers param is effectively required here or we default to all? 
            # Prompt says "filtered by drivers if provided". 
            # Telemetry for ALL drivers might be huge. Let's assume if not provided, take all? 
            # Or maybe restrict. Let's try to handle all if not too heavy, but safer to stick to selected if present.
            
            driver_list = selected_drivers if selected_drivers else f1_session.drivers
            
            telemetry_data = []
            
            for driver in driver_list:
                d_laps = f1_session.laps.pick_driver(driver)
                
                # Pick lap
                if lap == 'fastest':
                    target_lap = d_laps.pick_fastest()
                elif lap == 'lap_number':
                    if lap_number is None:
                        # Fallback
                        target_lap = d_laps.pick_fastest()
                    else:
                        target_lap_df = d_laps[d_laps['LapNumber'] == lap_number]
                        if not target_lap_df.empty:
                            target_lap = target_lap_df.iloc[0]
                        else:
                            continue 
                            
                if target_lap is None:
                    continue
                    
                try:
                    tel = target_lap.get_telemetry()
                    cols = ['Time', 'Distance', 'Speed', 'Throttle', 'Brake', 'Gear', 'DRS', 'X', 'Y']
                    existing_cols = [c for c in cols if c in tel.columns]
                    subset = tel[existing_cols].copy()
                    
                    subset['driver'] = driver
                    telemetry_data.append(subset)
                    
                except Exception as ex:
                    print(f"Error getting telemetry for {driver}: {ex}")
                    continue

            if telemetry_data:
                output_df = pd.concat(telemetry_data)
        
        elif type == 'compare':
            # Strict Compare Logic (Telemetry Alignment)
            if len(selected_drivers) != 2:
                raise HTTPException(status_code=400, detail="Compare mode requires exactly 2 drivers.")
            
            driver_a = selected_drivers[0]
            driver_b = selected_drivers[1]
            
            # Helper to get lap
            def get_target_lap(d_code):
                d_laps = f1_session.laps.pick_driver(d_code)
                if lap == 'fastest':
                    return d_laps.pick_fastest()
                elif lap == 'lap_number':
                     res = d_laps[d_laps['LapNumber'] == lap_number]
                     return res.iloc[0] if not res.empty else None
                return None

            lap_a = get_target_lap(driver_a)
            lap_b = get_target_lap(driver_b)
            
            if lap_a is None or lap_b is None:
                 raise HTTPException(status_code=404, detail="Could not find specified laps for one or both drivers.")

            tel_a = lap_a.get_telemetry()
            tel_b = lap_b.get_telemetry()
            
            base_cols = ['Distance', 'Speed', 'Throttle', 'Brake']
            def prep_tel(t, suffix):
                t = t.drop_duplicates(subset=['Distance'])
                t = t[base_cols].set_index('Distance')
                t.columns = [f"{c}_{suffix}" for c in t.columns]
                return t
                
            df_a = prep_tel(tel_a, "A")
            df_b = prep_tel(tel_b, "B")
            
            merged = pd.concat([df_a, df_b], axis=1).sort_index()
            merged = merged.interpolate(method='slinear').fillna(method='bfill').fillna(method='ffill')
            
            output_df = merged.reset_index()

            # Add Driver Metadata
            try:
                info_a = f1_session.get_driver(driver_a)
                info_b = f1_session.get_driver(driver_b)
                
                output_df['Driver_A_Name'] = info_a['BroadcastName'] or info_a['FullName'] or driver_a
                output_df['Driver_A_Team'] = info_a['TeamName'] or "Unknown"
                output_df['Driver_B_Name'] = info_b['BroadcastName'] or info_b['FullName'] or driver_b
                output_df['Driver_B_Team'] = info_b['TeamName'] or "Unknown"
                
                meta_cols = ['Driver_A_Name', 'Driver_A_Team', 'Driver_B_Name', 'Driver_B_Team']
                cols = meta_cols + [c for c in output_df.columns if c not in meta_cols]
                output_df = output_df[cols]
                
            except Exception as e:
                print(f"Warning: Could not fetch driver details: {e}")
                pass
        
        elif type == 'team_partners':
            # SUMMARY-LEVEL CSV logic with Q1/Q2/Q3 reconstruction
            
            summary_data = []

            # Check if this is a Qualifying session with Q-split
            has_q_split = False
            try:
                if 'Q1' in f1_session.results.columns:
                    has_q_split = True
            except:
                pass
            
            # Group drivers by team to ensure we process teammates (though user asks for one row per driver, iterating by team is still cleaner to group mentally or if we add team stats)
            # Actually, we can just iterate all drivers in results if we want.
            # But the requirement is "Two drivers from the same team".
            # We will iterate teams as before to be safe.
            
            team_drivers = {}
            for d in f1_session.drivers:
                try:
                    drv = f1_session.get_driver(d)
                    team = drv['TeamName']
                    if not team: continue
                    if team not in team_drivers:
                         team_drivers[team] = []
                    team_drivers[team].append(d)
                except:
                    continue
            
            for team, drivers_in_team in team_drivers.items():
                if len(drivers_in_team) < 2:
                    continue # only teams with pairs
                
                # Identify teammates for ranking context (rank is per phase per team?)
                # "Compare teammates ... Lap rank within team"
                
                # Gather all rows for this team first, then rank them per phase?
                team_rows = []
                
                # If Q split available, look for Q1, Q2, Q3 per driver
                phases_to_check = ['Q1', 'Q2', 'Q3'] if has_q_split else ['ALL']
                
                for d_code in drivers_in_team:
                    try:
                        # Get driver info from results/session
                        drv_info = f1_session.get_driver(d_code)
                        d_laps = f1_session.laps.pick_driver(d_code)

                        for phase in phases_to_check:
                            target_lap = None
                            
                            if phase == 'ALL':
                                # Standard fastest lap
                                target_lap = d_laps.pick_fastest()
                            else:
                                # Look up the time in results
                                # drv_info acts as the row in results usually? 
                                # f1_session.get_driver returns Series from results.
                                q_time = drv_info.get(phase)
                                
                                if pd.isna(q_time):
                                    continue # Driver didn't set time in this phase
                                
                                # Find lap matching this time
                                # Rounding issues? FastF1 results time is usually exact sum of sectors. LapTime is also.
                                # Let's try exact match with some tolerance if needed.
                                
                                # Match LapTime. 
                                candidates = d_laps[d_laps['LapTime'] == q_time]
                                if not candidates.empty:
                                    target_lap = candidates.iloc[0]
                                else:
                                    # Fallback: maybe approximate match? or Pick fastest in that generic 'session' window?
                                    # If exact match fails, it might be due to Deleted lap logic or something? 
                                    # Actually, let's just pick the lap closest to that time? 
                                    # Or if not found, we skip? 
                                    # Let's try exact first. If empty, maybe print warning.
                                    # Safe fallback: pick matches within 1ms?
                                    import datetime
                                    delta = pd.Timedelta(milliseconds=1)
                                    candidates = d_laps[(d_laps['LapTime'] >= q_time - delta) & (d_laps['LapTime'] <= q_time + delta)]
                                    if not candidates.empty:
                                        target_lap = candidates.iloc[0]
                            
                            if target_lap is None or pd.isna(target_lap['LapTime']):
                                continue

                            # Telemetry aggregates
                            try:
                                tel = target_lap.get_telemetry()
                                avg_speed = tel['Speed'].mean() if 'Speed' in tel else None
                                max_speed = tel['Speed'].max() if 'Speed' in tel else None
                                throttle_avg = tel['Throttle'].mean() if 'Throttle' in tel else None
                            except:
                                avg_speed = None
                                max_speed = None
                                throttle_avg = None

                            row = {
                                "qualifying_phase": phase if phase != 'ALL' else "",
                                "event_name": event,
                                "session": session,
                                "team": team,
                                "driver_name": drv_info['BroadcastName'] or drv_info['FullName'] or d_code,
                                "driver_code": drv_info['Abbreviation'] or d_code,
                                "car_number": drv_info['DriverNumber'],
                                "lap_time": str(target_lap['LapTime']).split('days')[-1].strip(),
                                "lap_time_ms": target_lap['LapTime'].total_seconds() * 1000,
                                "tire_compound": target_lap['Compound'],
                                "average_speed": f"{avg_speed:.2f}" if avg_speed else "",
                                "max_speed": f"{max_speed:.2f}" if max_speed else "",
                                "throttle_avg": f"{throttle_avg:.2f}" if throttle_avg else "",
                                "brake_events": "",
                                "sector1_time": str(target_lap['Sector1Time']).split('days')[-1].strip() if not pd.isna(target_lap['Sector1Time']) else "",
                                "sector2_time": str(target_lap['Sector2Time']).split('days')[-1].strip() if not pd.isna(target_lap['Sector2Time']) else "",
                                "sector3_time": str(target_lap['Sector3Time']).split('days')[-1].strip() if not pd.isna(target_lap['Sector3Time']) else "",
                                "lap_rank_within_team": 0 # to be calculated
                            }
                            team_rows.append(row)
                    except Exception as e:
                        print(f"Error processing {d_code} in pair logic: {e}")
                        continue
                
                # Rank within team per phase
                # Group by phase
                rows_by_phase = {}
                for r in team_rows:
                    p = r['qualifying_phase']
                    if p not in rows_by_phase: rows_by_phase[p] = []
                    rows_by_phase[p].append(r)
                
                for p, rows in rows_by_phase.items():
                    # Sort by lap_time_ms
                    rows.sort(key=lambda x: x['lap_time_ms'])
                    for i, r in enumerate(rows, 1):
                        r['lap_rank_within_team'] = i
                    summary_data.extend(rows)
            
            output_df = pd.DataFrame(summary_data)
            col_list = [
                "qualifying_phase", "event_name", "session", "team", "driver_name", "driver_code", "car_number",
                "lap_time", "lap_time_ms", "tire_compound", 
                "average_speed", "max_speed", "throttle_avg", "brake_events",
                "sector1_time", "sector2_time", "sector3_time", "lap_rank_within_team"
            ]
            for c in col_list:
                if c not in output_df.columns:
                    output_df[c] = ""
            output_df = output_df[col_list]
        
        elif type == 'final_speed':
            # TASK 1: Final Speeds by Driver and Team
            # Definition: Final speed = maximum speed reached at the end of the longest straight during the session. (Approximated by Max Speed in session)
            
            driver_stats = []
            
            if not selected_drivers:
                 # Default to all available drivers if none selected
                try:
                    driver_list = f1_session.drivers
                except:
                    driver_list = []
            else:
                driver_list = selected_drivers
            
            for d in driver_list:
                try:
                    drv = f1_session.get_driver(d)
                    if not drv['DriverNumber']: continue # skip valid check

                    d_laps = f1_session.laps.pick_driver(d)
                    fastest = d_laps.pick_fastest()
                    
                    if fastest is None or pd.isna(fastest['LapTime']):
                        continue
                        
                    # Get telemetry for max speed
                    try:
                        tel = fastest.get_telemetry()
                        max_speed = tel['Speed'].max()
                    except:
                        max_speed = None
                    
                    driver_stats.append({
                        "driver_code": drv['Abbreviation'],
                        "driver_name": drv['BroadcastName'] or drv['FullName'],
                        "team": drv['TeamName'],
                        "final_speed_kph": max_speed
                    })
                except Exception as ex:
                    print(f"Error processing final speed for {d}: {ex}")
                    continue
            
            output_df = pd.DataFrame(driver_stats)
            # Sort by speed descending
            if not output_df.empty:
                output_df = output_df.sort_values(by='final_speed_kph', ascending=False)

        elif type == 'race_pace':
            # TASK 2: Race Pace by Driver (Ordered)
            # Definition: Race pace = median lap time of valid race laps.
            # Filtering: Exclude In-laps, Out-laps, SC, VSC, Pit stops. Include only green flag.
            
            pace_stats = []
            
            # Ensure we use all drivers for a ranking unless restricted? 
            # Usually rankings imply everyone. Let's use all drivers if user didn't specify.
            target_drivers = selected_drivers if selected_drivers else f1_session.drivers
            
            for d in target_drivers:
                try:
                    drv = f1_session.get_driver(d)
                    d_laps = f1_session.laps.pick_driver(d)
                    
                    # Filtering Rules
                    # 1. Green flag only (TrackStatus == '1')
                    # 2. Exclude In/Out laps (usually marked by PitInTime/PitOutTime not null? Or use IsAccurate? )
                    # FastF1 `pick_quicklaps` or `pick_wo_box` ?
                    # Detailed filtering:
                    # - TrackStatus == '1' (Green)
                    # - No PitIn/PitOut
                    
                    # Filter for Green Flag:
                    # Laps have 'TrackStatus'. It is a string code. '1' is Green. 
                    # Sometimes it's '12' (Yellow in sector 2). 
                    # "Only include green-flag laps" -> strictly '1'? Or '1' implies green all around.
                    # Let's assume TrackStatus == '1'.
                    
                    # FastF1 documentation says TrackStatus is for the END of the lap? 
                    # Actually, let's stick to standard clean lap filtering:
                    # Pick laps where NO safety car / VSC occurred? 
                    # Using `pick_track_status('1')`
                    
                    clean_laps = d_laps.pick_track_status('1')
                    
                    # Exclude laps with pit stops
                    # PitIn, PitOut columns are non-null? 
                    # clean_laps = clean_laps[clean_laps['PitInTime'].isna() & clean_laps['PitOutTime'].isna()] 
                    # Actually fastf1 `pick_wo_box()` removes in/out laps.
                    clean_laps = clean_laps.pick_wo_box()
                    
                    # Calculate Median
                    if clean_laps.empty:
                        median_time = None
                        median_seconds = float('inf')
                    else:
                        median_time = clean_laps['LapTime'].median()
                        median_seconds = median_time.total_seconds()
                    
                    if median_time:
                         pace_stats.append({
                            "driver_code": drv['Abbreviation'],
                            "driver_name": drv['BroadcastName'] or drv['FullName'],
                            "team": drv['TeamName'],
                            "race_pace_median": str(median_time).split('days')[-1].strip(),
                            "race_pace_seconds": median_seconds,
                            "valid_laps_count": len(clean_laps)
                        })
                except Exception as ex:
                    print(f"Error processing race pace for {d}: {ex}")
            
            output_df = pd.DataFrame(pace_stats)
            if not output_df.empty:
                output_df = output_df.sort_values(by='race_pace_seconds', ascending=True)
                output_df['rank'] = range(1, len(output_df) + 1)
                # Cleanup helper column
                output_df = output_df.drop(columns=['race_pace_seconds'])

        elif type == 'pole_microsectors':
            # TASK 3: Previous Year Pole Lap with Microsectors
            # 1. Identify prev year
            prev_year = year - 1
            
            try:
                # Load previous year session
                # Assume same event name and session name
                # Note: Events might change names slightly (e.g. "Saudi Arabian Grand Prix"). 
                # This is risky but standard approach for "previous year" logic.
                
                # We need to find the event schedule for prev year to match exact event name?
                # Or just try loading with same parameters.
                
                session_type = 'Q' # Pole implies Qualifying usually. 
                # If current session is 'R', user might still want Pole data? 
                # Prompt says "Identify pole driver from Q3". So we must load Q from prev year.
                
                # Check if we can just try loading
                py_session = fastf1.get_session(prev_year, event, 'Q')
                py_session.load()
                
                # Identify Pole Position (rank 1)
                # py_session.results contains 'Position'
                pole_driver_info = py_session.results[py_session.results['Position'] == 1.0].iloc[0]
                pole_driver_code = pole_driver_info['Abbreviation']
                
                # Extract fastest Q3 lap
                d_laps = py_session.laps.pick_driver(pole_driver_code)
                pole_lap = d_laps.pick_fastest()
                
                # Telemetry
                tel = pole_lap.get_telemetry()
                
                # Microsectors: Split lap distance into N=25 equal chunks?
                # "Microsectors = equal-distance splits of the lap"
                # Let's say 25 chunks.
                n_microsectors = 25
                total_dist = tel['Distance'].max()
                chunk_size = total_dist / n_microsectors
                
                tel['MicrosectorID'] = (tel['Distance'] // chunk_size).astype(int) + 1
                
                # Aggregate per microsector
                # Mean speed, Time? 
                # Maybe just return the center point of the sector? 
                # "Aggregate telemetry per microsector"
                
                # Let's aggregate: Mean Speed, Mean Throttle, Mean Brake? 
                # And maybe Time valid at start/end? 
                
                ms_stats = []
                for ms_id in range(1, n_microsectors + 1):
                    chunk = tel[tel['MicrosectorID'] == ms_id]
                    if chunk.empty: continue
                    
                    # Calculate time elapsed at start of microsector (approx)
                    # We take the first timestamp in the chunk or min time
                    time_sec = chunk['Time'].min().total_seconds()

                    ms_stats.append({
                        "year": prev_year,
                        "event": event,
                        "driver": pole_driver_code,
                        "microsector_id": ms_id,
                        "time_elapsed_seconds": time_sec,
                        "avg_speed": chunk['Speed'].mean(),
                        "max_speed": chunk['Speed'].max(),
                        "avg_throttle": chunk['Throttle'].mean(),
                        "avg_brake": chunk['Brake'].mean(),
                        "distance_start": (ms_id - 1) * chunk_size,
                        "distance_end": ms_id * chunk_size
                    })
                
                output_df = pd.DataFrame(ms_stats)
                
            except Exception as e:
                # Fallback or Error
                print(f"Error fetching previous year pole: {e}")
                # Return empty or error info
                output_df = pd.DataFrame([{"error": f"Could not retrieve previous year data: {str(e)}" }])
        # Convert to CSV
        stream = io.StringIO()
        output_df.to_csv(stream, index=False)
        response = Response(content=stream.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
