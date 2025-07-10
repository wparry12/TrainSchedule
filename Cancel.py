import streamlit as st
import os
from Code.Time import parse_time_utc
from Code.Database import save_schedule, load_schedule

# Cancel train page
def train_cancel_page():
    st.header("🚦 Cancel or Enable Trains")

    schedule = load_schedule()

    # Sort by departure time
    schedule.sort(key=lambda x: parse_time_utc(x['departure_time'], "%H:%M"))

    for train in schedule:
        current_status = train.get("cancelled", False)
        new_status = st.checkbox(
            f"Cancel train at {train['departure_time']}", value=current_status, key=train['departure_time']
        )
        train["cancelled"] = new_status

    if st.button("Save Changes"):
        save_schedule(schedule)
        st.success("Train schedule updated.")
