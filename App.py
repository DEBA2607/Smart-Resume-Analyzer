import streamlit as st
from views.user_view import render_user_view
from views.admin_view import render_admin_view

def run():
    # Set page configuration once at the start
    st.set_page_config(page_title="Smart Resume Analyzer", layout="wide")

    # App state tracking for performance optimization
    if 'app_state' not in st.session_state:
        st.session_state.app_state = 'initial'

    st.title("Smart Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

    if choice == 'User':
        render_user_view()
    else:
        render_admin_view()

if __name__ == "__main__":
    run()