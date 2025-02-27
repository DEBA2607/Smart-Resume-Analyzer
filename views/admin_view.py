import streamlit as st
import pandas as pd
from utils.database import get_database_connection
from utils.download_utils import get_table_download_link

def render_admin_view():
    """Render the admin view of the application"""
    st.success('Welcome to Admin Side')
    
    with st.container():
        ad_user = st.text_input("Username")
        ad_password = st.text_input("Password", type='password')
        
        if st.button('Login'):
            if ad_user == 'abc' and ad_password == '123':
                display_admin_dashboard()
            else:
                st.error("Wrong ID & Password Provided")

def display_admin_dashboard():
    """Display the admin dashboard after successful login"""
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
            display_skills_chart(df)
        
        st.markdown(get_table_download_link(df, 'User_Data.csv', 'Download Report'), unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Database error: {str(e)}")
    finally:
        cursor.close()

def display_skills_chart(df):
    """Display a chart of skills from the dataframe"""
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