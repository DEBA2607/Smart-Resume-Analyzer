# utils/database.py
import streamlit as st
import pymysql
import time

# Remove the cache_resource decorator to prevent connection pooling issues
def get_database_connection():
    """Get a fresh database connection."""
    try:
        connection = pymysql.connect(
            host=st.secrets["DB"]["HOST"],
            user=st.secrets["DB"]["USER"],
            password=st.secrets["DB"]["PASSWORD"],
            port=st.secrets["DB"]["PORT"],
            database=st.secrets["DB"]["DATABASE"],
            cursorclass=pymysql.cursors.DictCursor,
            # Add connection timeout parameters
            connect_timeout=10,
            # Adding autocommit to prevent transaction issues
            autocommit=True
        )
        return connection
    except pymysql.MySQLError as e:
        st.error(f"Database connection error: {e}")
        return None

def insert_data(name, email, timestamp, no_of_pages, cand_level, skills, recommended_skills, courses):
    """Insert data into the database with proper connection handling."""
    # Create a new connection for each operation
    connection = None
    try:
        connection = get_database_connection()
        if not connection:
            return False
            
        cursor = connection.cursor()
        
        # Create the resume_data table if it doesn't exist
        create_table_query = """
        CREATE TABLE IF NOT EXISTS resume_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            timestamp VARCHAR(255),
            no_of_pages VARCHAR(10),
            cand_level VARCHAR(255),
            skills TEXT,
            recommended_skills TEXT,
            courses TEXT
        )
        """
        cursor.execute(create_table_query)
        
        # Insert data into the table
        insert_query = """
        INSERT INTO resume_data 
        (name, email, timestamp, no_of_pages, cand_level, skills, recommended_skills, courses) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            name, email, timestamp, no_of_pages, 
            cand_level, skills, recommended_skills, courses
        ))
        
        cursor.close()
        return True
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return False
    finally:
        # Always close the connection in the finally block
        if connection:
            connection.close()