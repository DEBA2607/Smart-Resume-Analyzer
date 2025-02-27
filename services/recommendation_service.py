import streamlit as st
import random
from Recommendor.Skills import ds_keyword, ds_skills, web_keyword, web_skills, android_keyword, android_skills, ios_keyword, ios_skills, uiux_keyword, uiux_skills
from Recommendor.Courses import ds_course, web_course, android_course, ios_course, uiux_course

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