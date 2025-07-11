import streamlit as st
from Code import WC as wc
from Code.SmallGroup import SmallGroupHandler
from Code.MediumGroup import MediumGroupHandler
from Code.LargeGroups import LargeGroupHandler
from Code.Database import save_schedule, load_schedule, create_tables, create_presets_table
from datetime import datetime
from zoneinfo import ZoneInfo

LOCAL = ZoneInfo("Europe/London")

now_local = datetime.now(LOCAL)

def parse_time_local(time_str):
    now = datetime.now(LOCAL)
    dt = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day, tzinfo=LOCAL
    )
    return dt

from Code.Utils import only_c4_c5_available, only_c1_c8_available

WARNING_THRESHOLD_MINUTES = 10

create_tables()
create_presets_table()

def minutes_until_departure(dep_time_str):
    now = datetime.now()
    dep_time = parse_time_local(dep_time_str)
    delta = dep_time - now
    return int((delta.total_seconds() + 59) // 60)

def find_soon_departing_train(schedule):
    for train in schedule:
        if train["cancelled"] or train["party_train"] or train["school_name"] != "":
            continue
        minutes = minutes_until_departure(train["departure_time"])
        if 0 <= minutes <= WARNING_THRESHOLD_MINUTES and any(not c["occupied"] for c in train["carriages"]):
            return train, minutes
    return None, None

def assign_group(schedule, adults, toddlers, wheelchair_count, group_size, group_id, confirmed=False, restricted_carriages=None):
    schedule = sorted(schedule, key=lambda x: parse_time_local(x['departure_time']))

    for train_index, train in enumerate(schedule):
        if train["cancelled"] or train["party_train"] or train["school_name"] != "":
            continue

        minutes = minutes_until_departure(train["departure_time"])
        if minutes < 0:
            continue

        if minutes <= WARNING_THRESHOLD_MINUTES and not confirmed:
            continue

        # --- Restriction mode for specific carriages ---
        if restricted_carriages is not None:
            carriages = [c for c in train["carriages"] if c["number"] in restricted_carriages and not c["occupied"]]
            total_cap = sum(c["capacity"] for c in carriages)

            if total_cap < group_size:
                continue

            if wheelchair_count > 0:
                assigned = wc.WC.wheelchair(wheelchair_count, group_size, adults, toddlers, [train], st, group_id)
                if assigned:
                    schedule[train_index] = train
                    return True, schedule
                continue

            remaining = group_size
            per = toddlers // len(carriages)
            extra = toddlers % len(carriages)
            for i, c in enumerate(carriages):
                assign = min(remaining, c["capacity"])
                tod = per + (1 if i < extra else 0)
                c.update({"occupied": True, "group_size": assign, "toddlers": tod, "wheelchair": wheelchair_count > 0, "group_id": group_id})
                remaining -= assign
                for orig_c in train["carriages"]:
                    if orig_c["number"] == c["number"]:
                        orig_c.update(c)
            schedule[train_index] = train
            return True, schedule

        # --- Wheelchair logic first if unrestricted ---
        if wheelchair_count > 0:
            assigned = wc.WC.wheelchair(wheelchair_count, group_size, adults, toddlers, [train], st, group_id)
            if assigned:
                schedule[train_index] = train
                return True, schedule
            continue

        # --- Standard group handling using new classes ---
        handler_class = (
            SmallGroupHandler if group_size <= 2 else
            MediumGroupHandler if 3 <= group_size <= 4 else
            LargeGroupHandler
        )
        handler = handler_class(
            group={"size": group_size, "toddlers": toddlers},
            adults=adults,
            carriages=train["carriages"],
            train=train,
            st_module=st,
            group_id=group_id,
            confirmation_callback=small_group_confirmation
        )

        assigned = handler.assign()
        if assigned:
            schedule[train_index] = train
            return True, schedule

    return False, schedule

def display_assignment_success(schedule, group_id):
    for train in schedule:
        carriages = [c for c in train["carriages"] if c["group_id"] == group_id]
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

def group_can_fit_on_train(train, group_size, adults, toddlers, wheelchair_count):
    carriages = train["carriages"]
    available_capacity = sum(c["capacity"] for c in carriages if not c["occupied"])

    if wheelchair_count > 0:
        return wc.WC.can_fit_wheelchair(train, group_size, adults, toddlers, wheelchair_count)

    if group_size in [3, 4] and adults >= 2:
        c4 = next((c for c in carriages if c["number"] == "4" and not c["occupied"]), None)
        c5 = next((c for c in carriages if c["number"] == "5" and not c["occupied"]), None)
        c1 = next((c for c in carriages if c["number"] == "1" and not c["occupied"]), None)
        c8 = next((c for c in carriages if c["number"] == "8" and not c["occupied"]), None)
        if c4 and c5:
            return True
        elif c1 and c8:
            return True

    if group_size <= available_capacity:
        return True

    return False

def small_group_confirmation(train, group_size, carriage):
    key = f"small_group_confirm_{train['departure_time']}_{carriage['number']}_{group_size}"
    if key not in st.session_state:
        st.session_state[key] = None

    if st.session_state[key] is None:
        st.warning(
            f"Train at {train['departure_time']} has no free 2-seat carriages.\n"
            f"Assign your group of {group_size} to larger carriage {carriage['number']} "
            f"(capacity {carriage['capacity']}) now, or wait for the next train?"
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Assign now", key=key + "_yes"):
                st.session_state[key] = True
                st.rerun()
        with col2:
            if st.button("❌ Wait for next train", key=key + "_no"):
                st.session_state[key] = False
                st.rerun()

    return st.session_state[key]  # True/False or None if undecided

def assign_to_2cap_only(schedule, adults, toddlers, wheelchair_count, group_size, group_id):
    if adults < 1:
        return False, schedule

    for train_index, train in enumerate(schedule):
        if train["cancelled"] or train["party_train"] or train["school_name"] != "":
            continue
        if minutes_until_departure(train["departure_time"]) < 0:
            continue

        # Only consider small carriages: 1, 4, 5, 8 that are not occupied
        carriages = [c for c in train["carriages"] if c["number"] in ["1", "4", "5", "8"] and not c["occupied"]]
        total_cap = sum(c["capacity"] for c in carriages)
        if total_cap < group_size:
            continue

        # Assign group to the minimum number of required carriages
        remaining = group_size
        used_carriages = []
        for c in carriages:
            if remaining <= 0:
                break
            assign = min(remaining, c["capacity"])
            used_carriages.append((c, assign))
            remaining -= assign

        if remaining > 0:
            continue  # Not enough capacity in eligible carriages

        # Distribute toddlers among used carriages
        num_used = len(used_carriages)
        per = toddlers // num_used if num_used > 0 else 0
        extra = toddlers % num_used

        for i, (c, assign) in enumerate(used_carriages):
            tod = per + (1 if i < extra else 0)
            c.update({
                "occupied": True,
                "group_size": assign,
                "toddlers": tod,
                "wheelchair": wheelchair_count > 0,
                "group_id": group_id
            })

            # Update original carriage in train
            for orig_c in train["carriages"]:
                if orig_c["number"] == c["number"]:
                    orig_c.update(c)

        schedule[train_index] = train
        return True, schedule

    return False, schedule

def booking_page():
    if "confirm_c45" not in st.session_state:
        st.session_state.confirm_c45 = {}
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "allow_2p_in_4cap_by_group" not in st.session_state:
        st.session_state.allow_2p_in_4cap_by_group = {}

    def display_feedback():
        if st.session_state.feedback:
            if st.session_state.feedback["type"] == "success":
                updated, gid = st.session_state.feedback["data"]
                display_assignment_success(updated, gid)
            elif st.session_state.feedback["type"] == "error":
                st.error(st.session_state.feedback["data"])
            st.session_state.feedback = None
    
    if "reset_form" not in st.session_state:
        st.session_state.reset_form = False

    if st.session_state.reset_form:
        st.session_state.adults = 0
        st.session_state.children = 0
        st.session_state.toddlers = 0
        st.session_state.wheelchair = False
        st.session_state.reset_form = False
        st.rerun()

    schedule = load_schedule()
    st.header("🎟️ Automatic Group Assignment")

    # Inputs
    adults = st.number_input("Number of Adults", min_value=0, key="adults")
    children = st.number_input("Number of Children", min_value=0, key="children")
    toddlers = st.number_input("Number of Lap-sitting Toddlers", min_value=0, max_value=st.session_state.adults, key="toddlers")
    wheelchair = st.checkbox("A wheelchair user is in this group", key="wheelchair")

    group_size = adults + children
    if wheelchair:
        wheelchair_count = 1
    else:
        wheelchair_count = 0

    group_ids = [c["group_id"] for t in schedule for c in t["carriages"] if c["group_id"]]
    group_id = max(group_ids, default=0) + 1

    soon_train, soon_minutes = find_soon_departing_train(schedule)

    # --- Check for 2-person group fallback to 4-cap carriage ---
    if group_size <= 2 and adults >= 1 and not wheelchair:
        already_decided = st.session_state.allow_2p_in_4cap_by_group.get(group_id, None)

        if already_decided is None:
            for train in schedule:
                if train["cancelled"] or train["party_train"] or train["school_name"] != "":
                    continue
                if minutes_until_departure(train["departure_time"]) < 0:
                    continue

                available = [c for c in train["carriages"] if not c["occupied"]]
                two_caps = [c for c in available if c["capacity"] == 2]
                four_caps = [c for c in available if c["capacity"] == 4]

                if not two_caps and four_caps:
                    st.warning(
                        f"🚩 Group of {group_size} can be seated in a 4-person carriage "
                        f"on the {train['departure_time']} train (leaves in {minutes_until_departure(train['departure_time'])} mins). Continue?"

                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, assign on this train"):
                            assigned, updated = assign_group(
                            schedule, adults, toddlers, wheelchair_count, group_size, group_id,
                            confirmed=True)
                            if assigned:
                                save_schedule(updated)
                                st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
                                st.session_state.reset_form = True
                            else:
                                st.session_state.feedback = {"type": "error", "data": "❌ Could not assign group to this train."}
                            st.rerun()
                    with col2:
                        if st.button("❌ No, assign to 2-person carriage"):
                            st.session_state.allow_2p_in_4cap_by_group[group_id] = False
                            assigned, updated = assign_to_2cap_only(
                                schedule, adults, toddlers, wheelchair_count, group_size, group_id
                            )
                            if assigned:
                                save_schedule(updated)
                                st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
                                st.session_state.reset_form = True
                            else:
                                st.session_state.feedback = {"type": "error", "data": "❌ Could not assign group to this train."}
                            st.rerun()
                    st.markdown("---")
                    display_feedback()
                    return

    # --- Step 2: Handle special 4/5 carriage confirmation ---
    special_train_idx = None
    special_carriages = None

    for idx, train in enumerate(schedule):
        if train["cancelled"] or train["party_train"] or train["school_name"] != "":
            continue
        if minutes_until_departure(train["departure_time"]) < 0:
            continue
        carriages = train["carriages"]
        if (group_size == 3 or group_size == 4) and adults >= 2:
            if only_c4_c5_available(carriages, group_size):
                special_train_idx = idx
                special_carriages = ["4", "5"]
                break
            elif only_c1_c8_available(carriages, group_size):
                special_train_idx = idx
                special_carriages = ["1", "8"]
                break

    if special_train_idx is not None:
        train = schedule[special_train_idx]
        key = f"group_{group_id}_{''.join(special_carriages)}"
        if not st.session_state.confirm_c45.get(key, False):
            st.warning(
                f"🚩 Only space for your group is on carriages {', '.join(special_carriages)} on train at {train['departure_time']} "
                f"which leaves in {minutes_until_departure(train['departure_time'])} minutes"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Yes, assign to carriages {', '.join(special_carriages)}"):
                    st.session_state.confirm_c45[key] = True
                    st.rerun()
            with col2:
                if st.button("❌ No, assign to next available train"):
                    st.session_state.confirm_c45[key] = True
                    assigned, updated = assign_group(
                        schedule, adults, toddlers, wheelchair_count, group_size, group_id,
                        confirmed=False
                    )
                    if assigned:
                        save_schedule(updated)
                        st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
                        st.session_state.reset_form = True
                    else:
                        st.session_state.feedback = {"type": "error", "data": "❌ No space on any upcoming train."}
                    st.rerun()
            st.markdown("---")
            display_feedback()
            return

        assigned, updated = assign_group(
            schedule, adults, toddlers, wheelchair_count, group_size, group_id,
            confirmed=True, restricted_carriages=special_carriages
        )
        if assigned:
            save_schedule(updated)
            st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
            st.session_state.reset_form = True
        else:
            st.session_state.feedback = {"type": "error", "data": "❌ Could not assign group to this train."}
        st.rerun()

    # --- Step 3: Handle soon-departing train ---
    def can_accommodate_wheelchair(train, wheelchair_count):
        # Check if there are enough free spaces in carriage 2(s) for the wheelchair users
        carriage_2_list = [c for c in train["carriages"] if c["number"] == "2" and not c.get("occupied", False)]
        return len(carriage_2_list) >= wheelchair_count

    if soon_train and group_can_fit_on_train(soon_train, group_size, adults, toddlers, wheelchair_count):
        # Skip warning if wheelchair users exist but no room for them on carriage 2(s)
        if wheelchair_count == 0 or (wheelchair_count > 0 and can_accommodate_wheelchair(soon_train, wheelchair_count)):
            st.warning(f"⚠️ Train at {soon_train['departure_time']} leaves in {soon_minutes} minutes.")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Assign to this train"):
                    assigned, updated = assign_group(
                        schedule, adults, toddlers, wheelchair_count, group_size, group_id,
                        confirmed=True
                    )
                    if assigned:
                        save_schedule(updated)
                        st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
                        st.session_state.reset_form = True
                    else:
                        st.session_state.feedback = {"type": "error", "data": "❌ Could not assign group to this train."}
                    st.rerun()
            with col2:
                if st.button("Assign to next available train"):
                    assigned, updated = assign_group(
                        schedule, adults, toddlers, wheelchair_count, group_size, group_id,
                        confirmed=False
                    )
                    if assigned:
                        save_schedule(updated)
                        st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
                        st.session_state.reset_form = True
                    else:
                        st.session_state.feedback = {"type": "error", "data": "❌ No space on any upcoming train."}
                    st.rerun()
            st.markdown("---")
            display_feedback()
            return


    # --- Step 4: Default assign button ---
    if st.button("Assign Group") and group_size != 0:
        assigned, updated = assign_group(
            schedule, adults, toddlers, wheelchair_count, group_size, group_id,
            confirmed=False
        )
        if assigned:
            save_schedule(updated)
            st.session_state.feedback = {"type": "success", "data": (updated, group_id)}
            st.session_state.reset_form = True
        else:
            st.session_state.feedback = {"type": "error", "data": "❌ No space on any upcoming train."}
        st.rerun()

    st.markdown("---")
    display_feedback()

booking_page()
