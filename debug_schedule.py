import fastf1
import datetime

try:
    y = datetime.datetime.now().year
    s = fastf1.get_event_schedule(y)
    print("Columns:", s.columns)
    print("First row:", s.iloc[0] if not s.empty else "Empty")
except Exception as e:
    print(e)
