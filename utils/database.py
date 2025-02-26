# utils/database.py
import streamlit as st
import pymysql

@st.cache_resource
def get_database_connection():
    """Get database connection with connection pooling."""
    try:
        connection = pymysql.connect(
            host=st.secrets["DB"]["HOST"],
            user=st.secrets["DB"]["USER"],
            password=st.secrets["DB"]["PASSWORD"],
            port=st.secrets["DB"]["PORT"],
            cursorclass=pymysql.cursors.DictCursor
        )
        connection.ping(reconnect=True)  # Reconnect if necessary
        return connection
    except pymysql.MySQLError as e:
        st.error(f"Database connection error: {e}")
        return None

def insert_data(type, email, timestamp, no_of_pages, cand_level, skills, recommended_skills, courses):
    """Insert data into the database."""
    connection = get_database_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # ... rest of your code ...
            connection.commit()
            cursor.close()
        except pymysql.MySQLError as e:
            st.error(f"Database error: {e}")
            if connection.open:
                connection.rollback()  # Only rollback if connection is open


