import streamlit as st
import json
import google.genai as genai
import google.genai.types as types
import re
import os
import datetime # <-- ADDED

# --- 1. Helper Function: Extract JSON from PDF (Modified for Streamlit) ---
# We use st.cache_data to avoid re-running the extraction on every UI interaction
@st.cache_data(show_spinner=False)
def extract_json_from_pdf(pdf_bytes, prompt_text, _client, model_name): # <-- FIX: Renamed 'client' to '_client'
    """
    Sends a PDF and a prompt to the Gemini API and returns the parsed JSON response.
    """
    try:
        # Use the same model and config as your working code
        response = _client.models.generate_content( # <-- FIX: Use '_client' here
            model=model_name,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt_text
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
                max_output_tokens=4096,
            ),
        )
        
        raw_text = response.text
        data = json.loads(raw_text)
        return data, None  # Return data, no error
        
    except json.JSONDecodeError as e:
        error_msg = f"⚠️ Could not parse output as JSON. Raw output: {raw_text}"
        st.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"An error occurred during API call: {e}"
        st.error(error_msg)
        return None, error_msg

# --- NEW HELPER FUNCTIONS for Experience Calculation ---

def _parse_experience_years(experience_list):
    """Parses CV experience entries and sums up total years."""
    total_duration_years = 0
    current_year = datetime.datetime.now().year

    for job in experience_list:
        try:
            start_date_str = str(job.get('start_date', ''))
            end_date_str = str(job.get('end_date', ''))

            # Find year in start_date
            start_year_match = re.search(r'(\d{4})', start_date_str)
            if not start_year_match:
                continue # Need a start year
            start_year = int(start_year_match.group(1))
            
            # Find year in end_date
            end_year = start_year
            if 'current' in end_date_str.lower() or 'present' in end_date_str.lower():
                end_year = current_year
            else:
                end_year_match = re.search(r'(\d{4})', end_date_str)
                if end_year_match:
                    end_year = int(end_year_match.group(1))
                else:
                    # If no end year, assume 1 year
                    end_year = start_year + 1
            
            # Add 1 to be inclusive (e.g., 2020-2020 is 1 year)
            duration = (end_year - start_year) + 1
            if duration > 0:
                total_duration_years += duration
                
        except (ValueError, TypeError):
            continue # Skip if parsing fails
    
    return total_duration_years

def _parse_jd_experience_req(experience_needed_list):
    """Parses JD experience strings to find the max required years."""
    max_years_required = 0
    for req_text in experience_needed_list:
        # Find numbers like "5+", "5", "5 years"
        matches = re.findall(r'(\d+)\+?\s*year[s]?', req_text, re.IGNORECASE)
        for match in matches:
            try:
                years = int(match)
                if years > max_years_required:
                    max_years_required = years
            except ValueError:
                continue
    return max_years_required

# --- 2. Helper Function: Calculate Match Score (Modified for Streamlit) ---
def calculate_match_score(cv_data, jd_data):
    """
    Calculates a match score and returns a dictionary with all scoring details.
    """
    scores = {}

    # --- Skill Match (70% weight) ---
    cv_skills = set(s.lower().strip() for s in cv_data.get('skills', []) if s)
    jd_skills = set(s.lower().strip() for s in jd_data.get('required_skills', []) if s)
    
    overlapping_skills = cv_skills.intersection(jd_skills)
    
    if len(jd_skills) == 0:
        skill_score = 100.0
    else:
        skill_score = (len(overlapping_skills) / len(jd_skills)) * 100.0
    
    scores['skill_score'] = skill_score
    scores['skill_matches'] = len(overlapping_skills)
    scores['skill_total'] = len(jd_skills)
    scores['overlapping_skills'] = list(overlapping_skills)

    # --- Qualification Match (20% weight) ---
    cv_education_text = " ".join([
        f"{e.get('degree', '')} {e.get('school', '')}" 
        for e in cv_data.get('education', [])
    ]).lower()
    
    # NEW: Add projects text
    cv_projects_text = " ".join([
        f"{p.get('name', '')} {p.get('description', '')}"
        for p in cv_data.get('projects', [])
    ]).lower()

    cv_qual_text = cv_education_text + " " + cv_projects_text # Combined text
    
    jd_qualifications = jd_data.get('qualifications', [])
    matched_quals = 0
    
    if len(jd_qualifications) == 0:
        qual_score = 100.0
    else:
        for qual in jd_qualifications:
            qual_lower = qual.lower().strip()
            if not qual_lower: continue
            
            # Check for keyword matches in the combined text
            if qual_lower in cv_qual_text:
                matched_quals += 1
            # Keep the degree matching logic as a fallback
            elif ("bachelor" in qual_lower or "bs" in qual_lower or "b.s" in qual_lower) and \
                    ("bachelor" in cv_education_text or "bs" in cv_education_text or "b.s" in cv_education_text):
                matched_quals += 1
            elif ("master" in qual_lower or "ms" in qual_lower or "m.s" in qual_lower) and \
                    ("master" in cv_education_text or "ms" in cv_education_text or "m.s" in cv_education_text):
                matched_quals += 1
        
        qual_score = (matched_quals / len(jd_qualifications)) * 100.0
        
    scores['qual_score'] = qual_score
    scores['qual_matches'] = matched_quals
    scores['qual_total'] = len(jd_qualifications)

    # --- Experience Match (10% weight) ---
    
    # NEW: Use parsing functions
    cv_years = _parse_experience_years(cv_data.get('experience', []))
    jd_years_req = _parse_jd_experience_req(jd_data.get('experience_needed', []))

    if jd_years_req == 0:
        exp_score = 100.0 # No specific requirement, so pass
    elif cv_years >= jd_years_req:
        exp_score = 100.0 # Meets or exceeds
    else:
        exp_score = (cv_years / jd_years_req) * 100.0 # Prorated
    
    scores['exp_score'] = exp_score
    scores['cv_years'] = cv_years # Store calculated years for info
    scores['jd_years'] = jd_years_req # Store required years for info

    # --- Final Score (Weighted Average) ---
    total_score = (skill_score * 0.70) + (qual_score * 0.20) + (exp_score * 0.10)
    scores['total_score'] = int(total_score)
    
    return scores

# --- 3. Streamlit App UI ---

# Page configuration
st.set_page_config(
    page_title="CV & JD Matcher",
    page_icon="🤖",
    layout="wide"
)

# --- Sidebar (Inputs) ---
with st.sidebar:
    st.title("📄 CV & JD Matcher")
    st.markdown("Enter your API key and upload your documents to get a match score.")
    
    api_key = st.text_input("Gemini API Key", type="password", help="Get your key from Google AI Studio.")
    model_name = st.selectbox(
        "Select Gemini Model",
        ("gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro")
    )
    
    st.divider()
    
    uploaded_cv = st.file_uploader("Upload your CV (PDF)", type="pdf")
    uploaded_jd = st.file_uploader("Upload the Job Description (PDF)", type="pdf")
    
    st.divider()

    analyze_button = st.button("Analyze Match", type="primary", use_container_width=True)

# --- Main Page (Results) ---

# Initial State
if not analyze_button:
    st.title("CV & Job Description Matching Tool")
    st.markdown("""
    Welcome! This tool uses Google's Gemini AI to analyze a resume against a job description.
    
    **Here's how it works:**
    1.  **AI Extraction:** Gemini reads the PDF files to extract structured data (skills, experience, etc.).
    2.  **Scoring:** A weighted algorithm scores the match based on skills (70%), qualifications (20%), and experience (10%).
    
    <span style="color: #FF4B4B;">**Please provide your Gemini API Key, CV, and Job Description in the sidebar to get started.**</span>
    """, unsafe_allow_html=True)

# After "Analyze" is clicked
if analyze_button:
    # --- Input Validation ---
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not uploaded_cv:
        st.error("Please upload your CV in the sidebar.")
    elif not uploaded_jd:
        st.error("Please upload the Job Description in the sidebar.")
    else:
        # --- Processing ---
        try:
            # Configure client
            client = genai.Client(api_key=api_key)
            
            # Define Prompts
            cv_prompt = """
            Extract candidate information from this resume PDF and output as JSON.
            Structure: {"name": "", "skills": [], "education": [{"school": "", "degree": "", "start_year": "", "end_year": ""}], "experience": [{"company": "", "position": "", "start_date": "", "end_date": "", "description": ""}], "projects": [{"name": "", "description": ""}]}
            - For 'projects', extract key projects mentioned with their descriptions.
            If a field is missing, use an empty string or empty list.
            """
            
            jd_prompt = """
            Extract job requirements from this job description PDF and output as JSON.
            Structure: {"required_skills": [], "qualifications": [], "experience_needed": []}
            - 'required_skills': List of technical skills (e.g., "Python", "React", "SQL").
            - 'qualifications': List of educational or certification requirements (e.g., "BS in Computer Science").
            - 'experience_needed': List of key experience requirements (e.g., "5+ years in software development").
            If a field is missing, use an empty list.
            """

            # Read file bytes
            cv_bytes = uploaded_cv.getvalue()
            jd_bytes = uploaded_jd.getvalue()

            # --- Extraction Step ---
            with st.spinner("Gemini is reading the CV..."):
                cv_data, cv_error = extract_json_from_pdf(cv_bytes, cv_prompt, client, model_name)
            
            with st.spinner("Gemini is reading the Job Description..."):
                jd_data, jd_error = extract_json_from_pdf(jd_bytes, jd_prompt, client, model_name)
            
            # --- Scoring & Display Step ---
            if cv_data and jd_data:
                st.success("Successfully extracted data from both documents!")
                
                with st.spinner("Calculating match score..."):
                    scores = calculate_match_score(cv_data, jd_data)
                
                st.title("Analysis Results")
                
                # --- Score ---
                st.metric(
                    label="Overall Suitability Score",
                    value=f"{scores['total_score']} / 100"
                )
                
                # --- Reasons for the Score ---
                st.subheader("Reasoning for the Score")
                st.markdown("The score is a weighted average: 70% Skills, 20% Qualifications, and 10% Experience.")
                
                # Score Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric(
                    label="Skill Match (70%)",
                    value=f"{scores['skill_score']:.0f}%",
                    help=f"Based on {scores['skill_matches']} out of {scores['skill_total']} required skills."
                )
                col2.metric(
                    label="Qualification Match (20%)",
                    value=f"{scores['qual_score']:.0f}%",
                    help=f"Based on {scores['qual_matches']} out of {scores['qual_total']} qualifications found."
                )
                col3.metric(
                    label="Experience Match (10%)",
                    value=f"{scores['exp_score']:.0f}%",
                    help=f"Calculated {scores['cv_years']:.1f} years vs. required {scores['jd_years']} years."
                )
                
                if scores['overlapping_skills']:
                    st.write("Matching Skills Found:")
                    st.write(f"`{', '.join(scores['overlapping_skills'])}`")
                else:
                    st.write("No matching skills found.")
                
                st.divider()

                # --- JSON Outputs (Side-by-Side) ---
                st.subheader("Extracted Data")
                json_col1, json_col2 = st.columns(2)
                
                with json_col1:
                    st.header("CV Data")
                    st.json(cv_data)
                
                with json_col2:
                    st.header("Job Description Data")
                    st.json(jd_data)
                    
            else:
                st.error("Could not complete analysis. See error messages above.")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.exception(e)


