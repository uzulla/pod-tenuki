"""Configuration utilities for pod-tenuki."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parents[3] / '.env'
load_dotenv(dotenv_path=env_path)

# Auphonic API configuration
AUPHONIC_API_KEY = os.getenv('AUPHONIC_API_KEY')
AUPHONIC_API_URL = 'https://auphonic.com/api'

# Gemini API configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Google Cloud Speech-to-Text configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
GOOGLE_STORAGE_BUCKET = os.getenv('GOOGLE_STORAGE_BUCKET')

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def validate_config():
    """Validate that all required configuration variables are set."""
    missing_vars = []
    
    if not AUPHONIC_API_KEY:
        missing_vars.append('AUPHONIC_API_KEY')
    
    # Gemini APIはもう使わないのでチェックから除外
    # if not GEMINI_API_KEY:
    #     missing_vars.append('GEMINI_API_KEY')
    
    if not OPENAI_API_KEY:
        missing_vars.append('OPENAI_API_KEY')
    
    # Google Cloud Speech-to-Text APIに必要な設定をチェック
    if not GOOGLE_APPLICATION_CREDENTIALS:
        missing_vars.append('GOOGLE_APPLICATION_CREDENTIALS')
    elif not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        missing_vars.append('GOOGLE_APPLICATION_CREDENTIALS (file not found)')
    
    if not GOOGLE_CLOUD_PROJECT:
        missing_vars.append('GOOGLE_CLOUD_PROJECT')
    
    if missing_vars:
        raise ValueError(f"Missing required configuration variables: {', '.join(missing_vars)}")
    
    return True
