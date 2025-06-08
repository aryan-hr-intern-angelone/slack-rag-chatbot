import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
    SLACK_SOCKET_TOKEN = os.environ.get("SLACK_SOCKET_TOKEN")
    SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GOOGLE_APLICATION_CREDENTIALS = os.environ.get("GOOGLE_APLICATION_CREDENTIALS")
    AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET")
    AZURE_APPLICATION_ID = os.environ.get("AZURE_APPLICATION_ID")
    AZURE_AUTHORITY_URL = os.environ.get("AZURE_AUTHORITY_URL")
    CUSTOM_WEBHOOK_URL = os.environ.get("CUSTOM_WEBHOOK_URL")
    EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME")
    RANKING_MODEL = os.environ.get("RANKING_MODEL")

env = Config()