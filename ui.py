# ui.py
import streamlit as st
import time
import uuid

from knowledge import save_uploaded_file, build_pdf_index
from agent import get_agent_response
from storage import init_db, save_message, load_history, delete_history, get_recent_session_titles

st.set_page_config(page_title="Claude PDF Chat", layout="wide")
st.title("📄 Claude PDF Chatbot")

# Initialize DB
init_db()

# Setup session and state
if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
if 'history_page' not in st.session_state:
    st.session_state['history_page'] = 0
if 'global_history_page' not in st.session_state:
    st.session_state['global_history_page'] = 0

view_session_id = st.session_state.get("view_session_id")
active_session_id = view_session_id or st.session_state['session_id']

# Sidebar: New Chat button at the top
if st.sidebar.button("🆕 New Chat", use_container_width=True):
    st.session_state['session_id'] = str(uuid.uuid4())
    st.session_state.pop("view_session_id", None)
    st.session_state.pop("index", None)
    st.rerun()
 
# Always rebuild index if viewing a session (on first visit only)
if view_session_id and 'index' not in st.session_state:
    try:
        index = build_pdf_index(view_session_id)
        st.session_state['index'] = index
    except Exception as e:
        st.error(f"Error loading previous session PDFs: {str(e)}")

# Show previous chat history
if view_session_id:
    st.markdown("### 📜 Session History")
    history = load_history(view_session_id)
    for role, msg in history:
        if role == "user":
            st.markdown(f"**🧑 User:** {msg}")
        elif role == "assistant":
            st.markdown(f"**🤖 Claude:** {msg}")
    st.markdown("---")

# Upload Section (Main area, only for new chats)
if not view_session_id:
    st.markdown("### 📥 Upload PDFs")
    uploaded_files = st.file_uploader("Choose PDFs", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        status_placeholder = st.empty()
        status_placeholder.info("Processing uploaded files...")
        saved_files = []

        for file in uploaded_files:
            try:
                file_path = save_uploaded_file(file, active_session_id)
                saved_files.append(file_path)
                st.success(f"✅ Saved: {file.name}")
            except Exception as e:
                st.error(f"❌ Error saving {file.name}: {str(e)}")

        if saved_files:
            try:
                time.sleep(1)
                index = build_pdf_index(active_session_id)
                st.session_state['index'] = index
                st.success("✅ PDF index built successfully")
                status_placeholder.empty()
            except Exception as e:
                st.error(f"❌ Error building index: {str(e)}")
    else:
        st.info("📄 Upload one or more PDF files to get started.")


# Chat Interface
st.subheader("🧠 Ask a question")

with st.form(key="question_form", clear_on_submit=True):
    user_input = st.text_input("Your question")
    submit_clicked = st.form_submit_button("💬 Submit")

if submit_clicked:
    if not user_input.strip():
        st.warning("⚠️ Please enter a question before submitting.")
    else:
        index = st.session_state.get('index')

        # Check: no index AND this is not a loaded/viewed session
        if not index and not view_session_id:
            st.warning("⚠️ Please upload a PDF before asking a question.")
        elif not index:
            st.error("No PDF index loaded. Please upload or load a session.")
        else:
            try:
                with st.spinner("Generating response..."):
                    response = get_agent_response(user_input, index)
                    st.markdown(f"**Claude:** {response}")

                    history = load_history(active_session_id)
                    is_first = len(history) == 0
                    save_message(active_session_id, "user", user_input, title=user_input if is_first else None)
                    save_message(active_session_id, "assistant", response)
            except Exception as e:
                st.error(f"Error generating response: {str(e)}")


   
# Sidebar: Recent Chat Sessions
st.sidebar.subheader("🕓 Recent Chat Sessions")
title_page_size = 10
title_page = st.session_state.get("global_history_page", 0)
title_offset = title_page * title_page_size

recent_titles = get_recent_session_titles(limit=title_page_size, offset=title_offset)

if recent_titles:
    for sid, title in recent_titles:
        if st.sidebar.button(f"📄 {title or 'Untitled'}", key=f"title_btn_{sid}", use_container_width=True):
            st.session_state["view_session_id"] = sid
            st.session_state.pop("index", None)
            st.rerun()
else:
    st.sidebar.info("No recent sessions found.")

# Pagination
prev_col, next_col = st.sidebar.columns(2)

with prev_col:
    if st.button("⬅️ Prev", disabled=title_offset == 0, use_container_width=True):
        st.session_state["global_history_page"] = max(0, title_page - 1)
        st.rerun()

with next_col:
    if st.button("➡️ Next", disabled=len(recent_titles) < title_page_size, use_container_width=True):
        st.session_state["global_history_page"] += 1
        st.rerun()



# Clear history of selected/viewed session only with confirmation
if view_session_id:
    if st.sidebar.button("🗑️ Delete This Chat"):
        st.session_state["confirm_delete"] = True

    if st.session_state.get("confirm_delete"):
        with st.sidebar.expander("⚠️ Confirm Deletion", expanded=True):
            st.warning("Are you sure you want to delete this chat?")
            confirm = st.button("✅ Yes, delete")
            cancel = st.button("❌ Cancel")

            if confirm:
                delete_history(view_session_id)
                st.session_state.pop("view_session_id", None)
                st.session_state.pop("index", None)
                st.session_state.pop("confirm_delete", None)
                st.rerun()

            if cancel:
                st.session_state.pop("confirm_delete", None)


