import streamlit as st
import os
import matplotlib.cm
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

def is_valid_time(t):
    try:
        parse_time_local(t)
        return True
    except:
        return False

def booking_overview_page():
    st.title("📊 Train Booking Overview")

    schedule = load_schedule()
    if not schedule:
        return

    # Sort schedule by departure_time to keep order consistent after edits
    schedule.sort(key=lambda x: parse_time_local(x['departure_time']))

    group_colour_map = create_group_colour_map(schedule)

    # Filter UI
    all_times = [train['departure_time'] for train in schedule]
    selected_times = st.multiselect("Filter by Departure Time:", all_times, default=None)

    show_cancelled = st.checkbox("Show Cancelled Trains", value=True)
    show_party = st.checkbox("Show Party Trains", value=True)
    show_Schools = st.checkbox("Show School Trains", value=True)
    show_wheelchair = st.checkbox("Show Wheelchair Users", value=True)
    show_toddlers = st.checkbox("Show Toddlers", value=True)

    # Filter trains based on selections
    filtered = [
        t for t in schedule
        if (not selected_times or t['departure_time'] in selected_times)
        and (show_cancelled or not t.get('cancelled', False))
        and (show_party or not t.get('party_train', False))
        and (show_Schools or not t.get('school_name', False))
    ]

    if not filtered:
        st.info("No trains match your filters.")
        return

    for idx, train in enumerate(filtered):
        dep = train['departure_time']
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
                st.markdown(f"### 🚆 Train leaves at {dep} {' - ' + ' '.join(tags) if tags else ''}")
            with cols[1]:
                edit_key = f"edit_btn_{idx}"
                if st.button("Edit", key=edit_key):
                    st.session_state["edit_idx"] = idx

            # Editing logic: show input box only if current train is being edited
            if st.session_state.get("edit_idx") == idx:
                new_time_key = f"time_input_{idx}"
                new_time = st.text_input("Edit Time (HH:MM)", value=dep, key=new_time_key)

                if new_time:
                    if is_valid_time(new_time):
                        if new_time != dep:
                            # Find the actual index in schedule and update there
                            actual_idx = schedule.index(train)
                            schedule[actual_idx]['departure_time'] = new_time
                            save_schedule(schedule)
                            st.success(f"Time updated to {new_time}")
                            # Clear editing index so input disappears after update
                            del st.session_state["edit_idx"]
                            st.rerun()
                    else:
                        st.error("Invalid time format. Please enter HH:MM (24-hour format).")

            # Show carriages with colors and details
            carriage_cols = st.columns(8)
            for i, carriage in enumerate(train['carriages']):
                size = carriage.get('group_size', 0)
                gid = carriage.get('group_id', 0)
                toddlers = carriage.get('toddlers', 0)
                wheelchair = carriage.get('wheelchair', False)

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
        new_train_time = st.text_input("Departure Time (HH:MM)", key="new_train_time")
        submitted = st.form_submit_button("Add Train")

        if submitted:
            if is_valid_time(new_train_time):
                # Check if time already exists
                if any(t['departure_time'] == new_train_time for t in schedule):
                    st.warning("A train with this departure time already exists.")
                else:
                    default_carriages = {
                        "1": 2, "2": 4, "3": 4, "4": 2, "5": 2, "6": 4, "7": 4, "8": 2
                    }   
                    new_train = {
                        "departure_time": new_train_time,
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
                    st.success(f"Train at {new_train_time} added.")
                    st.rerun()
            else:
                st.error("Invalid time format. Please enter HH:MM (24-hour format).")

if __name__ == "__main__":
    if "edit_idx" not in st.session_state:
        st.session_state["edit_idx"] = None
    booking_overview_page()
