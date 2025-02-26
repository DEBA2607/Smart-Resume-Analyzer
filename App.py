import streamlit as st
import time, datetime
import random
import pandas as pd
from streamlit_tags import st_tags
from PIL import Image  # Import here as it's only used in App.py

from utils.pdf_utils import pdf_reader, show_pdf, extract_resume_data_with_gemini
from utils.text_utils import cleanResume
from utils.model_loader import load_ml_models
from utils.database import get_database_connection, insert_data
from Recommendor.Skills import ds_keyword, ds_skills, web_keyword, web_skills, android_keyword, android_skills, ios_keyword, ios_skills, uiux_keyword, uiux_skills
from Recommendor.Courses import ds_course, web_course, android_course, ios_course, uiux_course

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

# --- Recommendation Functions (moved from Recommendor files for brevity) ---
@st.cache_resource
def load_recommendation_data():
    """Load recommendation data"""
    return {
        'ds_keyword': ds_keyword, 'ds_skills': ds_skills,
        'web_keyword': web_keyword, 'web_skills': web_skills,
        'android_keyword': android_keyword, 'android_skills': android_skills,
        'ios_keyword': ios_keyword, 'ios_skills': ios_skills,
        'uiux_keyword': uiux_keyword, 'uiux_skills': uiux_skills,
        'ds_course': ds_course, 'web_course': web_course,
        'android_course': android_course, 'ios_course': ios_course,
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
# --- ML Prediction Functions ---
@st.cache_data
def predict_category(resume_text):
    """Predict the resume category."""
    models = load_ml_models()
    resume_text = cleanResume(resume_text)
    resume_tfidf = models['tfidf_vectorizer_categorization'].transform([resume_text])
    predicted_category = models['rf_classifier_categorization'].predict(resume_tfidf)[0]
    return predicted_category


@st.cache_data
def job_recommendation(resume_text):
    """Recommend a job based on resume text."""
    models = load_ml_models()
    resume_text = cleanResume(resume_text)
    resume_tfidf = models['tfidf_vectorizer_job_recommendation'].transform([resume_text])
    recommended_job = models['rf_classifier_job_recommendation'].predict(resume_tfidf)[0]
    return recommended_job


# --- Utility Functions ---
import base64


def get_table_download_link(df, filename, text):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


def reset_session_state():
    """Reset session state variables."""
    keys_to_reset = ['skills', 'recommended_skills', 'courses', 'resume_data', 'resume_text', 'recommended_job',
                      'predicted_category']
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]


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
        if 'current_pdf' not in st.session_state:
            st.session_state.current_pdf = None

        with st.container():
            pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])

            if pdf_file is not None:
                if st.session_state.current_pdf != pdf_file.name:
                    reset_session_state()
                    st.session_state.current_pdf = pdf_file.name
                    st.session_state.app_state = 'pdf_uploaded'

                save_image_path = './Uploaded_Resumes/' + pdf_file.name
                with open(save_image_path, "wb") as f:
                    f.write(pdf_file.getbuffer())

                with st.spinner("Loading PDF preview..."):
                    show_pdf(save_image_path)

                if 'resume_data' not in st.session_state or st.session_state.app_state == 'pdf_uploaded':
                    with st.spinner("Extracting resume data..."):
                        st.session_state.resume_data = extract_resume_data_with_gemini(save_image_path)
                        st.session_state.resume_text = pdf_reader(save_image_path)
                        st.session_state.app_state = 'data_extracted'

                if st.session_state.resume_data:
                    st.header("**Resume Analysis**")
                    with st.container():
                        st.subheader("**Your Basic info**")
                        try:
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

                        if 'skills' not in st.session_state:
                            st.session_state.skills = st.session_state.resume_data['skills']

                        skills_key = f"skills_{st.session_state.current_pdf}"
                        st_tags(label='### Skills that you have', text='See our skills recommendation',
                                value=st.session_state.skills, key=skills_key, maxtags=15)

                        st.success(
                            "The predicted category of the Resume is: " + st.session_state.predicted_category)
                        st.success(
                            "According to our Analysis, this Resume is suited for the aforementioned job: " + st.session_state.recommended_job)

                        if 'recommended_skills' not in st.session_state:
                            rec_data = load_recommendation_data()
                            recommended_skills = []
                            rec_course = ''

                            for i in st.session_state.resume_data['skills']:
                                i_lower = i.lower()
                                if i_lower in rec_data['ds_keyword']:
                                    recommended_skills = rec_data['ds_skills']
                                    rec_course = course_recommender(rec_data['ds_course'])
                                    break
                                elif i_lower in rec_data['web_keyword']:
                                    recommended_skills = rec_data['web_skills']
                                    rec_course = course_recommender(rec_data['web_course'])
                                    break
                                elif i_lower in rec_data['android_keyword']:
                                    recommended_skills = rec_data['android_skills']
                                    rec_course = course_recommender(rec_data['android_course'])
                                    break
                                elif i_lower in rec_data['ios_keyword']:
                                    recommended_skills = rec_data['ios_skills']
                                    rec_course = course_recommender(rec_data['ios_course'])
                                    break
                                elif i_lower in rec_data['uiux_keyword']:
                                    recommended_skills = rec_data['uiux_skills']
                                    rec_course = course_recommender(rec_data['uiux_course'])
                                    break

                            st.session_state.recommended_skills = recommended_skills
                            st.session_state.rec_course = rec_course

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