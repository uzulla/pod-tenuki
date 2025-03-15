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

# Google Cloud configuration
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')

# OpenAI API configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def validate_config():
    """Validate that all required configuration variables are set."""
    missing_vars = []
    
    if not AUPHONIC_API_KEY:
        missing_vars.append('AUPHONIC_API_KEY')
    
    if not GOOGLE_APPLICATION_CREDENTIALS:
        missing_vars.append('GOOGLE_APPLICATION_CREDENTIALS')
    elif not Path(GOOGLE_APPLICATION_CREDENTIALS).exists():
        missing_vars.append('GOOGLE_APPLICATION_CREDENTIALS (file not found)')
    
    if not GOOGLE_CLOUD_PROJECT:
        missing_vars.append('GOOGLE_CLOUD_PROJECT')
    
    if not OPENAI_API_KEY:
        missing_vars.append('OPENAI_API_KEY')
    
    if missing_vars:
        raise ValueError(f"Missing required configuration variables: {', '.join(missing_vars)}")
    
    return True
