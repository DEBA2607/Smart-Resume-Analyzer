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

def extract_location_from_resume(resume_text):
    """Extract location information from resume text using Gemini AI"""
    from utils.gemini_utils import get_gemini_response1
    import json
    
    location_prompt = """
    You are an expert resume parser. Your task is to extract the candidate's current location information from the resume text.
    
    Instructions:
    1. Look for explicit mentions of current location, address, city, state, country or postal/zip code
    2. Focus on the most recent/current location if multiple locations are present
    3. Pay attention to headers like "Contact Information", "Personal Details", or address sections
    4. Return the location in a structured format as a JSON with these fields (include as many as you can find):
       {
         "city": "",
         "state": "",
         "country": "",
         "postal_code": "",
         "full_address": ""
       }
    5. If you can't find a specific field, leave it as an empty string
    6. If you can't find any location information at all, return {"location_found": false}
    7. Be specific - don't just say "United States" if you can identify the city and state
    8. IMPORTANT: Make sure you return only valid JSON, nothing else.
    
    Analyze the resume carefully and extract only factual location information, not assumptions.
    """
    
    try:
        response = get_gemini_response1(location_prompt, resume_text)
        
    
        
        # Try to clean the response if it's not valid JSON
        # Sometimes AI models add extra text before or after the JSON
        if response:
            # Try to find JSON-like content between braces
            import re
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                try:
                    # Parse and validate the JSON
                    location_data = json.loads(json_str)
                    return location_data
                except json.JSONDecodeError:
                    st.error("Could not parse location data as JSON")
                    # Return a default valid format
                    return {"location_found": False, "error": "Invalid JSON format"}
            else:
                st.error("No JSON-like content found in response")
                return {"location_found": False, "error": "No JSON content found"}
        else:
            st.error("Empty response from Gemini API")
            return {"location_found": False, "error": "Empty API response"}
            
    except Exception as e:
        st.error(f"Error extracting location: {str(e)}")
        return {"location_found": False, "error": str(e)}