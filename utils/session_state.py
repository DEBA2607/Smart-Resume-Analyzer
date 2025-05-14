import streamlit as st


def reset_session_state():
    """Reset session state variables when a new PDF is uploaded"""
    # Clear all data extraction results
    if 'skills' in st.session_state:
        del st.session_state.skills
    if 'resume_data' in st.session_state:
        del st.session_state.resume_data
    if 'resume_text' in st.session_state:
        del st.session_state.resume_text
    # if 'predicted_category' in st.session_state:
    #     del st.session_state.predicted_category
    if 'recommended_job' in st.session_state:
        del st.session_state.recommended_job
    if 'recommended_skills' in st.session_state:
        del st.session_state.recommended_skills
    if 'rec_course' in st.session_state:
        del st.session_state.rec_course
    if 'summary_response' in st.session_state:
        del st.session_state.summary_response
    
    # Clear all job search related variables
    if 'job_results' in st.session_state:
        del st.session_state.job_results
    if 'job_search_initiated' in st.session_state:
        del st.session_state.job_search_initiated
    if 'location_data' in st.session_state:
        del st.session_state.location_data
    if 'country_selected' in st.session_state:
        del st.session_state.country_selected
    
    # Set state to initial
    st.session_state.app_state = 'initial'