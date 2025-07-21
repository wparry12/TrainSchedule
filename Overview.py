import streamlit as st
import matplotlib.cm
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from Code.Database import save_schedule, load_schedule

LOCAL = ZoneInfo("Europe/London")


def has_departed(dep_time_str: str) -> bool:
    now = datetime.now(LOCAL)
    dep_time = datetime.strptime(dep_time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
    )
    return dep_time < now


def format_24_to_12(time_str: str) -> str:
    try:
        return datetime.strptime(time_str, "%H:%M").strftime("%-I:%M %p")
    except ValueError:
        return datetime.strptime(time_str, "%H:%M").strftime("%#I:%M %p")


def create_group_colour_map(schedule: list, cmap_name='tab20') -> dict:
    group_ids = sorted({
        carriage['group_id']
        for train in schedule
        for carriage in train['carriages']
        if carriage.get('group_size', 0) > 0
    })
    cmap = matplotlib.cm.get_cmap(cmap_name, len(group_ids))

    def rgb_to_hex(rgb_tuple):
        return '#{:02x}{:02x}{:02x}'.format(*rgb_tuple)

    colour_map = {}
    for i, gid in enumerate(group_ids):
        rgb = tuple(int(c * 255) for c in cmap(i)[:3])
        colour_map[gid] = rgb_to_hex(rgb)

    return colour_map


def booking_overview_page():
    st.title("📊 Train Booking Overview")

    schedule = load_schedule()
    if not schedule:
        st.info("No schedule data found.")
        return

    # Sort schedule by 24h time
    schedule.sort(key=lambda t: datetime.strptime(t['departure_time'], "%H:%M"))

    group_colour_map = create_group_colour_map(schedule)

    # Multiselect for 12-hour departure time filter
    unique_times_24 = sorted({t['departure_time'] for t in schedule}, key=lambda x: datetime.strptime(x, "%H:%M"))
    time_map_24_to_12 = {t: format_24_to_12(t) for t in unique_times_24}
    time_map_12_to_24 = {v: k for k, v in time_map_24_to_12.items()}

    selected_12hr = st.multiselect(
        "Filter by Departure Time:",
        options=list(time_map_12_to_24.keys()),
        default=None
    )
    selected_times = [time_map_12_to_24[t] for t in selected_12hr] if selected_12hr else []

    # Other filters
    show_cancelled = st.checkbox("Show Cancelled Trains", value=False)
    show_previous = st.checkbox("Show Previous Trains", value=False)
    show_party = st.checkbox("Show Party Trains", value=True)
    show_schools = st.checkbox("Show School Trains", value=True)
    show_wheelchair = st.checkbox("Show Wheelchair Users", value=True)
    show_toddlers = st.checkbox("Show Toddlers", value=True)

    # Filter schedule
    filtered_trains = [
        train for train in schedule
        if (not selected_times or train['departure_time'] in selected_times)
        and (show_cancelled or not train.get('cancelled', False))
        and (show_party or not train.get('party_train', False))
        and (show_schools or not train.get('school_name', False))
        and (show_previous or not has_departed(train['departure_time']))
    ]

    if not filtered_trains:
        st.info("No trains match your filters.")
        return

    for idx, train in enumerate(filtered_trains):
        dep_time_24 = train['departure_time']
        dep_time_12 = format_24_to_12(dep_time_24)
        cancelled = train.get('cancelled', False)
        party_train = train.get('party_train', False)
        school_name = train.get('school_name', "")

        tags = []
        if cancelled:
            tags.append("❌ CANCELLED")
        if party_train:
            tags.append("🎉 PARTY TRAIN")
        if school_name:
            tags.append(f"🏫🎓 {school_name}")

        container = st.container()
        with container:
            cols = st.columns([9, 1])
            with cols[0]:
                tag_str = f" - {' | '.join(tags)}" if tags else ""
                st.markdown(f"### 🚆 Train leaves at {dep_time_12}{tag_str}")
            with cols[1]:
                if st.button("Edit", key=f"edit_btn_{idx}"):
                    st.session_state["edit_idx"] = idx

            # Show time edit field
            if st.session_state.get("edit_idx") == idx:
                current_time = datetime.strptime(dep_time_24, "%H:%M").time()
                new_time = st.time_input(
                    "Edit Departure Time",
                    value=current_time,
                    key=f"time_input_{idx}",
                    step=timedelta(minutes=5)
                )
                new_time_24 = new_time.strftime("%H:%M")

                if new_time_24 != dep_time_24:
                    conflict = any(
                        t['departure_time'] == new_time_24 and t != train for t in schedule
                    )
                    if conflict:
                        st.warning(f"⛔ A train already departs at {format_24_to_12(new_time_24)}.")
                    else:
                        if st.button("Confirm Update", key=f"confirm_update_{idx}"):
                            actual_idx = schedule.index(train)
                            schedule[actual_idx]['departure_time'] = new_time_24
                            save_schedule(schedule)
                            st.success(f"Time updated to {format_24_to_12(new_time_24)}.")
                            del st.session_state["edit_idx"]
                            st.rerun()

            # Show carriages
            carriage_cols = st.columns(8)
            for i, carriage in enumerate(train['carriages']):
                size = carriage.get('group_size', 0)
                gid = carriage.get('group_id', 0)
                toddlers = carriage.get('toddlers', 0)
                wheelchair = carriage.get('wheelchair', False)

                if cancelled:
                    colour = '#ff4d4d'
                elif party_train:
                    colour = '#add8e6' if i % 2 == 0 else '#ffb6c1'
                elif school_name:
                    colour = "#ddc446"
                else:
                    colour = group_colour_map.get(gid, '#eee') if size else '#eee'

                label = f"👥 {size}" if size else "Empty"
                if show_toddlers and toddlers:
                    label += f"\n👶 {toddlers}"
                if show_wheelchair and wheelchair:
                    label += "\n♿️"

                with carriage_cols[i]:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {colour};
                            border-radius: 10px;
                            padding: 10px;
                            text-align: center;
                            min-height: 80px;
                        ">
                            <b>C{i+1}</b><br>{label.replace(chr(10), '<br>')}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            st.markdown("---")

    # Add new train
    st.subheader("➕ Add New Train")
    with st.form("add_train_form"):
        new_train_time = st.time_input("Departure Time", key="new_train_time", step=timedelta(minutes=5))
        submitted = st.form_submit_button("Add Train")

        new_time_24 = new_train_time.strftime("%H:%M")
        if any(t['departure_time'] == new_time_24 for t in schedule):
            st.warning(f"⛔ A train already departs at {format_24_to_12(new_time_24)}.")
        elif submitted:
            default_carriages = {
                "1": 2, "2": 4, "3": 4, "4": 2,
                "5": 2, "6": 4, "7": 4, "8": 2
            }
            new_train = {
                "departure_time": new_time_24,
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
                        "group_id": 0
                    }
                    for c_num, cap in default_carriages.items()
                ]
            }
            schedule.append(new_train)
            save_schedule(schedule)
            st.success(f"Train at {format_24_to_12(new_time_24)} added.")
            st.rerun()


if __name__ == "__main__":
    if "edit_idx" not in st.session_state:
        st.session_state["edit_idx"] = None
    booking_overview_page()