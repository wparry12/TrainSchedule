import streamlit as st
import os
from datetime import datetime
from Code.Database import save_schedule, load_schedule

def format_time_12h(time_24h):
    dt = datetime.strptime(time_24h, "%H:%M")
    return dt.strftime("%I:%M %p").lstrip("0")

def school_train_page():
    st.header("🏫 School Trains")

    schedule = load_schedule()
    # Sort by departure_time as datetime object for consistency
    schedule.sort(key=lambda t: datetime.strptime(t["departure_time"], "%H:%M"))

    for idx, train in enumerate(schedule):
        dep_12h = format_time_12h(train['departure_time'])
        st.markdown(
            f"<p style='font-size:24px; font-weight:bold;'>Train at {dep_12h}</p>",
            unsafe_allow_html=True
        )

        input_key = f"school_{idx}"
        current_val = st.session_state.get(input_key, train.get("school_name", ""))

        new_name = st.text_input(
            "",
            value=current_val,
            key=input_key
        )
        
        if new_name != train.get("school_name", ""):
            train["school_name"] = new_name.strip()
        
        st.markdown("---")

    if st.button("💾 Save School Trains"):
        save_schedule(schedule)
        st.success("School train data saved.")

if __name__ == "__main__":
    school_train_page()