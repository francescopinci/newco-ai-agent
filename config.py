"""
Application configuration settings.
Only secrets need to be configured manually in Streamlit Cloud.
"""

import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# OpenAI Agent Configuration (conversational interaction)
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.6
OPENAI_MAX_TOKENS = 700
OPENAI_TOP_P = 1.0
OPENAI_PRESENCE_PENALTY = 0.0
OPENAI_FREQUENCY_PENALTY = 0.2

# Summary Configuration (stable, accurate restatement)
OPENAI_SUMMARY_MODEL = "gpt-4o-mini"
OPENAI_SUMMARY_TEMPERATURE = 0.25
OPENAI_SUMMARY_MAX_TOKENS = 1000
OPENAI_SUMMARY_TOP_P = 1.0
OPENAI_SUMMARY_PRESENCE_PENALTY = 0.0
OPENAI_SUMMARY_FREQUENCY_PENALTY = 0.2

# Evaluation Configuration (analytical assessment)
OPENAI_EVALUATION_MODEL = "gpt-4o"
OPENAI_EVALUATION_TEMPERATURE = 0.4
OPENAI_EVALUATION_MAX_TOKENS = 1400
OPENAI_EVALUATION_TOP_P = 1.0
OPENAI_EVALUATION_PRESENCE_PENALTY = 0.0
OPENAI_EVALUATION_FREQUENCY_PENALTY = 0.3

# App Configuration
APP_TITLE = "The Unfair Advantage Scout"
APP_DESCRIPTION = "Expert mentor and interviewer for aspiring startup founders"

# Test Mode Configuration
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
