# utils/pdf_utils.py
import streamlit as st
import base64
import re
import json
from utils.gemini_utils import get_gemini_response1 # Correct relative import


@st.cache_data
def pdf_reader(file):
    """Extract text from PDF using PdfReader."""
    try:
        from PyPDF2 import PdfReader 
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except ImportError:
        st.error("PyPDF2 is not installed. Please install it.")
        return None


def show_pdf(file_path):
    """Display PDF in Streamlit."""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def extract_resume_data_with_gemini(pdf_path):
    """Extract resume data using Gemini API."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        max_pages = min(3, len(reader.pages))  # Limit to first 3 pages
        text = ""
        for i in range(max_pages):
            page = reader.pages[i]
            page_text = page.extract_text()
            if page_text is not None:
                text += page_text

        prompt5 = """
        You are a resume parsing assistant. Extract the following information from the resume text below:
        1. Name of the person
        2. Email address
        3. Phone/mobile number
        4. List of skills (technical, professional, etc.)

        VERY IMPORTANT: Return your answer ONLY as a valid JSON object with these exact keys:
        name, email, mobile_number, skills (as an array). Try to limit single skill to at most 3 words.
        Extract skills from at most 5 pages of the resume. Return at most 10 skills.
        Format your response as valid, parseable JSON with no other text before or after.
        Ensure all quotes are properly escaped.

        Example of expected response format:
        {"name": "John Doe", "email": "john@example.com", "mobile_number": "1234567890", "skills": ["Python", "Machine Learning"]}

        RESUME TEXT:
        """
        prompt5 += text

        response = get_gemini_response1(prompt5, text)  # Use the Gemini utility

        if response is not None:
            try:
                json_pattern = r'({.*})'
                json_match = re.search(json_pattern, response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                else:
                    data = json.loads(response)
                data["no_of_pages"] = len(reader.pages)
                return data
            except json.JSONDecodeError as e:
                with open("error.log", "a") as f:
                    f.write(f"Failed to parse JSON response: {str(e)}\n")
                    f.write(f"Response: {response}\n")

                # Fallback structured response based on regex patterns
                name_pattern = r'[nN]ame[\"\':\s]+([^\"\'}\n,]+)'
                email_pattern = r'[eE]mail[\"\':\s]+([^\s,]+)'
                phone_pattern = r'(?:[pP]hone|[mM]obile)[\"\':...\s]+([\d\s+-]+)'
                skills_pattern = r'[sS]kills[\"\':]\s*\[(.*?)\]'

                name_match = re.search(name_pattern, response)
                email_match = re.search(email_pattern, response)
                phone_match = re.search(phone_pattern, response)
                skills_match = re.search(skills_pattern, response, re.DOTALL)

                name = name_match.group(1).strip() if name_match and name_match.group(1) else ""
                email = email_match.group(1).strip() if email_match and email_match.group(1) else ""
                mobile_number = phone_match.group(1).strip() if phone_match and phone_match.group(1) else ""
                skills = []
                if skills_match:
                    skills_text = skills_match.group(1)
                    skills = [s.strip().strip('"\'') for s in re.findall(r'["\']([^"\']+)["\']', skills_text)]

                fallback_data = {
                    "name": name,
                    "email": email,
                    "mobile_number": mobile_number,
                    "skills": skills,
                    "no_of_pages": len(reader.pages)
                }
                return fallback_data

        else:
            with open("error.log", "a") as f:
                f.write("No response received from Gemini API.\n")
            return {
                "name": "",
                "email": "",
                "mobile_number": "",
                "skills": [],
                "no_of_pages": len(reader.pages)
            }

    except Exception as e:
        with open("error.log", "a") as f:
            f.write(f"Unexpected error in extract_resume_data_with_gemini: {str(e)}\n")
        return {
            "name": "",
            "email": "",
            "mobile_number": "",
            "skills": [],
            "no_of_pages": 0
        }
