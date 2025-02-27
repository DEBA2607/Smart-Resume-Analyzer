import streamlit as st

def reset_session_state():
    """Reset session state variables."""
    keys_to_reset = ['skills', 'recommended_skills', 'courses', 'resume_data', 'resume_text', 'recommended_job',
                      'predicted_category']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]