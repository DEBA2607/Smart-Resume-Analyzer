import streamlit as st
import json

def find_jobs_by_location(location_data, job_title=None, radius_miles=50):
    """Find job openings based on location data, with enhanced error handling"""
    import requests
    import json
    import streamlit as st

    # Validate input
    if not location_data:
        st.error("No location data provided")
        return None
        
    # Ensure location_data is a dictionary
    try:
        if isinstance(location_data, str):
            try:
                location_info = json.loads(location_data)
            except json.JSONDecodeError:
                st.error("Invalid JSON in location data")
                return None
        else:
            location_info = location_data

        # Extract country from location_info if available
        country_name = location_info.get("country")

        # If no country was found in the data, look for it in the full address
        if not country_name and location_info.get("full_address"):
            # Common country names to search for in address
            common_countries = [
                "United States", "USA", "US", "United Kingdom", "UK", "Canada",
                "Australia", "Germany", "France", "Italy", "Spain", "Netherlands", "India"
            ]

            for country in common_countries:
                if country.lower() in location_info["full_address"].lower():
                    country_name = country
                    break

        # If we still don't have a country, use state to infer (for US states)
        if not country_name and location_info.get("state"):
            us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                         "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
                         "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
                         "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
                         "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
                         "Alabama", "Alaska", "Arizona", "Arkansas", "California",
                         "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
                         "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas",
                         "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts",
                         "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana",
                         "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
                         "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma",
                         "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
                         "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
                         "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]
            if location_info["state"] in us_states:
                country_name = "United States"

        # If country is found, search for jobs
        if country_name:
            return search_jobs_by_country(country_name, job_title, radius_miles, location_info)
        else:
            # No country detected - return None to trigger country selection
            return None
            
    except Exception as e:
        st.error(f"Error processing location data: {str(e)}")
        return None
            
def search_jobs_by_country(country_name, job_title=None, radius_miles=50, location_info=None):
    """Search for jobs in the specified country, with optional location refinement"""
    import requests
    import json
    import streamlit as st
    
    # Map countries to their Adzuna API country codes
    country_map = {
        "united states": "us",
        "usa": "us",
        "us": "us",
        "united kingdom": "gb",
        "uk": "gb",
        "canada": "ca",
        "australia": "au",
        "germany": "de",
        "france": "fr",
        "italy": "it",
        "netherlands": "nl",
        "spain": "es",
        "india": "in"
    }
    
    # Get the country code for the API endpoint
    country_code = country_map.get(country_name.lower())
    
    if country_code is None:
        st.error(f"Invalid country selected: {country_name}. Using default (US).")
        country_code = "us"  # Set a default rather than returning None
    
    # Get API credentials
    APP_ID = st.secrets["adzuna"]["ADZUNA_APP_ID"]
    API_KEY = st.secrets["adzuna"]["ADZUNA_API_KEY"]
    
    if not APP_ID or not API_KEY:
        st.error("Adzuna API credentials not configured.")
        return None
    
    # Construct API URL
    api_url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    
    # Set up parameters
    params = {
        "app_id": APP_ID,
        "app_key": API_KEY,
        "results_per_page": 15,
        "content-type": "application/json"
    }
    
    # Add job title if provided
    if job_title:
        params["what"] = job_title
    
    # Try to refine location search if we have more specific location data
    location_query = None
    if location_info:
        # Create a more specific location query if possible
        location_parts = []
        if location_info.get("city"):
            location_parts.append(location_info["city"])
        if location_info.get("state"):
            location_parts.append(location_info["state"])
            
        if location_parts:
            location_query = ", ".join(location_parts)
            params["where"] = location_query
            params["distance"] = radius_miles
    
    # If no specific location was added, we'll search the entire country
    if "where" not in params:
        st.info(f"Searching for jobs throughout {country_name}")
    else:
        st.info(f"Searching for jobs near {location_query} in {country_name}")
    
    # Make the API request
    try:
        response = requests.get(api_url, params=params)
        
        if response.status_code == 200:
            try:
                json_response = response.json()
                
                # Process and format the job data
                jobs = []
                for result in json_response.get("results", []):
                    job = {
                        "title": result.get("title", "Unknown Position"),
                        "company": result.get("company", {}).get("display_name", "Unknown Company"),
                        "location": result.get("location", {}).get("display_name", "Location not specified"),
                        "description": result.get("description", "No description available"),
                        "url": result.get("redirect_url", "#"),
                        "salary": f"{result.get('salary_min', 'N/A')} - {result.get('salary_max', 'N/A')}",
                        "date_posted": result.get("created", "Unknown date"),
                        "job_type": "Full-time"  # Default as Adzuna often doesn't specify
                    }
                    jobs.append(job)
                
                if not jobs:
                    st.warning(f"No job openings found in {country_name} matching your criteria.")
                    # Return empty results rather than None
                    return {
                        "jobs": [],
                        "count": 0,
                        "country": country_name,
                        "location_used": location_query if location_query else "Entire country"
                    }
                    
                job_results = {
                    "jobs": jobs,
                    "count": len(jobs),
                    "country": country_name,
                    "location_used": location_query if location_query else "Entire country"
                }
                
                return job_results
                
            except json.JSONDecodeError as e:
                st.error(f"Failed to parse API response: {e}")
                return None
        else:
            st.error(f"API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Request error: {e}")
        return None
            
def test_adzuna_api():
    """Test function to check if Adzuna API is working correctly"""
    import requests
    import streamlit as st
    
    APP_ID = st.secrets["adzuna"]["ADZUNA_APP_ID"]
    API_KEY = st.secrets["adzuna"]["ADZUNA_API_KEY"]
    
    if not APP_ID or not API_KEY:
        st.error("Adzuna API credentials not configured.")
        return
        
    # Simple test query
    api_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": API_KEY,
        "results_per_page": 1,
        "what": "software engineer",
        "where": "New York",
        "content-type": "application/json"
    }
    
    try:
        response = requests.get(api_url, params=params)
        st.write("Status code:", response.status_code)
        st.write("Response:", response.text[:500] + "..." if len(response.text) > 500 else response.text)
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                st.write("JSON parsed successfully")
                st.write("Number of results:", json_data.get("count", 0))
                st.write("First result:", json_data.get("results", [])[0] if json_data.get("results") else "No results")
            except json.JSONDecodeError as e:
                st.error(f"JSON parse error: {e}")
    except Exception as e:
        st.error(f"Request error: {e}")

# Function to display job results in the UI
def display_job_results(job_data):
    """Display job search results in a user-friendly format"""
    if not job_data or not job_data.get("jobs"):
        st.info("No job openings found matching your criteria.")
        return
        
    st.subheader(f"📍 Job Openings Found")
    
    # Show search information
    location_used = job_data.get('location_used', 'your location')
    country = job_data.get('country', 'the specified country')
    st.write(f"Found {len(job_data.get('jobs', []))} job openings in {location_used} matching your profile.")
    
    # Display each job in its own expander
    for job in job_data.get("jobs", []):
        with st.expander(f"{job.get('title')} at {job.get('company')}"):
            st.write(f"**Location:** {job.get('location')}")
            st.write(f"**Type:** {job.get('job_type', 'Not specified')}")
            st.write(f"**Posted:** {job.get('date_posted', 'Not specified')}")
            st.write(f"**Salary:** {job.get('salary', 'Not specified')}")
            st.write(f"**Description:** {job.get('description', 'No description available')[:300]}...")
            if job.get("url"):
                st.markdown(f"[Apply for this job]({job.get('url')})")
