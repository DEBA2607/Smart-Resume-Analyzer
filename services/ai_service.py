import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gemini_response1(input_prompt, text):
    """Get Gemini AI response for a single input"""
    from utils.expensive_libraries import load_expensive_libraries
    libs = load_expensive_libraries()
    genai = libs['genai']
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([input_prompt, text])
    return response.text

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gemini_response2(input_prompt, text, input):
    """Get Gemini AI response for multiple inputs"""
    from utils.expensive_libraries import load_expensive_libraries
    libs = load_expensive_libraries()
    genai = libs['genai']
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([input_prompt, text, input])
    return response.text