import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from Code.Database import list_presets, load_preset, save_preset, delete_preset, save_schedule

LOCAL = ZoneInfo("Europe/London")


def parse_time_local(time_str):
    now = datetime.now(LOCAL)
    return datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
    )


def preset_schedule_page():
    st.title("📆 Train Schedule Presets")

    # Initialise schedule in session state
    if "schedule" not in st.session_state:
        st.session_state.schedule = []

    schedule = st.session_state.schedule

    # === Load Existing Schedule Presets ===
    st.subheader("📁 Load Existing Schedule Presets")
    presets = list_presets()

    if presets:
        for preset in presets:
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.write(preset)
            with cols[1]:
                if st.button("Load", key=f"load_{preset}"):
                    new_schedule = load_preset(preset)
                    if new_schedule is None:
                        st.error(f"Preset '{preset}' not found in DB.")
                    else:
                        save_schedule(new_schedule)
                        st.session_state.schedule = new_schedule
                        for key in ["confirm_c45", "feedback"]:
                            st.session_state.pop(key, None)
                        st.success(f"Preset '{preset}' loaded and applied.")
                        st.rerun()
            with cols[2]:
                if st.button("Delete", key=f"delete_{preset}"):
                    if delete_preset(preset):
                        st.success(f"Preset '{preset}' deleted.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete preset '{preset}'.")
    else:
        st.info("No presets saved yet.")

    st.markdown("---")

    # === Save Current Schedule as New Preset ===
    st.subheader("💾 Save Current Schedule as New Preset")
    preset_name = st.text_input("Enter a name for the new preset", key="preset_name")

    if st.button("Save Current Schedule"):
        if schedule:
            if preset_name.strip():
                save_preset(preset_name.strip(), schedule)
                st.success(f"Preset '{preset_name.strip()}' saved.")
                st.rerun()
            else:
                st.error("Please enter a valid preset name.")
        else:
            st.error("No schedule to save.")

    st.markdown("---")

    # === Display Current Schedule ===
    st.subheader("🛤️ Current Schedule")

    if schedule:
        for i, train in enumerate(schedule):
            cols = st.columns([6, 1])
            with cols[0]:
                st.write(f"Train {i + 1} - Departure at {train['departure_time']}")
            with cols[1]:
                if st.button("🗑️ Remove", key=f"remove_{i}"):
                    schedule.pop(i)
                    st.session_state.schedule = schedule
                    st.rerun()
    else:
        st.info("No trains in the current schedule.")

    st.markdown("---")

    # === Add New Train ===
    st.subheader("➕ Add New Train")
    new_time_input = st.text_input("Enter departure time (HH:MM)", key="new_train_time")

    if new_time_input:
        try:
            parsed_time = parse_time_local(new_time_input)
            formatted_time = parsed_time.strftime("%H:%M")
            time_exists = any(train["departure_time"] == formatted_time for train in schedule)

            if time_exists:
                st.warning(f"A train already departs at {formatted_time}. Please choose a different time.")
            else:
                if st.button("Add Train"):
                    default_carriages = {
                        "1": 2, "2": 4, "3": 4, "4": 2,
                        "5": 2, "6": 4, "7": 4, "8": 2,
                    }
                    new_train = {
                        "departure_time": formatted_time,
                        "cancelled": False,
                        "party_train": False,
                        "school_name": "",
                        "carriages": [
                            {
                                "number": c_num,
                                "capacity": cap,
                                "occupied": False,
                                "group_size": 0,
                                "toddlers": 0,
                                "wheelchair": False,
                                "group_id": 0,
                            }
                            for c_num, cap in default_carriages.items()
                        ],
                    }
                    schedule.append(new_train)
                    st.session_state.schedule = schedule
                    st.success(f"Added train at {formatted_time}")
                    st.rerun()

        except ValueError:
            st.error("Invalid time format! Please enter time as HH:MM.")

    # Final save of schedule
    st.session_state.schedule = schedule


if __name__ == "__main__":
    preset_schedule_page()
