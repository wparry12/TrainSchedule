import streamlit as st
import os
from datetime import datetime
from Code.Database import save_schedule, load_schedule
from zoneinfo import ZoneInfo

LOCAL = ZoneInfo("Europe/London")

def parse_time_local(time_str):
    now = datetime.now(LOCAL)
    dt = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
    )
    return dt

# Cancel train page
def train_cancel_page():
    st.header("🚦 Cancel or Enable Trains")

    schedule = load_schedule()

    # Sort by departure time
    schedule.sort(key=lambda x: parse_time_local(x['departure_time']))

    for train in schedule:
        # Convert 24H to 12H with AM/PM, removing leading zero
        try:
            dt_24h = parse_time_local(train['departure_time'])
            time_12h = dt_24h.strftime("%I:%M %p").lstrip("0")
        except Exception:
            time_12h = train['departure_time']

        current_status = train.get("cancelled", False)
        new_status = st.checkbox(
            f"Cancel train at {time_12h}", value=current_status, key=train['departure_time']
        )
        train["cancelled"] = new_status

    if st.button("Save Changes"):
        save_schedule(schedule)
        st.success("Train schedule updated.")
