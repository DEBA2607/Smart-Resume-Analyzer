import streamlit as st
import datetime
import time
from streamlit_tags import st_tags
from utils.pdf_utils import pdf_reader, show_pdf, extract_resume_data_with_gemini
from utils.session_state import reset_session_state
from utils.database import insert_data
from services.ml_service import predict_category, job_recommendation
from services.recommendation_service import load_recommendation_data, course_recommender
from services.ai_service import get_gemini_response1, get_gemini_response2

def render_user_view():
    """Render the user view of the application"""
    if 'current_pdf' not in st.session_state:
        st.session_state.current_pdf = None

    with st.container():
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])

        if pdf_file is not None:
            process_uploaded_pdf(pdf_file)

def process_uploaded_pdf(pdf_file):
    """Process the uploaded PDF file"""
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
        display_resume_analysis(save_image_path)

def display_resume_analysis(save_image_path):
    """Display the resume analysis results"""
    st.header("**Resume Analysis**")
    
    # Display basic info
    display_basic_info()
    
    # Display skills and recommendations
    display_skills_and_recommendations()
    
    # Display resume tips
    display_resume_tips()
    
    # Display AI analysis
    display_ai_analysis()

def display_basic_info():
    """Display basic information extracted from the resume"""
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

def display_skills_and_recommendations():
    """Display skills and related recommendations"""
    cand_level = ''

    if 'skills' not in st.session_state:
        st.session_state.skills = st.session_state.resume_data['skills']

    skills_key = f"skills_{st.session_state.current_pdf}"
    st_tags(label='### Skills that you have', text='See our skills recommendation',
            value=st.session_state.skills, key=skills_key, maxtags=15)

    st.success("The predicted category of the Resume is: " + st.session_state.predicted_category)
    st.success("According to our Analysis, this Resume is suited for the aforementioned job: " + st.session_state.recommended_job)

    if 'recommended_skills' not in st.session_state:
        generate_recommendations()

    # Save data to database
    save_to_database(cand_level)

    if st.session_state.recommended_skills:
        st_tags(label='### Recommended skills for you.', text='Recommended skills generated from System',
            value=st.session_state.recommended_skills, key='rec_skills', maxtags=10)
        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost the chances of getting a Job💼</h4>''',
            unsafe_allow_html=True)

def generate_recommendations():
    """Generate skill and course recommendations"""
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

def save_to_database(cand_level):
    """Save the analysis results to database"""
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

def display_resume_tips():
    """Display tips for improving the resume"""
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

def display_ai_analysis():
    """Display AI analysis of the resume"""
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