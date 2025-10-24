import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from typing import TypedDict, List
import pandas as pd

# Load variables from .env file
load_dotenv()

# API Keys & LLM Initialization
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_EXTRACTION_MODEL = os.getenv("LLM_EXTRACTION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
LLM_EMAIL_MODEL = os.getenv("LLM_EMAIL_MODEL", "llama-3.1-8b-instant")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0))

llm_extraction = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name=LLM_EXTRACTION_MODEL,
    temperature=LLM_TEMPERATURE
)

llm_email = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name=LLM_EMAIL_MODEL,
    temperature=LLM_TEMPERATURE
)

# Database Configuration
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DATABASE")
}

# Email Configuration
SMTP_CONFIG = {
    "SMTP_SERVER": os.getenv("SMTP_SERVER"),
    "SMTP_PORT": int(os.getenv("SMTP_PORT")),
    "SENDER_EMAIL": os.getenv("SENDER_EMAIL"),
    "SENDER_PASSWORD": os.getenv("SENDER_PASSWORD"),
    "RECEIVER_EMAIL": os.getenv("RECEIVER_EMAIL")
}

# Data Schemas
NEW_CATALOG_ITEM_TEMPLATE = {
    "Product Name": "", "SKU": "", "Description": "",
    "Price": None, "MOQ": None, "Specifications": "",
    "Availability": "", "Extraction_Confidence": 0.98
}

# LangGraph State Definition
class GraphState(TypedDict):
    """Represents the state of our graph."""
    encoded_image: str
    extraction_template: dict
    extracted_item: dict
    historical_df: pd.DataFrame
    factors: List[str]
    suggested_status: str
    final_result: dict
    row_data_for_db: dict
    email_subject: str
    email_body_html: str