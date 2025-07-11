import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from Code.Database import save_schedule, load_schedule

LOCAL = ZoneInfo("Europe/London")

now_local = datetime.now(LOCAL)

def parse_time_local(time_str):
    now = datetime.now(LOCAL)
    dt = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
    )
    return dt

def display_assignment_success(schedule, group_id):
    for train in schedule:
        carriages = [c for c in train["carriages"] if c.get("group_id") == group_id]
        if carriages:
            carriages.sort(key=lambda c: int(c["number"]))
            sizes = [str(c["group_size"]) for c in carriages]
            toddler_count = sum(c["toddlers"] for c in carriages)
            wheelchair = any(c["wheelchair"] for c in carriages)
            summary = f"Carriages {', '.join(c['number'] for c in carriages)}, Train {train['departure_time']}"
            details = f"Group size: {' + '.join(sizes)}"
            extras = []
            if wheelchair:
                extras.append("wheelchair")
            if toddler_count > 0:
                extras.append(f"{toddler_count} toddler(s)")
            extra_str = f" ({', '.join(extras)})" if extras else ""
            st.success(f"✅ Assigned to {summary}, {details}{extra_str}")
            break

def display_feedback():
    if st.session_state.get("feedback"):
        fb = st.session_state.feedback
        if fb["type"] == "success":
            updated_schedule, gid = fb["data"]
            display_assignment_success(updated_schedule, gid)
        elif fb["type"] == "error":
            st.error(fb["data"])
        st.session_state.feedback = None

def is_future_train(train):
    now = now_local()
    try:
        dep_time = parse_time_local(train['departure_time']).replace(year=now.year, month=now.month, day=now.day)
        return dep_time >= now
    except:
        return False

def manual_group_assignment_page():
    schedule = load_schedule()
    if not schedule:
        st.warning("No schedule loaded")
        return

    assignable_schedule = [
        train for train in schedule
        if not train.get("school_name") and not train.get("cancelled") and not train.get("party_train") and is_future_train(train)
    ]
    if not assignable_schedule:
        st.warning("No assignable trains available.")
        return

    selected_train_id = st.session_state.get("selected_train_id", None)
    selected_carriage_index = st.session_state.get("selected_carriage_index", None)

    if selected_train_id is not None and selected_carriage_index is not None:
        train = next((t for t in assignable_schedule if t['id'] == selected_train_id), None)
        if train:
            st.title(f"📝 Assign Group to Carriage {selected_carriage_index + 1} at {train['departure_time']}")
            display_feedback()  # Show feedback immediately below the title

            carriage = train['carriages'][selected_carriage_index]
            if carriage.get("occupied", False):
                st.error(f"Carriage {selected_carriage_index + 1} on train {train['departure_time']} is already occupied.")
            else:
                capacity = carriage.get("capacity", 6)
                with st.form("assign_form"):
                    group_size = st.number_input("Adults and Children", min_value=1, max_value=capacity, value=2)
                    toddlers = st.number_input("Toddlers", min_value=0, max_value=capacity, value=0)

                    wheelchair_allowed = (selected_carriage_index == 1)
                    wheelchair = st.checkbox("♿ Wheelchair Access Needed") if wheelchair_allowed else False

                    submit = st.form_submit_button("Assign Group")

                    if submit:
                        # Recompute next_id here for assignment
                        all_ids = [c.get('group_id') for t in schedule for c in t['carriages'] if c.get('group_id')]
                        next_id = max(all_ids, default=0) + 1

                        if group_size > capacity:
                            st.error(f"Carriage only supports {capacity} passengers.")
                        elif not wheelchair_allowed and wheelchair:
                            st.error("Wheelchair access is only available in Carriage 2.")
                        else:
                            carriage.update({
                                "group_size": group_size,
                                "group_id": next_id,
                                "occupied": True,
                                "toddlers": toddlers,
                                "wheelchair": wheelchair
                            })
                            for t in schedule:
                                if t["id"] == train["id"]:
                                    t["carriages"][selected_carriage_index] = carriage
                                    break

                            save_schedule(schedule)

                            # Set feedback for success
                            st.session_state.feedback = {"type": "success", "data": (schedule, next_id)}

                            # Reset selection to clear form
                            st.session_state.selected_train_id = None
                            st.session_state.selected_carriage_index = None

                            st.rerun()
        else:
            st.title("📝 Manual Group Assignment")
            display_feedback()
    else:
        st.title("📝 Manual Group Assignment")
        display_feedback()

    st.markdown("### Select a Train and Carriage")

    for train_idx, train in enumerate(assignable_schedule):
        dep = train['departure_time']
        st.subheader(f"⏰ {dep}")

        cols = st.columns(len(train['carriages']))
        for i, carriage in enumerate(train['carriages']):
            occupied = carriage.get("occupied", False)
            label = f"🚫 C{i+1}" if occupied else f"🟢 C{i+1}"
            if i == 1:
                label += " ♿"
            with cols[i]:
                if st.button(label, key=f"train{train_idx}_carriage{i}"):
                    st.session_state.feedback = None
                    st.session_state.selected_train_id = train['id']
                    st.session_state.selected_carriage_index = i
                    st.rerun()
