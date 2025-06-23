from typing import List
import vertexai
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.adk.tools import ToolContext
from pydantic import BaseModel, Field
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

import json


def after_greeting_agent_model_callback(callback_context: CallbackContext, llm_response: LlmResponse):
    if llm_response.content and llm_response.content.parts:
        # Assuming simple text response for this example
        if llm_response.content.parts[0].text:
            original_text = llm_response.content.parts[0].text
            if 'Thank you for confirming that you are a candidate' in original_text:
                callback_context.state.__setitem__('user_type', 'candidate')
            if 'Thank you for confirming that you are a HR person' in original_text:
                callback_context.state.__setitem__('user_type', 'HR')
            return None
    return None


def after_resume_agent_model_callback(callback_context: CallbackContext, llm_response: LlmResponse):
    if llm_response.content and llm_response.content.parts:
        if llm_response.content.parts[0].text:
            original_text = llm_response.content.parts[0].text
            if 'json' in original_text:
                original_text = original_text.replace("```", "")
                original_text = original_text.replace("json", "")
                r = json.loads(original_text)
                callback_context.state.__setitem__('resume_list', r)
    return None


def after_job_description_agent_model_callback(callback_context: CallbackContext, llm_response: LlmResponse):
    if llm_response.content and llm_response.content.parts:
        if llm_response.content.parts[0].text:
            original_text = llm_response.content.parts[0].text
            callback_context.state.__setitem__('job_description', original_text)
    return None


def transfer_to_job_description_agent(tool_context: ToolContext):
    tool_context.actions.transfer_to_agent = "JobDescriptionPdfReaderAgent"

resume_pdf_reader = LlmAgent(
    name="ResumePdfReaderAgent",
    model="gemini-2.0-flash",
    description=(
        "Agent to read resumes"
    ),
    instruction=(
        "You are the resume processing agent."
        "You will ask the user for one or more resume PDF files by strictly only saying 'Please upload the resume PDF "
        "files. I will then extract the information for you'."
        "Then your task is to extract the full resume text content from each PDF and return a list of raw resume "
        "texts."
        "Each item in the list should correspond to a single resume and should preserve paragraph breaks and bullet "
        "points where possible. Do not summarize or rephrase—extract the full content verbatim."
        "The extracted text should be a valid json array string representing the list of extracted resume texts. "
        "then without asking the user, pass the work to JobDescriptionPdfReaderAgent"
    ),
    after_model_callback=after_resume_agent_model_callback
)

job_description_pdf_reader = LlmAgent(
    name="JobDescriptionPdfReaderAgent",
    model="gemini-2.0-flash",
    description=(
        "Agent to read job descriptions"
    ),
    instruction=(
        "You are the job description processing agent. You can only process job descriptions"
        "You will ask the user for ONLY one job description PDF file: ."
        "Your task is to extract the full job description text content user input, "
        "You can summarize or rephrase—extract the full content verbatim."
        "Your output MUST be ONLY a valid string representing the extracted job description text."
        "then without asking the user, Pass the work to InformationParserAgent"
    ),
    after_model_callback=after_job_description_agent_model_callback
)

class ParsedResumeDataContent(BaseModel):
    """Represents the detailed parsed data extracted from the resume."""
    skills: list[str] = Field(description="A list of technical skills, soft skills, programming languages, tools, frameworks, and technologies identified in the resume.")
    years: int = Field(description="The total number of years of relevant work experience extracted from the resume.")
    education: list[str] = Field(description="A list of educational entries, each containing degree information and school information.")
    email: str | str = Field(description="The candidate's email address. Can be a string if not a valid email format, but EmailStr is preferred.", default="")

class ParsedResumeData(BaseModel):
    """Represents the detailed parsed data extracted from the resume."""
    data: List[ParsedResumeDataContent] = Field(description="Array of each resume person's ParsedResumeDataContent")

class ScoreEntry(BaseModel):
    email: str = Field(description="The candidate's email address. Can be a string if not a valid email format, but EmailStr is preferred.")
    score: int = Field(description="calculated final compatibility score (1-100) for the candidate in the resume list.")

class Scores(BaseModel):
    data: List[ScoreEntry] = Field(description="Array that contains each resume owner's email and score.")

parser_agent = LlmAgent(
    name="InformationParserAgent",
    model="gemini-2.0-flash",
    description=(
        "Agent to extract key information from resumes"
    ),
    instruction=(
        "You are a sophisticated resume parsing agent. "
        "You will receive the extracted plain texts of the resumes from the state['resume_list'] "
        "From resume_list, for all resume texts, identify and list *all* technical skills, "
        "soft skills, programming languages, tools, frameworks, and technologies mentioned. "
        "Also, identify the total years of relevant work experience (e.g., '5 years of experience'), "
        "any degrees or relevant education, and the candidate's email address. "
        "Your output MUST strictly adhere to the this provided JSON output schema for **EACH** resume texts in "
        "the"
        "resume_list: "
        "{skills: {}(skills list), years: {}(total years of all work experience mentioned in the resume texts), "
        "education: {}(education list with degree and school), email: {}(resume"
        "email address)}"
        "Notice, even resumes with the same email should be parsed into different separate entry in the result list. "
        "then without asking the user, Pass the work to ScoreAgent, don't pass to other agents, ONLY TO ScoreAgent"
    ),
    output_schema=ParsedResumeData,
    output_key='resume_summary'
)

score_agent = LlmAgent(
    name="ScoreAgent",
    model="gemini-2.0-flash",
    description=(
        "Agent to score resumes based on their matches with job description"
    ),
    instruction=(
        "You are the compatibility scoring agent. "
        "You will receive a list of matched resume data in state['resume_summary'] "
        "and the job description text is available in state['job_description']. "  # Correct path
        "You will also receive the user_type from state['user_type']. "  # Correct path
        "Your task is to calculate a final compatibility score (1-100) for *each* resume in the list. "
        "Your output is a list of emails with their corresponding scores, it MUST strictly adhere to the this "
        "provided JSON output schema for each resume summary in"
        "the state['resume_summary']:"
        "{email: {}(resume email address), score: {}(resume final score generated by you)"
        "You should follow this scoring logic weights: Skills (50% - more matches with job_description is better), "
        "Work Experience (30% -"
        "longer experience is"
        "better), Education (20%"
        "- better school and higher degree is better)."
        "Finally, if the user_type in state['user_type'] is HR, pass over your work to HrNotifierAgent, if it is not "
        "HR, don't do anything, your job is done."
    ),
    output_key='score',
    output_schema=Scores
)

hr_notifier_agent = LlmAgent(
    name="HrNotifierAgent",
    model="gemini-2.0-flash",
    instruction=(
        "You are the HR notification agent. Your task is to return mocked follow-up emails "
        "or rejection notices to candidates based on their scores. "
        "You will receive a list of scored resume data in state['score']. "
        "For each candidate in the list, determine if they should receive a follow-up (score >= 60) or a rejection ("
        "score < 60) email."
        "For follow up email, the email title is 'Next steps on software development engineer position', "
        "generate suitable contents that greet the candidate and politely ask "
        "candidates' availability in next two weeks for first round of interview"
        "For rejection email, the email title is 'Application Update', "
        "write exactly: 'Thank you for taking the time to apply for the our role and for your interest in joining our "
        "team."
        "After careful consideration, we regret to inform you that we will not be moving forward with your "
        "application at this time."
        "This decision was not easy, as we received applications from many highly qualified candidates, including "
        "yourself."
        "We genuinely appreciate the effort you put into the process and encourage you to apply for future "
        "opportunities that match your skills and experience. We wish you all the best in your job search and "
        "professional journey.'"
        "Compile a list of these results. "
        "Your final output MUST strictly conform to a list of JSON output with candidate emails and their "
        "corresponding mocked email contents."
    )
)

# --- Define the Root Dispatcher Agent ---
greeting_agent = LlmAgent(
    name="GreetingAgent",
    model="gemini-2.0-flash",
    instruction=(
        "You are the main entry point for the Resume Filtering Bot. "
        "You are a friendly and professional greeting agent, designed to greet users and explain how the Resume Filter "
        "service works."
        "This service supports both job candidates who want to evaluate their resumes"
        "against a job posting and HR professionals who want to quickly screen candidates."
        "For Candidates:"
        "They can upload one or more of their resumes and a job description."
        "The system will analyze and score resumes based on how well they matches the job."
        "the system can return a mock follow-up or rejection email, so they can see what employers might think."
        "For HR Users:"
        "They can upload one or more candidate resumes along with the job description."
        "The system will use intelligent agents to parse, compare, and rank candidates based on how well their "
        "resumes match the job."
        "It can automatically send follow-up or rejection emails to candidates based on the matching score."
        "When a user joins, greet them warmly, tell them what they can do both as a candidate and as a HR person"
        "and ask them if they are a candidate or an HR."
        "If the user says candidate, then only output the word 'Thank you for confirming that you are a candidate' "
        "without any other responses or outputs"
        "If user says HR, then output the word 'Thank you for confirming that you are a HR person' without any other "
        "words or responses."
        "Finally, pass over the work to ResumePdfReaderAgent"
    ),
    after_model_callback=after_greeting_agent_model_callback
)

coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    description="I coordinate greetings and tasks.",
    instruction="transfer work to greeting agent",
    sub_agents=[  # Assign sub_agents here
        greeting_agent,
        resume_pdf_reader,
        job_description_pdf_reader,
        parser_agent,
        score_agent,
        hr_notifier_agent
    ]
)

root_agent = coordinator

# PROJECT_ID = "resume-filter-bot"
# LOCATION = "us-central1"
# STAGING_BUCKET = "gs://resume-filter-bot"
#
# vertexai.init(
#     project=PROJECT_ID,
#     location=LOCATION,
#     staging_bucket=STAGING_BUCKET,
# )
#
# app = reasoning_engines.AdkApp(
#     agent=root_agent,
#     enable_tracing=True,
# )


