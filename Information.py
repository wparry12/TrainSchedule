import streamlit as st
from datetime import date

def information_page():
    st.title("🗓️ Information & Planning Page")

    # Default questions
    questions = {
        "in_charge": "In charge:",
        "first_aider": "First Aider:",
        "diggers_1_2": "Diggers 1pm-2pm:",
        "train_lunch": "What time is the train driver having lunch and who is covering:",
        "clean_toilet": "Clean top toilet before 11:00am:",
        "quads_gokarts": "Quads & gokarts before 11:00am:",
        "leaf_blow": "Leaf blow Molly the Cow concrete, Panning for gold, train station etc.:",
        "general_rubbish": "General rubbish walk:",
        "party_trains": "Times of party trains today:",
        "school_trains": "Schools and the time of their trains today:",
    }

    # Initialize user-added questions in session state if not already
    if "user_questions" not in st.session_state:
        st.session_state["user_questions"] = {}  # key: question_id, value: question text

    today_key = date.today().isoformat()

    # Ensure today's notes exist in session state, including user questions
    if f"notes_{today_key}" not in st.session_state:
        combined_keys = list(questions.keys()) + list(st.session_state["user_questions"].keys())
        st.session_state[f"notes_{today_key}"] = {k: "" for k in combined_keys}

    # --- Show today's notes at the top (read-only, question and answer on separate lines) ---
    with st.expander(f"📅 Today's Notes ({today_key})", expanded=True):
        today_notes = st.session_state[f"notes_{today_key}"]
        has_any = False

        # Show default questions
        for key, question in questions.items():
            val = today_notes.get(key, "").strip()
            if val:
                has_any = True
                st.markdown(f"**{question}**")
                st.markdown(val)
                st.markdown("")

        # Show user-added questions
        for key, question_text in st.session_state["user_questions"].items():
            val = today_notes.get(key, "").strip()
            if val:
                has_any = True
                st.markdown(f"**{question_text}**")
                st.markdown(val)
                st.markdown("")

        if not has_any:
            st.info("No notes saved for today yet.")

    st.markdown("---")

    # --- Section to add/edit notes for a chosen date ---
    st.header("📅 Plan for Another Date")

    selected_date = st.date_input("Select a date to plan for", value=date.today())
    date_key = selected_date.isoformat()

    if f"notes_{date_key}" not in st.session_state:
        combined_keys = list(questions.keys()) + list(st.session_state["user_questions"].keys())
        st.session_state[f"notes_{date_key}"] = {k: "" for k in combined_keys}

    notes_for_date = st.session_state[f"notes_{date_key}"]

    # Show default questions with inputs
    for key, question in questions.items():
        notes_for_date[key] = st.text_input(question, value=notes_for_date.get(key, ""), key=f"{date_key}_{key}")

    # Show user-added questions with inputs
    for key, question_text in st.session_state["user_questions"].items():
        notes_for_date[key] = st.text_input(question_text, value=notes_for_date.get(key, ""), key=f"{date_key}_{key}")

    if st.button(f"💾 Save Notes for {date_key}"):
        st.session_state[f"notes_{date_key}"] = notes_for_date
        st.success(f"Notes saved for {date_key}!")

    st.markdown("---")
    st.subheader("➕ Add a New Custom Question")

    new_question_text = st.text_input("Enter your new question here:")

    if st.button("Add Question"):
        if not new_question_text.strip():
            st.error("Please enter a non-empty question.")
        else:
            new_key = f"user_q_{len(st.session_state['user_questions']) + 1}"
            st.session_state["user_questions"][new_key] = new_question_text.strip()
            st.success(f"Added new question: {new_question_text}")

            # Initialize empty notes for all existing dates for this new question
            for key in st.session_state.keys():
                if key.startswith("notes_") and new_key not in st.session_state[key]:
                    st.session_state[key][new_key] = ""

            st.rerun()

    st.markdown("---")
    st.subheader("➖ Remove a Custom Question")

    user_qs = st.session_state["user_questions"]
    if user_qs:
        question_to_remove = st.selectbox("Select a question to remove:", options=list(user_qs.keys()), format_func=lambda k: user_qs[k])
        if st.button("Remove Selected Question"):
            # Remove question from user_questions
            removed_text = user_qs.pop(question_to_remove)
            # Remove question data from all notes
            for key in st.session_state.keys():
                if key.startswith("notes_") and question_to_remove in st.session_state[key]:
                    del st.session_state[key][question_to_remove]

            st.success(f"Removed question: {removed_text}")
            st.rerun()
    else:
        st.info("No custom questions to remove.")

if __name__ == "__main__":
    information_page()
