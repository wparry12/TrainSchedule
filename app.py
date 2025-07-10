import streamlit as st
from streamlit_option_menu import option_menu
from Booking import booking_page
from Overview import booking_overview_page
from Cancel import train_cancel_page
from RemoveGroup import remove_group_page
from Manual import manual_group_assignment_page
from Party import party_train_page
from Presets import preset_schedule_page
from School import school_train_page

def main():
    # Sidebar navigation
    with st.sidebar:
        selected_page = option_menu(
            menu_title="Main Menu",
            options=[
                "Booking", "Overview", "Manual Booking", "Remove Groups",
                "Remove Train Times", "Party Train", "School Train", "Schedule Presets"
            ],
            icons=["book", "list-task", "person", "trash", "x-circle", "gift", "building", "gear"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
        )

    # Refresh logic
    if "last_page" not in st.session_state:
        st.session_state.last_page = selected_page
    elif st.session_state.last_page != selected_page:
        st.session_state.last_page = selected_page
        st.rerun()

    # Route to the correct page
    if selected_page == "Booking":
        booking_page()
    elif selected_page == "Overview":
        booking_overview_page()
    elif selected_page == "Remove Train Times":
        train_cancel_page()
    elif selected_page == "Remove Groups":
        remove_group_page()
    elif selected_page == "Manual Booking":
        manual_group_assignment_page()
    elif selected_page == "Party Train":
        party_train_page()
    elif selected_page == "Schedule Presets":
        preset_schedule_page()
    elif selected_page == "School Train":
        school_train_page()

if __name__ == "__main__":
    main()

#  c2,c6,c7 full and group of 8 then c3/4/5 will be chosen, is this good?
# swap to sqlite from JSON