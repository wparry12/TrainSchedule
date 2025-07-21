import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from Code.Database import list_presets, load_preset, save_preset, delete_preset, save_schedule


def preset_schedule_page():
    st.title("📆 Train Schedule Presets")
    LOCAL = ZoneInfo("Europe/London")

    # Initialise or load schedule
    if "schedule" not in st.session_state:
        st.session_state.schedule = []
    schedule = st.session_state.schedule

    # === Section 1: Load or Delete Existing Presets ===
    st.subheader("📁 Load Existing Schedule Presets")
    presets = list_presets()

    if presets:
        for preset in presets:
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.write(preset)
            with cols[1]:
                if st.button("Load", key=f"load_{preset}"):
                    loaded = load_preset(preset)
                    if loaded is not None:
                        st.session_state.schedule = loaded
                        save_schedule(loaded)
                        for key in ["confirm_c45", "feedback"]:
                            st.session_state.pop(key, None)
                        st.success(f"Preset '{preset}' loaded.")
                        st.rerun()
                    else:
                        st.error(f"Preset '{preset}' not found.")
            with cols[2]:
                if st.button("Delete", key=f"delete_{preset}"):
                    if delete_preset(preset):
                        st.success(f"Preset '{preset}' deleted.")
                        st.rerun()
                    else:
                        st.error(f"Failed to delete '{preset}'.")
    else:
        st.info("No saved presets yet.")

    st.markdown("---")

    # === Section 2: Save Current Schedule ===
    st.subheader("💾 Save Current Schedule as New Preset")
    preset_name = st.text_input("Enter a name for the new preset", key="preset_name")

    if st.button("Save Current Schedule"):
        if not schedule:
            st.error("⚠️ No schedule to save.")
        elif not preset_name.strip():
            st.error("❌ Please enter a valid name.")
        else:
            save_preset(preset_name.strip(), schedule)
            st.success(f"Preset '{preset_name.strip()}' saved.")
            st.rerun()

    st.markdown("---")

    # === Section 3: Display & Remove Trains ===
    st.subheader("🛤️ Current Schedule")

    if schedule:
        for i, train in enumerate(schedule):
            try:
                time_obj = datetime.strptime(train["departure_time"], "%H:%M")
                formatted_time = time_obj.strftime("%I:%M %p").lstrip("0")
            except ValueError:
                formatted_time = train["departure_time"]

            cols = st.columns([6, 1])
            with cols[0]:
                st.write(f"Train {i + 1} – Departure: {formatted_time}")
            with cols[1]:
                if st.button("🗑️ Remove", key=f"remove_{i}"):
                    schedule.pop(i)
                    st.session_state.schedule = schedule
                    st.rerun()
    else:
        st.info("No trains in the current schedule.")

    st.markdown("---")

    # === Section 4: Add New Train ===
    st.subheader("➕ Add New Train")
    new_time = st.text_input("Enter departure time (HH:MM)", key="new_train_time")

    existing_times = {t["departure_time"] for t in schedule}
    if new_time.strip() in existing_times:
        st.warning("⚠️ A train with this departure time already exists.")

    if st.button("Add Train"):
        if not new_time.strip():
            st.error("❌ Please enter a departure time.")
        elif new_time.strip() in existing_times:
            st.error("🚫 This departure time is already used.")
        else:
            try:
                now = datetime.now(LOCAL)
                datetime.strptime(new_time.strip(), "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
                )
            except ValueError:
                st.error("⏰ Invalid time format! Please use HH:MM (e.g., 02:30 or 14:00).")
            else:
                default_carriages = {
                    "1": 2, "2": 4, "3": 4, "4": 2,
                    "5": 2, "6": 4, "7": 4, "8": 2,
                }
                new_train = {
                    "departure_time": new_time.strip(),
                    "cancelled": False,
                    "party_train": False,
                    "school_name": "",
                    "carriages": [
                        {
                            "number": num,
                            "capacity": cap,
                            "occupied": False,
                            "group_size": 0,
                            "toddlers": 0,
                            "wheelchair": False,
                            "group_id": 0,
                        }
                        for num, cap in default_carriages.items()
                    ],
                }
                schedule.append(new_train)
                st.session_state.schedule = schedule
                st.success(f"✅ Train added for {new_time.strip()}.")
                st.rerun()


if __name__ == "__main__":
    preset_schedule_page()