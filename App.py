import streamlit as st
import re
import pickle
import pandas as pd
import base64
import time, datetime
import json
from streamlit_tags import st_tags
import pymysql
import random

# Import expensive libraries only when needed
from PIL import Image  # Much lighter than matplotlib for basic image display

# Lazy imports to speed up initial load time
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

# Load models with proper caching
@st.cache_resource
def load_ml_models():
    """Load ML models with proper caching"""
    rf_classifier_categorization = pickle.load(open('models/rf_classifier_categorization.pkl', 'rb'))
    tfidf_vectorizer_categorization = pickle.load(open('models/tfidf_vectorizer_categorization.pkl', 'rb'))
    rf_classifier_job_recommendation = pickle.load(open('models/rf_classifier_job_recommendation.pkl', 'rb'))
    tfidf_vectorizer_job_recommendation = pickle.load(open('models/tfidf_vectorizer_job_recommendation.pkl', 'rb'))
    
    return {
        'rf_classifier_categorization': rf_classifier_categorization,
        'tfidf_vectorizer_categorization': tfidf_vectorizer_categorization,
        'rf_classifier_job_recommendation': rf_classifier_job_recommendation,
        'tfidf_vectorizer_job_recommendation': tfidf_vectorizer_job_recommendation
    }

# Database connection with proper pooling
@st.cache_resource
def get_database_connection():
    """Get database connection with connection pooling"""
    connection = pymysql.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"],
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Cache Gemini API responses
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gemini_response1(input_prompt, text):
    libs = load_expensive_libraries()
    genai = libs['genai']
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([input_prompt, text])
    return response.text

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_gemini_response2(input_prompt, text, input):
    libs = load_expensive_libraries()
    genai = libs['genai']
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([input_prompt, text, input])
    return response.text

# Clean resume
def cleanResume(txt):
    cleanText = re.sub(r'http\S+\s', ' ', txt)
    cleanText = re.sub(r'RT|cc', ' ', cleanText)
    cleanText = re.sub(r'#\S+\s', ' ', cleanText)
    cleanText = re.sub(r'@\S+', '  ', cleanText)
    cleanText = re.sub(r'[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
    cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText)
    cleanText = re.sub(r'\s+', ' ', cleanText)
    return cleanText

# Prediction and Category Name - with model loading optimization
@st.cache_data
def predict_category(resume_text):
    models = load_ml_models()
    resume_text = cleanResume(resume_text)
    resume_tfidf = models['tfidf_vectorizer_categorization'].transform([resume_text])
    predicted_category = models['rf_classifier_categorization'].predict(resume_tfidf)[0]
    return predicted_category

@st.cache_data
def job_recommendation(resume_text):
    models = load_ml_models()
    resume_text = cleanResume(resume_text)
    resume_tfidf = models['tfidf_vectorizer_job_recommendation'].transform([resume_text])
    recommended_job = models['rf_classifier_job_recommendation'].predict(resume_tfidf)[0]
    return recommended_job

# Optimize PDF processing to use only one library
@st.cache_data
def pdf_reader(file):
    """Extract text from PDF using a single library"""
    libs = load_expensive_libraries()
    PdfReader = libs['PdfReader']
    
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# More efficient PDF display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # Use a smaller iframe height to reduce initial rendering load
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="500" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def extract_resume_data_with_gemini(pdf_path):
    try:
        libs = load_expensive_libraries()
        PdfReader = libs['PdfReader']
        
        # Read PDF
        reader = PdfReader(pdf_path)
        max_pages = min(3, len(reader.pages))  # Limit to first 5 pages for performance
        text = ""
        for i in range(max_pages):
            page = reader.pages[i]
            page_text = page.extract_text()
            if page_text is not None:
                text += page_text
        
        # Modified prompt to explicitly request valid JSON format
        prompt5 = """
        You are a resume parsing assistant. Extract the following information from the resume text below:
        1. Name of the person
        2. Email address
        3. Phone/mobile number
        4. List of skills (technical, professional, etc.)
        
        VERY IMPORTANT: Return your answer ONLY as a valid JSON object with these exact keys: name, email, mobile_number, skills (as an array). Try to limit single skill to at most 3 words. Extract skills from at most 5 pages of the resume. Return at most 10 skills.
        Format your response as valid, parseable JSON with no other text before or after. Ensure all quotes are properly escaped.
        Example of expected response format:
        {"name": "John Doe", "email": "john@example.com", "mobile_number": "1234567890", "skills": ["Python", "Machine Learning"]}
        
        RESUME TEXT:
        """
        
        # Ensure text is a string
        if text is None:
            text = "No text extracted."
            
        prompt5 += text
        
        # Call your existing Gemini function with error handling
        try:
            response = get_gemini_response1(prompt5, text)
        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}", file=open("error.log", "a"))
            response = None
        
        # Process response
        if response is not None:
            try:
                # Attempt to extract just the JSON part if there's additional text
                json_pattern = r'({.*})'
                json_match = re.search(json_pattern, response, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(1)
                    data = json.loads(json_str)
                else:
                    data = json.loads(response)
                    
                # Add page count
                data["no_of_pages"] = len(reader.pages)
                return data
                
            except json.JSONDecodeError as e:
                # Log the error and response for debugging
                with open("error.log", "a") as f:
                    f.write(f"Failed to parse JSON response: {str(e)}\n")
                    f.write(f"Response: {response}\n")
                
                # Create a fallback structured response based on regex patterns
                name_pattern = r'[nN]ame[\"\':\s]+([^\"\'}\n,]+)'
                email_pattern = r'[eE]mail[\"\':\s]+([^\s,]+)'
                phone_pattern = r'(?:[pP]hone|[mM]obile)[\"\':_\s]+([\d\s+-]+)'
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
                
                # Fallback data
                fallback_data = {
                    "name": name,
                    "email": email, 
                    "mobile_number": mobile_number,
                    "skills": skills,
                    "no_of_pages": len(reader.pages)
                }
                
                return fallback_data
        
        # Handle None response
        with open("error.log", "a") as f:
            f.write("No response received from Gemini API.\n")
        
        # Fallback data when no response is received
        fallback_data = {
            "name": "",
            "email": "", 
            "mobile_number": "",
            "skills": [],
            "no_of_pages": len(reader.pages)
        }
        
        return fallback_data
        
    except Exception as e:
        # Catch any other exceptions
        with open("error.log", "a") as f:
            f.write(f"Unexpected error in extract_resume_data_with_gemini: {str(e)}\n")
        
        # Return empty data on error
        return {
            "name": "",
            "email": "", 
            "mobile_number": "",
            "skills": [],
            "no_of_pages": 0
        }


def reset_session_state():
    """Reset all relevant session state variables when a new PDF is uploaded"""
    keys_to_reset = ['skills', 'recommended_skills', 'courses', 'resume_data', 'resume_text', 'recommended_job', 'predicted_category'] # Add all PDF-dependent keys here
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

# Load course and skill data more efficiently
@st.cache_resource
def load_recommendation_data():
    """Load recommendation data"""
    from Recommendor.Skills import ds_keyword, ds_skills, web_keyword, web_skills, android_keyword, android_skills, ios_keyword, ios_skills, uiux_keyword, uiux_skills
    from Recommendor.Courses import ds_course, web_course, android_course, ios_course, uiux_course
    
    return {
        'ds_keyword': ds_keyword,
        'ds_skills': ds_skills,
        'web_keyword': web_keyword,
        'web_skills': web_skills,
        'android_keyword': android_keyword,
        'android_skills': android_skills,
        'ios_keyword': ios_keyword,
        'ios_skills': ios_skills,
        'uiux_keyword': uiux_keyword,
        'uiux_skills': uiux_skills,
        'ds_course': ds_course,
        'web_course': web_course,
        'android_course': android_course,
        'ios_course': ios_course,
        'uiux_course': uiux_course
    }

def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations**")
    c = 0
    rec_course = []
    no_of_reco = st.slider('Choose Number of Course Recommendations:', 1, 10, 4)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course

def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def insert_data(type, email, timestamp, no_of_pages, cand_level, skills, recommended_skills, courses):
    connection = get_database_connection()
    cursor = connection.cursor()
    
    # Create the DB if it doesn't exist
    db_sql = """CREATE DATABASE IF NOT EXISTS sql12764371;"""
    cursor.execute(db_sql)
    connection.select_db("sql12764371")
    
    # Create table if it doesn't exist
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """(ID INT NOT NULL AUTO_INCREMENT,Type varchar(100),Email_ID VARCHAR(50),Timestamp VARCHAR(50) NOT NULL,Page_no VARCHAR(5) NOT NULL,User_level VARCHAR(30) NOT NULL,Actual_skills VARCHAR(300) NOT NULL,Recommended_skills VARCHAR(300) NOT NULL,Recommended_courses VARCHAR(600) NOT NULL,PRIMARY KEY (ID),UNIQUE(Email_ID));"""
    cursor.execute(table_sql)
    
    # Insert data
    insert_sql = f"INSERT IGNORE INTO {DB_table_name} VALUES (0,%s,%s,%s,%s,%s,%s,%s,%s)"
    rec_values = (type, email, timestamp, str(no_of_pages), cand_level, skills, recommended_skills, courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()
    cursor.close()

def run():
    # Set page configuration once at the start
    st.set_page_config(
        page_title="Smart Resume Analyzer",
        layout="wide"  # This gives more space and can help with rendering
    )
    
    # App state tracking for performance optimization
    if 'app_state' not in st.session_state:
        st.session_state.app_state = 'initial'
    
    st.title("Smart Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)
    
    if choice == 'User':
        # User section
        if 'current_pdf' not in st.session_state:
            st.session_state.current_pdf = None
        
        # Use a container for the file uploader to improve re-rendering performance
        with st.container():
            pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
            
            if pdf_file is not None:
                if st.session_state.current_pdf != pdf_file.name:
                    # Reset session state for a new PDF
                    reset_session_state()
                    st.session_state.current_pdf = pdf_file.name
                    st.session_state.app_state = 'pdf_uploaded'
                
                save_image_path = './Uploaded_Resumes/' + pdf_file.name
                with open(save_image_path, "wb") as f:
                    f.write(pdf_file.getbuffer())
                
                # Show PDF with progress indicator
                with st.spinner("Loading PDF preview..."):
                    show_pdf(save_image_path)
                
                # Process resume data only if we haven't already or if it's a new PDF
                if 'resume_data' not in st.session_state or st.session_state.app_state == 'pdf_uploaded':
                    with st.spinner("Extracting resume data..."):
                        st.session_state.resume_data = extract_resume_data_with_gemini(save_image_path)
                        st.session_state.resume_text = pdf_reader(save_image_path)
                        st.session_state.app_state = 'data_extracted'
                
                # Display resume analysis
                if st.session_state.resume_data:
                    st.header("**Resume Analysis**")
                    
                    with st.container():
                        st.subheader("**Your Basic info**")
                        try:
                            # Do job and category predictions only once
                            if 'recommended_job' not in st.session_state:
                                with st.spinner("Analyzing resume..."):
                                    st.session_state.recommended_job = job_recommendation(st.session_state.resume_text)
                                    st.session_state.predicted_category = predict_category(st.session_state.resume_text)
                            
                            pages = st.session_state.resume_data.get('no_of_pages', 'N/A')
                            email = st.session_state.resume_data.get('email', 'N/A')
                            mobile = st.session_state.resume_data.get('mobile_number', 'N/A')
                            st.text(f'Resume pages: {pages}')
                            st.text(f'Email: {email}')
                            st.text(f'Mobile: {mobile}')
                        except Exception as e:
                            st.error(f"Error processing resume info: {str(e)}")
                        
                        cand_level = ''
                        
                        # Set skills in session state if not already there
                        if 'skills' not in st.session_state:
                            st.session_state.skills = st.session_state.resume_data['skills']
                        
                        # Display skills
                        skills_key = f"skills_{st.session_state.current_pdf}"
                        st_tags(label='### Skills that you have', text='See our skills recommendation', 
                               value=st.session_state.skills, key=skills_key, maxtags=15)
                        
                        # Show predictions
                        st.success("The predicted category of the Resume is: " + st.session_state.predicted_category)
                        st.success("According to our Analysis, this Resume is suited for the aforementioned job: " + st.session_state.recommended_job)
                    
                    # Skill recommendations - only compute if not already in session state
                    if 'recommended_skills' not in st.session_state:
                        rec_data = load_recommendation_data()
                        recommended_skills = []
                        rec_course = ''
                        
                        # Process skills only once per PDF upload
                        for i in st.session_state.resume_data['skills']:
                            i_lower = i.lower()
                            
                            # Data science recommendation
                            if i_lower in rec_data['ds_keyword']:
                                recommended_skills = rec_data['ds_skills']
                                rec_course = course_recommender(rec_data['ds_course'])
                                break
                            
                            # Web development recommendation
                            elif i_lower in rec_data['web_keyword']:
                                recommended_skills = rec_data['web_skills']
                                rec_course = course_recommender(rec_data['web_course'])
                                break
                            
                            # Android App Development
                            elif i_lower in rec_data['android_keyword']:
                                recommended_skills = rec_data['android_skills']
                                rec_course = course_recommender(rec_data['android_course'])
                                break
                            
                            # IOS App Development
                            elif i_lower in rec_data['ios_keyword']:
                                recommended_skills = rec_data['ios_skills']
                                rec_course = course_recommender(rec_data['ios_course'])
                                break
                            
                            # Ui-UX Recommendation
                            elif i_lower in rec_data['uiux_keyword']:
                                recommended_skills = rec_data['uiux_skills']
                                rec_course = course_recommender(rec_data['uiux_course'])
                                break
                        
                        # Store in session state for future reference
                        st.session_state.recommended_skills = recommended_skills
                        st.session_state.rec_course = rec_course
                        
                        # Insert into database
                        ts = time.time()
                        cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                        cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                        timestamp = str(cur_date + '_' + cur_time)
                        
                        insert_data(
                            st.session_state.resume_data['name'], 
                            st.session_state.resume_data['email'], 
                            timestamp, 
                            str(st.session_state.resume_data['no_of_pages']), 
                            cand_level, 
                            str(st.session_state.resume_data['skills']),
                            str(st.session_state.recommended_skills), 
                            str(st.session_state.rec_course)
                        )
                    
                    # Display recommended skills if available
                    if st.session_state.recommended_skills:
                        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System',
                              value=st.session_state.recommended_skills, key='rec_skills', maxtags=10)
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                    
                    # Resume writing tips - check only once to improve performance
                    with st.expander("Resume Tips & Ideas", expanded=False):
                        st.subheader("**Resume Tips & Ideas**")
                        resume_text = st.session_state.resume_text
                        
                        if 'Objective' in resume_text:
                            st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',unsafe_allow_html=True)
                        else:
                            st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)
                        
                        if 'Declaration' in resume_text:
                            st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration/h4>''',unsafe_allow_html=True)
                        else:
                            st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',unsafe_allow_html=True)
                        
                        if 'Hobbies' in resume_text or 'Interests' in resume_text:
                            st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>''',unsafe_allow_html=True)
                        else:
                            st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Hobbies. It will show your persnality to the Recruiters and give the assurance that you are fit for this role or not.</h4>''',unsafe_allow_html=True)
                        
                        if 'Achievements' in resume_text:
                            st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>''',unsafe_allow_html=True)
                        else:
                            st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Achievements. It will show that you are capable for the required position.</h4>''',unsafe_allow_html=True)
                        
                        if 'Projects' in resume_text:
                            st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects </h4>''',unsafe_allow_html=True)
                        else:
                            st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Projects. It will show that you have done work related the required position or not.</h4>''',unsafe_allow_html=True)
                    
                    # GEMINI Integration
                    st.subheader("AI Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Summarize the Candidate", key="summarize_btn"):
                            with st.spinner("Generating summary..."):
                                input_prompt1 = """Act as a Applicant Tracking System(ATS) with deep knowledge and expertise in various job fields. Analyse the entire Resume and give a brief summary of the candidate from the Resume. Give the Summary in points within 100 to 150 words."""
                                text = st.session_state.resume_text
                                
                                # Use session state to cache response
                                if 'summary_response' not in st.session_state:
                                    st.session_state.summary_response = get_gemini_response1(input_prompt1, text)
                                
                                st.subheader("Candidate Summary:")
                                st.write(st.session_state.summary_response)
                    
                    with col2:
                        input_text = st.text_area("Job Description: ", key="input")
                        if st.button("Candidate Matching", key="matching_btn"):
                            if input_text == "":
                                st.warning("Please provide Job Description")
                            else:
                                with st.spinner("Analyzing match..."):
                                    input_prompt2 = """You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of various job fields and ATS functionality, your task is to evaluate the resume against the provided job description. First the output should come as Key skills missing and then last final thoughts."""
                                    text = st.session_state.resume_text
                                    
                                    # Create a unique key for this job description
                                    match_key = f"match_{hash(input_text)}"
                                    
                                    # Use session state to cache response
                                    if match_key not in st.session_state:
                                        st.session_state[match_key] = get_gemini_response2(input_prompt2, text, input_text)
                                    
                                    st.write(st.session_state[match_key])
        
    else:
        # Admin section
        st.success('Welcome to Admin Side')
        
        with st.container():
            ad_user = st.text_input("Username")
            ad_password = st.text_input("Password", type='password')
            
            if st.button('Login'):
                if ad_user == 'abc' and ad_password == '123':
                    st.success("Welcome !!")
                    
                    # Get database connection
                    connection = get_database_connection()
                    cursor = connection.cursor()
                    
                    # Display Data - only fetch when necessary
                    try:
                        connection.select_db("sql12764371")
                        cursor.execute('''SELECT * FROM user_data''')
                        data = cursor.fetchall()
                        
                        st.header("**User's👨‍💻 Data**")
                        
                        # Convert to DataFrame
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                        
                        # Only create visualization if there's data
                        if not df.empty and 'Actual Skills' in df.columns:
                            # Use session state to avoid recomputing
                            if 'admin_chart' not in st.session_state:
                                # Here we use pandas built-in plotting which is much lighter than matplotlib
                                skills_series = df['Actual Skills'].str.split(',').explode().str.strip()
                                skill_counts = skills_series.value_counts()
                                
                                if not skill_counts.empty:
                                    chart_data = pd.DataFrame({
                                        'Skill': skill_counts.index,
                                        'Count': skill_counts.values
                                    })
                                    st.session_state.admin_chart = chart_data
                            
                            # Display chart
                            if 'admin_chart' in st.session_state:
                                st.bar_chart(st.session_state.admin_chart.set_index('Skill'))
                        
                        st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
                    
                    except Exception as e:
                        st.error(f"Database error: {str(e)}")
                    finally:
                        cursor.close()
                else:
                    st.error("Wrong ID & Password Provided")

if __name__ == "__main__":
    run()