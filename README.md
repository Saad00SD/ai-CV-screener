Gemini CV Matcher

An AI-powered Streamlit application that intelligently scores a candidate's resume (CV) against a job description (JD) using Google's Gemini model.

🚀 Overview

This tool helps recruiters and job seekers by providing a detailed suitability score, automating the most time-consuming part of the application process. It uses the Gemini AI to analyze both PDF documents, extract structured data, and perform a sophisticated comparison.

✨ Features

AI-Powered Data Extraction: Uses the Google Gemini API to parse PDF resumes and job descriptions into structured JSON data.

Intelligent Scoring: Calculates a weighted match score based on:

Skills (70%): Direct comparison of skills listed on the CV vs. required by the JD.

Qualifications (20%): Cross-references JD qualifications against the CV's education and projects sections.

Experience (10%): Automatically calculates the candidate's total years of experience from their CV and compares it to the years required in the JD.

Detailed Breakdown: Provides a clear "Reasoning for the Score" with individual metrics for skills, qualifications, and experience.

Side-by-Side View: Displays the extracted JSON data from both the CV and the JD for easy manual review.

Interactive UI: A clean and simple web interface built with Streamlit, complete with file uploaders, spinners, and error handling.

🛠️ How It Works

Input: The user provides their Gemini API Key and uploads two PDF files: the candidate's CV and the job description.

Extract: Gemini reads both documents and extracts key information according to a predefined JSON schema (e.g., skills, education, experience, projects from the CV and required_skills, qualifications, experience_needed from the JD).

Analyze & Score: The Python backend calculates a score for each of the three main categories.

Skills: Percentage of required_skills found in the CV's skills.

Qualifications: Percentage of qualifications found in the combined text of the CV's education and projects.

Experience: Compares the calculated total years from the CV against the required years from the JD.

Display: The final weighted score (70/20/10 split) is presented to the user, along with the detailed breakdown and the raw JSON data.

📦 Setup & Installation

Clone the repository:

git clone [https://github.com/YourUsername/gemini-cv-matcher.git](https://github.com/YourUsername/gemini-cv-matcher.git)
cd gemini-cv-matcher


Create and activate a virtual environment:

# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate


Install the required dependencies:

pip install -r requirements.txt


🏃‍♂️ How to Run

Set your API Key:

You can enter your Google Gemini API Key directly into the app's sidebar.

(Optional) For local development, you could set it as an environment variable.

Run the Streamlit app:

streamlit run streamlit_app.py


Open the app: Open your web browser and go to http://localhost:8501.

Use the tool:

Upload a CV (PDF).

Upload a Job Description (PDF).

Click the "Analyze Match" button.

💻 Technologies Used

Python

Streamlit: For the interactive web UI.

Google Generative AI: For the core PDF-to-JSON extraction using the Gemini model.


Snapshots of this project;
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/fe0945dc-e5b2-4bdb-a106-72378571e24a" />

Final Output;
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/8349b6e9-75d3-445c-86a0-36c91586b339" />
<img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/ded37dff-b9bf-4113-aea8-f3ef39a7cb2d" />


