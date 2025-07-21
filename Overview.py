import streamlit as st
import os
import matplotlib.cm
from datetime import datetime, time, timedelta
from Code.Database import save_schedule, load_schedule
from zoneinfo import ZoneInfo

LOCAL = ZoneInfo("Europe/London")

def has_departed(dep_time_str):
    now = datetime.now(LOCAL)
    dep_time = datetime.strptime(dep_time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
    )
    return dep_time < now

def format_24_to_12(time_str):
    return datetime.strptime(time_str, "%H:%M").strftime("%-I:%M %p")

def create_group_colour_map(schedule, cmap_name='tab20'):
    group_ids = sorted({
        carriage['group_id']
        for train in schedule
        for carriage in train['carriages']
        if carriage.get('group_size', 0)
    })
    cmap = matplotlib.cm.get_cmap(cmap_name, len(group_ids))
    return {
        gid: f'rgb({int(cmap(i)[0]*255)}, {int(cmap(i)[1]*255)}, {int(cmap(i)[2]*255)})'
        for i, gid in enumerate(group_ids)
    }

# Function to generate times in 5-minute increments
def generate_time_options(start_time="00:00", end_time="23:55"):
    start = datetime.strptime(start_time, "%H:%M")
    end = datetime.strptime(end_time, "%H:%M")
    times = []
    while start <= end:
        times.append(start.strftime("%H:%M"))
        start += timedelta(minutes=5)
    return times

def booking_overview_page():
    st.title("📊 Train Booking Overview")

    schedule = load_schedule()
    if not schedule:
        return

    # Sort schedule by departure time
    schedule.sort(key=lambda x: datetime.strptime(x['departure_time'], "%H:%M"))

    group_colour_map = create_group_colour_map(schedule)

    # Generate time options in 5-minute intervals for the filter menu
    time_options = generate_time_options()

    # Time filter dropdown (12h format display)
    time_map = {t['departure_time']: format_24_to_12(t['departure_time']) for t in schedule}
    inv_time_map = {v: k for k, v in time_map.items()}
    selected_12hr = st.multiselect("Filter by Departure Time:", list(time_map.values()), default=None)
    selected_times = [inv_time_map[t] for t in selected_12hr]

    # Filter checkboxes
    show_cancelled = st.checkbox("Show Cancelled Trains", value=False)
    show_previous = st.checkbox("Show Previous Trains", value=False)
    show_party = st.checkbox("Show Party Trains", value=True)
    show_Schools = st.checkbox("Show School Trains", value=True)
    show_wheelchair = st.checkbox("Show Wheelchair Users", value=True)
    show_toddlers = st.checkbox("Show Toddlers", value=True)

    # Filtered schedule
    filtered = [
        t for t in schedule
        if (not selected_times or t['departure_time'] in selected_times)
        and (show_cancelled or not t.get('cancelled', False))
        and (show_party or not t.get('party_train', False))
        and (show_Schools or not t.get('school_name', False))
        and (show_previous or not has_departed(t['departure_time']))
    ]

    if not filtered:
        st.info("No trains match your filters.")
        return

    for idx, train in enumerate(filtered):
        dep = train['departure_time']
        formatted_dep = format_24_to_12(dep)
        is_cancelled = train.get('cancelled', False)
        is_party = train.get('party_train', False)
        is_school = train.get('school_name', False)

        tags = []
        if is_cancelled:
            tags.append("❌ CANCELLED")
        if is_party:
            tags.append("🎉 PARTY TRAIN")
        if is_school:
            tags.append("🏫🎓 " + train.get("school_name"))

        container = st.container()
        with container:
            cols = st.columns([9, 1])
            with cols[0]:
                st.markdown(f"### 🚆 Train leaves at {formatted_dep} {' - ' + ' '.join(tags) if tags else ''}")
            with cols[1]:
                edit_key = f"edit_btn_{idx}"
                if st.button("Edit", key=edit_key):
                    st.session_state["edit_idx"] = idx

            if st.session_state.get("edit_idx") == idx:
                new_time_key = f"time_input_{idx}"
                current_time = datetime.strptime(dep, "%H:%M").time()
                new_time = st.time_input("Edit Time", value=current_time, key=new_time_key, step=timedelta(minutes=5))

                new_time = st.time_input("Edit Time", value=current_time, key=new_time_key, step=timedelta(minutes=5))
                new_time_24 = new_time.strftime("%H:%M")

                if new_time_24 != dep:
                    if any(t['departure_time'] == new_time_24 and t != train for t in schedule):
                        st.warning(f"⛔ A train already departs at {format_24_to_12(new_time_24)}.")
                    else:
                        if st.button("Confirm Update", key=f"confirm_update_{idx}"):
                            actual_idx = schedule.index(train)
                            schedule[actual_idx]['departure_time'] = new_time_24
                            save_schedule(schedule)
                            st.success(f"Time updated to {format_24_to_12(new_time_24)}")
                            del st.session_state["edit_idx"]
                            st.rerun()


            carriage_cols = st.columns(8)
            for i, carriage in enumerate(train['carriages']):
                size = carriage.get('group_size', 0)
                gid = carriage.get('group_id', 0)
                toddlers = carriage.get('toddlers', 0)
                wheelchair = carriage.get('wheelchair', False)

                if is_cancelled:
                    colour = '#ff4d4d'
                elif is_party:
                    colour = '#add8e6' if i % 2 == 0 else '#ffb6c1'
                elif is_school:
                    colour = "#ddc446"
                else:
                    colour = group_colour_map.get(gid, '#eee') if size else '#eee'

                label = f"👥 {size}" if size else "Empty"
                if show_toddlers and toddlers:
                    label += f"\n👶 {toddlers}"
                if show_wheelchair and wheelchair:
                    label += f"\n♿️"

                with carriage_cols[i]:
                    st.markdown(f"""
                       <div style='background-color:{colour}; border-radius:10px; padding:10px; text-align:center; min-height:80px;'>
                            <b>C{i+1}</b><br>{label.replace(chr(10), '<br>')}
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

    st.subheader("➕ Add New Train")
    with st.form("add_train_form"):
        new_train_time = st.time_input("Departure Time", key="new_train_time", step=timedelta(minutes=5))
        submitted = st.form_submit_button("Add Train")

        new_train_time_24 = new_train_time.strftime("%H:%M")
        if any(t['departure_time'] == new_train_time_24 for t in schedule):
            st.warning(f"⛔ A train already departs at {format_24_to_12(new_train_time_24)}.")
        else:
            if submitted:
                default_carriages = {
                    "1": 2, "2": 4, "3": 4, "4": 2, "5": 2, "6": 4, "7": 4, "8": 2
                }
                new_train = {
                    "departure_time": new_train_time_24,
                    "cancelled": False,
                    "party_train": False,
                    "school_name": "",
                    "carriages": [
                        {"number": c_num, "capacity": cap, "occupied": False, "group_size": 0,
                        "toddlers": 0, "wheelchair": False, "group_id": 0}
                        for c_num, cap in default_carriages.items()
                    ]
                }
                schedule.append(new_train)
                save_schedule(schedule)
                st.success(f"Train at {format_24_to_12(new_train_time_24)} added.")
                st.rerun()


if __name__ == "__main__":
    if "edit_idx" not in st.session_state:
        st.session_state["edit_idx"] = None
    booking_overview_page()