import streamlit as st
import os
from Code.Database import save_schedule, load_schedule

def school_train_page():
    st.header("🏫 School Trains")

    schedule = load_schedule()
    schedule.sort(key=lambda t: t["departure_time"])

    edited = False
    for idx, train in enumerate(schedule):
        st.markdown(
            f"<p style='font-size:24px; font-weight:bold;'>Train at {train['departure_time']}</p>",
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
