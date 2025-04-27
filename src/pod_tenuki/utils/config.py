"""Configuration utilities for pod-tenuki."""
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Try to find and load .env file from multiple locations
possible_env_paths = [
    Path(__file__).parents[3] / '.env',  # プロジェクトルート
    Path.cwd() / '.env',                 # カレントディレクトリ
]

# まず、dotenvの自動検索機能を試す
dotenv_path = find_dotenv(usecwd=True)
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Found .env file at: {dotenv_path}")
else:
    # 自動検索で見つからない場合は手動で探す
    for env_path in possible_env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            print(f"Loaded .env from: {env_path}")
            break

# 絶対パスで直接.envファイルをロード（最終手段）
specific_env_path = "/Users/zishida/dev/pod-tenuki/.env"
if Path(specific_env_path).exists():
    load_dotenv(dotenv_path=specific_env_path)
    print(f"Loaded .env from specific path: {specific_env_path}")

# Auphonic API configuration
AUPHONIC_API_KEY = os.getenv('AUPHONIC_API_KEY')
AUPHONIC_API_URL = 'https://auphonic.com/api'

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
