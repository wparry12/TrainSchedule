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
from Information import information_page

def main():
    # Initialize counter in session state if not already present
    if "diggers_sold" not in st.session_state:
        st.session_state.diggers_sold = 0

    # Sidebar navigation and counter
    with st.sidebar:
        selected_page = option_menu(
            menu_title="Main Menu",
            options=[
                "Booking", "Overview", "Information","Manual Booking", "Remove Groups",
                "Remove Train Times", "Party Train", "School Train", "Schedule Presets"
            ],
            icons=["book", "list-task", "info-circle", "person", "trash", "x-circle", "gift", "building", "gear"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
        )

        st.markdown("### Diggers Sold:")

        cols = st.columns([1, 1, 1])
        with cols[0]:
            if st.button("➖"):
                if st.session_state.diggers_sold > 0:
                    st.session_state.diggers_sold -= 1
                    st.rerun()
        with cols[1]:
            st.markdown(f"<h3 style='text-align:center;'>{st.session_state.diggers_sold}</h3>", unsafe_allow_html=True)
        with cols[2]:
            if st.button("➕"):
                st.session_state.diggers_sold += 1
                st.rerun()

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
    elif selected_page == "Information":
        information_page()
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