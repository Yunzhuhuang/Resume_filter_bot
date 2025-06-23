import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines
from agents import agent

PROJECT_ID = "resume-filter-bot"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://resume-filter-bot"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

app = reasoning_engines.AdkApp(
    agent=agent,
    enable_tracing=True,
)

remote_app = agent_engines.get(
    "projects/162114671603/locations/us-central1/reasoningEngines/1027075801738117120"
)

remote_session = remote_app.create_session(user_id="u_456")
for event in remote_app.stream_query(
    user_id="u_456",
    session_id=remote_session["id"],
    message="hi",
):
    print(event)