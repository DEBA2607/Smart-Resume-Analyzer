import streamlit as st

@st.cache_resource
def load_expensive_libraries():
    """Load expensive libraries only when needed"""
    import google.generativeai as genai
    from PyPDF2 import PdfReader
    from pdfminer3.layout import LAParams
    from pdfminer3.pdfpage import PDFPage
    from pdfminer3.pdfinterp import PDFResourceManager
    from pdfminer3.pdfinterp import PDFPageInterpreter
    from pdfminer3.converter import TextConverter
    
    # Configure Gemini API
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