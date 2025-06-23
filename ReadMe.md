# 🤖 Resume Filtering Bot with Google Agent Development Kit (ADK)

## 🚀 Project Idea

The **Resume Filtering Bot** is an intelligent conversational agent designed to streamline the initial stages of the hiring process for HR professionals. Leveraging the power of Google's Agent Development Kit (ADK) and Gemini 2.0 Flash, this bot automates the collection, parsing, scoring, and notification steps involved in matching candidate resumes with specific job descriptions.

Instead of manually sifting through resumes, HR users can simply interact with the bot, provide job descriptions and candidate resumes, and receive instant compatibility scores, facilitating faster and more efficient candidate shortlisting. Candidates, on the other hand, can receive automated follow-up or rejection emails, improving the overall candidate experience. 
For Candidate users, they can play around with this tool and get scores for their resumes so they will know their resumes better.

## ✨ Key Features & Functionalities

The bot operates as a multi-agent system, orchestrated by a central dispatcher, with each agent specializing in a particular task:

1.  **Dispatcher (`Coordinator`):**
    * Acts as the central orchestrator, managing the conversation flow.
    * Identifies user type (HR or Candidate).
    * Explain our system to users
    * Delegates tasks to specialized sub-agents based on the current conversation state.

2.  **Resume PDF Reader (`ResumePdfReaderAgent`):**
    * Handles the uploading and extraction of text content from multiple PDF resume files.
    * Returns raw, unsummarized text for each resume, preserving formatting.

3.  **Job Description Reader (`JobDescriptionReaderAgent`):**
    * Manages the uploading and extraction of text content from a single PDF job description.
    * Provides the plain text of the job description for analysis.

4.  **Resume Parser (`InformationParserAgent`):**
    * Takes raw resume texts and parses them into structured data.
    * Extracts key information such as:
        * Skills (e.g., Python, SQL, Project Management)
        * Years of work experience
        * Education details (degree level, institution quality)
        * Candidate contact information (e.g., email)

5.  **Compatibility Scorer (`ScorerAgent`):**
    * Calculates a compatibility score for each resume against the job description, ranging from **1 to 100**.
    * The scoring logic applies the following weights:
        * **Skills Match: 50%** (more matched skills = higher score)
        * **Work Experience Years: 30%** (longer experience = higher score)
        * **Education: 20%** (better school/higher degree = higher score)
    * Outputs a list of JSON objects containing the score and the candidate's email for each resume.

8.  **HR Notifier (`HrNotifierAgent`):**
    * **Sends follow-up emails** to candidates whose scores are **above 60**.
    * **Sends rejection emails** to candidates whose scores are **60 or below**.
    * Emails include personalized details like score and matched skills (for follow-ups).

## 💻 Technology Stack

* **Google Agent Development Kit (ADK):** The core framework for building conversational agents.
* **Google Gemini 2.0 Flash:** The underlying Large Language Model (LLM) powering the agents.
* **Python3:** The primary programming language.
* **Pydantic:** For data validation and defining structured inputs/outputs for agents.

## ⚙️ Setup & Installation

Follow these steps to get your Resume Filtering Bot up and running.

### Prerequisites

* Python 3.9+ installed.
* `git` installed.

### Commands

First, clone this repository to your local machine:

```bash
git clone <repository_url> # Replace with your actual repo URL
cd resume_filter_bot
# Create a virtual environment
python -m venv adk_env

# Activate the virtual environment
# On macOS/Linux:
source adk_env/bin/activate
# On Windows:
.\adk_env\Scripts\activate

# Install project dependencies
pip install google-adk python-dotenv pydantic google-api-python-client google-auth-oauthlib

# Run on local UI
ask web # you are now free to talk with the agent
