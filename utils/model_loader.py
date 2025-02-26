# models/model_loader.py
import pickle
import streamlit as st

@st.cache_resource
def load_ml_models():
    """Load ML models with proper caching."""
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
