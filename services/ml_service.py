import streamlit as st
from utils.text_utils import cleanResume
from utils.model_loader import load_ml_models

# @st.cache_data
# def predict_category(resume_text):
#     """Predict the resume category."""
#     models = load_ml_models()
#     resume_text = cleanResume(resume_text)
#     resume_tfidf = models['tfidf_vectorizer_categorization'].transform([resume_text])
#     predicted_category = models['rf_classifier_categorization'].predict(resume_tfidf)[0]
#     return predicted_category

@st.cache_data
def job_recommendation(resume_text):
    """Recommend a job based on resume text."""
    models = load_ml_models()
    resume_text = cleanResume(resume_text)
    resume_tfidf = models['tfidf_vectorizer_job_recommendation'].transform([resume_text])
    recommended_job = models['rf_classifier_job_recommendation'].predict(resume_tfidf)[0]
    return recommended_job