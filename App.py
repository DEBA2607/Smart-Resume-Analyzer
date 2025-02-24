import streamlit as st
import re
import pickle
import nltk
nltk.download('stopwords')
import google.generativeai as genai
import pandas as pd
import base64, random
import time, datetime
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
import io, random
from streamlit_tags import st_tags
import pymysql
from Recommendor.Skills import ds_keyword,ds_skills, web_keyword, web_skills ,android_keyword, android_skills ,ios_keyword, ios_skills, uiux_keyword, uiux_skills
from Recommendor.Courses import ds_course, web_course, android_course, ios_course, uiux_course

#Genai API here 

load_dotenv()
genai.configure(api_key=os.getenv("API_KEY"))
def get_gemini_response1(input_prompt,text):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([input_prompt,text])
    return response.text

def get_gemini_response2(input_prompt,text,input):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([input_prompt,text,input])
    return response.text

# NLP Models here 
# Load models===========================================================================================================
rf_classifier_categorization = pickle.load(open('models/rf_classifier_categorization.pkl', 'rb'))
tfidf_vectorizer_categorization = pickle.load(open('models/tfidf_vectorizer_categorization.pkl', 'rb'))
rf_classifier_job_recommendation = pickle.load(open('models/rf_classifier_job_recommendation.pkl', 'rb'))
tfidf_vectorizer_job_recommendation = pickle.load(open('models/tfidf_vectorizer_job_recommendation.pkl', 'rb'))

# Clean resume==========================================================================================================
def cleanResume(txt):
    cleanText = re.sub('http\S+\s', ' ', txt)
    cleanText = re.sub('RT|cc', ' ', cleanText)
    cleanText = re.sub('#\S+\s', ' ', cleanText)
    cleanText = re.sub('@\S+', '  ', cleanText)
    cleanText = re.sub('[%s]' % re.escape("""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""), ' ', cleanText)
    cleanText = re.sub(r'[^\x00-\x7f]', ' ', cleanText)
    cleanText = re.sub('\s+', ' ', cleanText)
    return cleanText


# Prediction and Category Name
@st.cache_resource
def predict_category(resume_text):
    resume_text = cleanResume(resume_text)
    resume_tfidf = tfidf_vectorizer_categorization.transform([resume_text])
    predicted_category = rf_classifier_categorization.predict(resume_tfidf)[0]
    return predicted_category

def job_recommendation(resume_text):
    resume_text= cleanResume(resume_text)
    resume_tfidf = tfidf_vectorizer_job_recommendation.transform([resume_text])
    recommended_job = rf_classifier_job_recommendation.predict(resume_tfidf)[0]
    return recommended_job
# Upto here

def get_table_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(fh,caching=True,check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    # close open handles
    converter.close()
    fake_file_handle.close()
    return text

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = F'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)       

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

connection = pymysql.connect(host='127.0.0.1', user='root', password='Deba2607')
cursor = connection.cursor()

@st.cache_resource
def insert_data(type, email, timestamp, no_of_pages, cand_level, skills, recommended_skills,
                courses):
    DB_table_name = 'user_data'
    insert_sql = "insert IGNORE into " + DB_table_name + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s)"""
    rec_values = (
    type, email, timestamp, str(no_of_pages),cand_level, skills, recommended_skills,
    courses)
    cursor.execute(insert_sql, rec_values)
    connection.commit()

st.set_page_config(
    page_title="Smart Resume Analyzer",
)

def run():
    st.title("Smart Resume Analyser")
    st.sidebar.markdown("# Choose User")
    activities = ["User", "Admin"]
    choice = st.sidebar.selectbox("Choose among the given options:", activities)

 
    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS SRA;"""
    cursor.execute(db_sql)
    connection.select_db("sra")

    # Create table
    DB_table_name = 'user_data'
    table_sql = "CREATE TABLE IF NOT EXISTS " + DB_table_name + """(ID INT NOT NULL AUTO_INCREMENT,Type varchar(100),Email_ID VARCHAR(50),Timestamp VARCHAR(50) NOT NULL,Page_no VARCHAR(5) NOT NULL,User_level VARCHAR(30) NOT NULL,Actual_skills VARCHAR(300) NOT NULL,Recommended_skills VARCHAR(300) NOT NULL,Recommended_courses VARCHAR(600) NOT NULL,PRIMARY KEY (ID),UNIQUE(Email_ID));"""
    cursor.execute(table_sql)
    if choice == 'User':
        pdf_file = st.file_uploader("Choose your Resume", type=["pdf"])
        if pdf_file is not None:
            save_image_path = './Uploaded_Resumes/' + pdf_file.name
            with open(save_image_path, "wb") as f:
                f.write(pdf_file.getbuffer())
            show_pdf(save_image_path)
            resume_data = ResumeParser(save_image_path).get_extracted_data()
            if resume_data:
                ## Get the whole resume data
                resume_text = pdf_reader(save_image_path)

                st.header("**Resume Analysis**")
               
                st.subheader("**Your Basic info**")
                try:
                    recommended_job = job_recommendation(resume_text)
                    predicted_category = predict_category(resume_text)
                    st.text('Resume pages: ' + str(resume_data['no_of_pages']))
                    st.text('Email: ' + resume_data['email'])
                    st.text('Contact: ' + resume_data['mobile_number'])
                except:
                    pass
                cand_level = ''
                
                ## Skills shown
                st_tags(label='### Skills that you have',
                                   text='See our skills recommendation',
                                   value=resume_data['skills'], key='10',maxtags= 15)
                # Prediction 
                st.success("The predicted category of the Resume is: " + predicted_category)
                st.success("According to our Analysis, this Resume is suited for the aforementioned job: " + recommended_job)
                
                ##  recommendation 
                recommended_skills = []
                rec_course = ''
                ## Courses recommendation
                for i in resume_data['skills']:
                    ## Data science recommendation
                    if i.lower() in ds_keyword:
                        print(i.lower())
                        recommended_skills = ds_skills
                        st_tags(label='### Recommended skills for you.',text='Recommended skills generated from System',value=recommended_skills, key='2', maxtags=10)
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ds_course)
                        break

                    ## Web development recommendation
                    elif i.lower() in web_keyword:
                        print(i.lower())
                        recommended_skills = web_skills
                        st_tags(label='### Recommended skills for you.',text='Recommended skills generated from System',value=recommended_skills, key='3', maxtags=10)
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job💼</h4>''',unsafe_allow_html=True)
                        rec_course = course_recommender(web_course)
                        break

                    ## Android App Development
                    elif i.lower() in android_keyword:
                        print(i.lower())
                        recommended_skills = android_skills
                        st_tags(label='### Recommended skills for you.',text='Recommended skills generated from System',value=recommended_skills, key='4', maxtags=10)
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(android_course)
                        break

                    ## IOS App Development
                    elif i.lower() in ios_keyword:
                        print(i.lower())
                        recommended_skills = ios_skills
                        st_tags(label='### Recommended skills for you.',text='Recommended skills generated from System',value=recommended_skills, key='5', maxtags=10)
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(ios_course)
                        break

                    ## Ui-UX Recommendation
                    elif i.lower() in uiux_keyword:
                        print(i.lower())
                        recommended_skills = uiux_skills
                        st_tags(label='### Recommended skills for you.',text='Recommended skills generated from System',value=recommended_skills, key='6', maxtags=10)
                        st.markdown('''<h4 style='text-align: left; color: #1ed760;'>Adding this skills to resume will boost the chances of getting a Job💼</h4>''',
                            unsafe_allow_html=True)
                        rec_course = course_recommender(uiux_course)
                        break

                ## Insert into table
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                cur_time = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
                timestamp = str(cur_date + '_' + cur_time)

                ### Resume writing recommendation
                st.subheader("**Resume Tips & Ideas**")
                if 'Objective' in resume_text:
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective</h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add your career objective, it will give your career intension to the Recruiters.</h4>''',unsafe_allow_html=True)
                if 'Declaration' in resume_text:
                    st.markdown('''<h4 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Delcaration/h4>''',unsafe_allow_html=True)
                else:
                    st.markdown('''<h4 style='text-align: left; color: #fabc10;'>[-] According to our recommendation please add Declaration. It will give the assurance that everything written on your resume is true and fully acknowledged by you</h4>''',unsafe_allow_html=True)
                if 'Hobbies' or 'Interests' in resume_text:
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
                insert_data(resume_data['name'], resume_data['email'], timestamp,str(resume_data['no_of_pages']), cand_level, str(resume_data['skills']),str(recommended_skills), str(rec_course))
                
                #GEMINI
                input_prompt1="""Act as a Applicant Tracking System(ATS) with deep knowledge and expertise in various job fields. Analyse the entire Resume and give a brief summary of the candidate from the Resume. Give the Summary in points within 100 to 150 words."""

                input_prompt2 = """You are an skilled ATS (Applicant Tracking System) scanner with a deep understanding of various job fields and ATS functionality, your task is to evaluate the resume against the provided job description. First the output should come as Key skills missing and then last final thoughts."""
                
                
                submit1 = st.button("Summarize the Candidate")

                if submit1:
                        #if uploaded_file is not None:
                            text= resume_text
                            response1=get_gemini_response1(input_prompt1,text)
                            st.subheader("Candidate Summary:")
                            st.write(response1)

                input_text=st.text_area("Job Description: ",key="input")

                submit2 = st.button("Candidate Matching")

                if submit2:
                        if input_text == "":
                            st.warning("Please provide Job Description")
                        else: 
                            text=resume_text
                            response2=get_gemini_response2(input_prompt2,text,input_text)
                            st.write(response2)
                     
    else:
        ## Admin Side
        st.success('Welcome to Admin Side')
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        if st.button('Login'):
            if ad_user == 'abc' and ad_password == '123':
                st.success("Welcome !!")
                # Display Data
                cursor.execute('''SELECT*FROM user_data''')
                data = cursor.fetchall()
                st.header("**User's👨‍💻 Data**")
                df = pd.DataFrame(data, columns=['ID', 'Type', 'Email', 'Timestamp', 'Total Page','User Level', 'Actual Skills', 'Recommended Skills','Recommended Course'])
                st.dataframe(df)
                skills_series = df['Actual Skills'].str.split(',').explode().str.strip()
    
                # Count occurrences of each skill
                skill_counts = skills_series.value_counts()
    
                # Create a bar chart
                plt.figure(figsize=(12, 6))
                skill_counts.plot(kind='bar', color='skyblue')
                plt.title('Actual Skills Overview')
                plt.xlabel('Skills')
                plt.ylabel('Count')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                st.pyplot(plt)
                st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
            else:
                st.error("Wrong ID & Password Provided")
        
run()
