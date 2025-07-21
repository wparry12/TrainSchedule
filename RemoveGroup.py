import streamlit as st
import os
import matplotlib
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

def remove_group_page():
    st.title("🗑️ Remove Groups by Clicking")

    schedule = load_schedule()
    if not schedule:
        return

    show_past = st.checkbox("Show previous trains", value=False)

    group_colour_map = create_group_colour_map(schedule)

    removed_msg = None
    now = datetime.now(LOCAL).time()

    for train_idx, train in enumerate(schedule):
        dep_str = train['departure_time']
        dep_dt = parse_time_local(dep_str)
        dep_time = dep_dt.time()

        # Format time to 12H with AM/PM, remove leading zero on hour
        dep_str_12h = dep_dt.strftime("%I:%M %p").lstrip("0")

        if not show_past and dep_time < now:
            continue  # Skip past trains unless checkbox is ticked

        is_cancelled = train.get('cancelled', False)
        is_party = train.get('party_train', False)

        status_label = "❌ CANCELLED" if is_cancelled else ("🎉 PARTY TRAIN" if is_party else "")
        st.subheader(f"⏰ {dep_str_12h} {status_label}")

        cols = st.columns(len(train['carriages']))
        for i, carriage in enumerate(train['carriages']):
            size = carriage.get('group_size', 0)
            gid = carriage.get('group_id') if 'group_id' in carriage else None
            toddlers = carriage.get('toddlers', 0)
            wheelchair = carriage.get('wheelchair', False)

            colour = group_colour_map.get(gid, '#eee') if size else '#eee'

            label = f"🚋 C{i+1}\n"
            label += f"👥 {size}" if size else "Empty"
            if gid is not None and size:
                label += f"\n🆔 {gid}"
                if toddlers:
                    label += f"\n👶 {toddlers}"
                if wheelchair:
                    label += f"\n♿️"

            btn_key = f"remove_train{train_idx}_carriage{i}"

            with cols[i]:
                if st.button(label, key=btn_key, help="Click to remove this group"):
                    if size > 0 and gid is not None:
                        # Remove all carriages with this group_id in entire schedule
                        for t in schedule:
                            for c in t['carriages']:
                                if c.get('group_id') == gid:
                                    c['group_size'] = 0
                                    c['occupied'] = False
                                    c['group_id'] = 0
                                    c['toddlers'] = 0
                                    c['wheelchair'] = False
                        save_schedule(schedule)
                        removed_msg = f"Removed group {gid} from entire schedule"
                        st.rerun()

    if removed_msg:
        st.success(removed_msg)

remove_group_page()