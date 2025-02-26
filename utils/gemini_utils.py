# utils/gemini_utils.py
import streamlit as st

@st.cache_resource
def load_expensive_libraries():
    """Load expensive libraries only when needed."""
    import google.generativeai as genai
    from PyPDF2 import PdfReader
    from pdfminer3.layout import LAParams
    from pdfminer3.pdfpage import PDFPage
    from pdfminer3.pdfinterp import PDFResourceManager
    from pdfminer3.pdfinterp import PDFPageInterpreter
    from pdfminer3.converter import TextConverter

    genai.configure(api_key=st.secrets["API_KEY"])
    return {
        'genai': genai,
        'PdfReader': PdfReader,
        'LAParams': LAParams,
        'PDFPage': PDFPage,
        'PDFResourceManager': PDFResourceManager,
        'PDFPageInterpreter': PDFPageInterpreter,
        'TextConverter': TextConverter
    }

@st.cache_data(ttl=3600)
def get_gemini_response1(input_prompt, text):
    """Get Gemini API response."""
    libs = load_expensive_libraries()
    genai = libs['genai']
    model = genai.GenerativeModel('gemini-2.0-flash')
    try:
        response = model.generate_content([input_prompt, text])
        return response.text
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None

@st.cache_data(ttl=3600)
def get_gemini_response2(input_prompt, text, input):
    """Get Gemini API response with additional input."""
    libs = load_expensive_libraries()
    genai = libs['genai']
    model = genai.GenerativeModel('gemini-2.0-flash')
    try:
        response = model.generate_content([input_prompt, text, input])
        return response.text
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return None
