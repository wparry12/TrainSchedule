from datetime import datetime
import streamlit as st
import os
from Code.Database import save_schedule, load_schedule

# Party Train page
def party_train_page():
    st.header("🎉 Party Trains")

    schedule = load_schedule()

    # Sort trains by departure_time (e.g. "13:45") as datetime objects
    schedule.sort(key=lambda x: datetime.strptime(x['departure_time'], "%H:%M"))

    for train in schedule:
        current_status = train.get("party_train", False)
        new_status = st.checkbox(
            f"Mark train at {train['departure_time']} as a Party Train", value=current_status
        )
        train["party_train"] = new_status

    if st.button("Save Changes"):
        save_schedule(schedule)
        st.success("Party train settings updated.")
