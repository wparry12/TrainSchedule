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

# Party Train page
def party_train_page():
    st.header("🎉 Party Trains")

    schedule = load_schedule()

    # Sort trains by departure_time (e.g. "13:45") as datetime objects
    schedule.sort(key=lambda x: parse_time_local(x['departure_time']))

    for train in schedule:
        current_status = train.get("party_train", False)
        dep_dt = parse_time_local(train['departure_time'])
        dep_str_12h = dep_dt.strftime("%I:%M %p").lstrip("0")  # convert to 12h format

        new_status = st.checkbox(
            f"Mark train at {dep_str_12h} as a Party Train", value=current_status, key=dep_str_12h
        )
        train["party_train"] = new_status

    if st.button("Save Changes"):
        save_schedule(schedule)
        st.success("Party train settings updated.")

if __name__ == "__main__":
    party_train_page()
