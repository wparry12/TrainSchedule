import streamlit as st
from Code.Database import list_presets, load_preset, save_preset, delete_preset, save_schedule

def preset_schedule_page():
    st.title("📆 Train Schedule Presets")

    # Initialize schedule in session state
    if "schedule" not in st.session_state:
        st.session_state.schedule = []

    schedule = st.session_state.schedule

    # === List Saved Presets with Load & Delete ===
    st.subheader("📁 Load Existing Schedule Presets")

    presets = list_presets()
    if presets:
        for preset in presets:
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.write(preset)
            with cols[1]:
                if st.button(f"Load", key=f"load_{preset}"):
                    new_schedule = load_preset(preset)
                    if new_schedule is None:
                        st.error(f"Preset '{preset}' not found in DB.")
                    else:
                        save_schedule(new_schedule)  # Save to main schedule tables
                        st.session_state.schedule = new_schedule
                        for key in ["confirm_c45", "feedback"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.success(f"Preset '{preset}' loaded and applied.")
                        st.rerun()
            with cols[2]:
                if st.button(f"Delete", key=f"delete_{preset}"):
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

    # === Display Current Schedule with Option to Remove Trains ===
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

    # === Add New Train Manually ===
    st.subheader("➕ Add New Train")
    new_time = st.text_input("Enter departure time (HH:MM)", key="new_train_time")

    if st.button("Add Train"):
        from Code.Time import parse_time_utc

        try:
            parse_time_utc(new_time, "%H:%M")
        except ValueError:
            st.error("Invalid time format! Please enter time as HH:MM.")
        else:
            default_carriages = {
                "1": 2,
                "2": 4,
                "3": 4,
                "4": 2,
                "5": 2,
                "6": 4,
                "7": 4,
                "8": 2,
            }
            new_train = {
                "departure_time": new_time,
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
            st.success(f"Added train at {new_time}")
            st.rerun()

    # Save schedule to session state
    st.session_state.schedule = schedule


if __name__ == "__main__":
    preset_schedule_page()
