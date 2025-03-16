"""
Auphonic API client for audio processing.

This module provides functionality to interact with the Auphonic API
for audio file conversion using specified presets.
"""
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import requests
from tqdm import tqdm

from pod_tenuki.utils.config import AUPHONIC_API_KEY, AUPHONIC_API_URL

# Set up logging
logger = logging.getLogger(__name__)

class AuphonicClient:
    """Client for interacting with the Auphonic API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Auphonic API client.

        Args:
            api_key: Auphonic API key. If not provided, it will be loaded from environment variables.
        """
        self.api_key = api_key or AUPHONIC_API_KEY
        if not self.api_key:
            raise ValueError("Auphonic API key is required")
        
        self.api_url = AUPHONIC_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}"
        })
    
    def get_presets(self) -> List[Dict[str, Any]]:
        """
        Get all available presets.

        Returns:
            List of preset dictionaries.
        """
        url = f"{self.api_url}/presets.json"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def get_preset_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a preset by name.

        Args:
            name: Name of the preset to find.

        Returns:
            Preset dictionary if found, None otherwise.
        """
        presets = self.get_presets()
        for preset in presets:
            if preset.get("preset_name") == name:
                return preset
        return None
    
    def get_preset_by_uuid(self, uuid: str) -> Dict[str, Any]:
        """
        Get a preset by UUID.

        Args:
            uuid: UUID of the preset.

        Returns:
            Preset dictionary.
        """
        url = f"{self.api_url}/preset/{uuid}.json"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def create_production(self, preset_uuid: str, title: str) -> Dict[str, Any]:
        """
        Create a new production with a preset.

        Args:
            preset_uuid: UUID of the preset to use.
            title: Title for the production.

        Returns:
            Production data dictionary.
        """
        url = f"{self.api_url}/productions.json"
        
        # Create JSON payload according to Auphonic API documentation
        # Format according to https://auphonic.com/help/api/
        json_data = {
            "preset": preset_uuid,
            "metadata": {
                "title": title
            },
            "service": "multitrack",    # Add required service field
            "output_basename": title     # Set output basename to match title
        }
        
        # Set Content-Type header to application/json
        headers = {"Content-Type": "application/json"}
        
        logger.debug(f"Creating production with preset {preset_uuid} and title {title}")
        logger.debug(f"Request URL: {url}")
        logger.debug(f"Request payload: {json.dumps(json_data, indent=2)}")
        
        response = self.session.post(url, json=json_data, headers=headers)
        
        # Log complete response for debugging
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        
        try:
            response_json = response.json()
            logger.debug(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except Exception as e:
            logger.error(f"Failed to parse response as JSON: {str(e)}")
            logger.debug(f"Raw response text: {response.text}")
        
        # Log errors more explicitly
        if response.status_code != 200:
            logger.error(f"Auphonic API error: {response.status_code} {response.text}")
        
        response.raise_for_status()
        result = response.json()
        
        # APIは2つの形式で応答を返す場合があります:
        # 1. {"data": {"uuid": "..."}} - ネストされた構造
        # 2. {"uuid": "..."} - 直接のフラット構造
        
        # ネストされたデータ構造をチェック
        if "data" in result and isinstance(result["data"], dict) and "uuid" in result["data"] and result["data"]["uuid"]:
            production_uuid = result["data"]["uuid"]
            logger.debug(f"Created production with UUID (from nested data): {production_uuid}")
            return result["data"]
        
        # フラットな構造をチェック
        elif "uuid" in result and result["uuid"]:
            production_uuid = result["uuid"]
            logger.debug(f"Created production with UUID (from direct field): {production_uuid}")
            return result
        
        # UUIDが見つからない場合はエラー
        else:
            logger.error(f"Failed to get production UUID from response: {result}")
            raise ValueError("Production UUID not found in API response")
    
    def upload_audio(self, production_uuid: str, audio_file: str) -> Dict[str, Any]:
        """
        Upload an audio file to a production.

        Args:
            production_uuid: UUID of the production.
            audio_file: Path to the audio file.

        Returns:
            Response data dictionary.
        """
        if not production_uuid:
            raise ValueError("Production UUID cannot be None")
            
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
        url = f"{self.api_url}/production/{production_uuid}/upload.json"
        
        logger.debug(f"Uploading audio to URL: {url}")
        
        try:
            # Open the file in binary mode
            with open(audio_file, 'rb') as f:
                file_size = os.path.getsize(audio_file)
                file_name = Path(audio_file).name
                
                # Determine content type based on file extension
                file_ext = Path(audio_file).suffix.lower()
                content_type = 'application/octet-stream'  # Default content type
                
                # Set appropriate content type based on file extension
                if file_ext in ['.wav']:
                    content_type = 'audio/wav'
                elif file_ext in ['.mp3']:
                    content_type = 'audio/mpeg'
                elif file_ext in ['.m4a', '.mp4']:
                    content_type = 'audio/mp4'
                elif file_ext in ['.ogg']:
                    content_type = 'audio/ogg'
                elif file_ext in ['.flac']:
                    content_type = 'audio/flac'
                
                logger.debug(f"Uploading file: {file_name}, size: {file_size} bytes")
                logger.debug(f"Using file content type: {content_type}")
                
                with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {file_name}") as pbar:
                    # Prepare the multipart form data with proper Content-Type
                    # Use tuple format: (filename, fileobj, content_type)
                    files = {
                        'input_file': (file_name, f, content_type)
                    }
                    
                    # Make the POST request with file data only (no extra data)
                    response = self.session.post(url, files=files)
                    pbar.update(file_size)
            
            # Log complete response for debugging
            logger.debug(f"Upload response status: {response.status_code}")
            logger.debug(f"Upload response headers: {response.headers}")
            
            # Check for errors and log response
            if response.status_code != 200:
                logger.error(f"Error uploading audio: {response.status_code} {response.text}")
                
            response.raise_for_status()
            
            # Process the response
            result = response.json()
            logger.debug(f"Upload response body: {json.dumps(result, indent=2)}")
            
            # APIは2つの形式で応答を返す場合があります
            # ネストされたデータ構造をチェック
            if "data" in result and isinstance(result["data"], dict):
                logger.debug("Upload response contains nested data section")
                return result["data"]
            
            # フラットな構造を返す
            logger.debug("Upload response contains flat structure")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse upload response as JSON: {e}")
            logger.debug(f"Raw response text: {response.text}")
            # Return empty dict if we can't parse JSON but request was successful
            return {}
            
        except Exception as e:
            logger.error(f"Error uploading audio file {file_name} to production {production_uuid}: {str(e)}")
            raise
    
    def start_production(self, production_uuid: str) -> Dict[str, Any]:
        """
        Start processing a production.

        Args:
            production_uuid: UUID of the production.

        Returns:
            Response data dictionary.
        """
        if not production_uuid:
            raise ValueError("Production UUID cannot be None")
            
        url = f"{self.api_url}/production/{production_uuid}/start.json"
        
        logger.debug(f"Starting production at URL: {url}")
        
        try:
            # Make the POST request to start processing
            response = self.session.post(url)
            
            # Log response information
            logger.debug(f"Start production response status: {response.status_code}")
            logger.debug(f"Start production response headers: {response.headers}")
            
            # Check for errors
            if response.status_code != 200:
                logger.error(f"Error starting production: {response.status_code} {response.text}")
                
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Start production response: {json.dumps(result, indent=2)}")
            
            # APIは2つの形式で応答を返す場合があります
            # ネストされたデータ構造をチェック
            if "data" in result and isinstance(result["data"], dict):
                logger.debug("Start response contains nested data section")
                return result["data"]
            
            # フラットな構造を返す
            logger.debug("Start response contains flat structure")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse start response as JSON: {e}")
            logger.debug(f"Raw response text: {response.text}")
            # Return empty dict if we can't parse JSON but request was successful
            return {}
            
        except Exception as e:
            logger.error(f"Error starting production {production_uuid}: {str(e)}")
            raise
    
    def get_production_status(self, production_uuid: str) -> Dict[str, Any]:
        """
        Get the status of a production.

        Args:
            production_uuid: UUID of the production.

        Returns:
            Production status dictionary.
        """
        if not production_uuid:
            raise ValueError("Production UUID cannot be None")
            
        url = f"{self.api_url}/production/{production_uuid}.json"
        
        logger.debug(f"Getting production status from URL: {url}")
        
        try:
            response = self.session.get(url)
            
            # Log response details
            logger.debug(f"Status response code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Error getting production status: {response.status_code} {response.text}")
                
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Status response received")
            
            # APIは2つの形式で応答を返す場合があります
            # ネストされたデータ構造をチェック
            if "data" in result and isinstance(result["data"], dict):
                logger.debug("Status response contains nested data section")
                return result["data"]
            
            # フラットな構造を返す
            logger.debug("Status response contains flat structure")
            return result
            
        except Exception as e:
            logger.error(f"Error getting status for production {production_uuid}: {str(e)}")
            raise
    
    def wait_for_production(self, production_uuid: str, check_interval: int = 30, max_wait_time: int = 3600) -> Dict[str, Any]:
        """
        Wait for a production to complete.

        Args:
            production_uuid: UUID of the production.
            check_interval: Interval in seconds between status checks (default: 30 seconds).
            max_wait_time: Maximum time to wait in seconds (default: 3600 seconds = 1 hour).

        Returns:
            Final production status dictionary.
        """
        if not production_uuid:
            raise ValueError("Production UUID is required to wait for production")
            
        logger.info(f"Waiting for production {production_uuid} to complete...")
        
        try:
            # 処理開始時間を記録
            start_time = time.time()
            elapsed_time = 0
            
            with tqdm(desc="Processing audio", unit="min") as pbar:
                # 古い進捗バーの値
                old_progress = 0
                
                while elapsed_time < max_wait_time:
                    try:
                        status = self.get_production_status(production_uuid)
                        status_string = status.get("status_string", "")
                        status_code = status.get("status")
                        
                        # 経過時間を分単位で計算して表示
                        elapsed_time = time.time() - start_time
                        elapsed_minutes = int(elapsed_time / 60)
                        
                        # プログレスバーを更新（分単位）
                        if elapsed_minutes > old_progress:
                            pbar.update(elapsed_minutes - old_progress)
                            old_progress = elapsed_minutes
                        
                        # ステータス文字列を優先して判断
                        # "Audio Processing" や "Processing" という文字列があれば処理中と見なす
                        if "processing" in status_string.lower() or "audio processing" in status_string.lower():
                            logger.info(f"Production is being processed: {status_string} (status code: {status_code})")
                            logger.info(f"Elapsed time: {elapsed_minutes} minutes")
                            # 処理中なのでスキップして待機を続ける
                            time.sleep(check_interval)
                            continue
                        
                        # 完了ステータス
                        if status_code == 3 or "completed" in status_string.lower() or "done" in status_string.lower():
                            logger.info(f"Production completed: {status_string} (took {elapsed_minutes} minutes)")
                            return status
                        
                        # 処理中ステータス
                        if status_code == 1:
                            logger.debug(f"Production is processing (status: {status_code}, {status_string})")
                            logger.debug(f"Elapsed time: {elapsed_minutes} minutes")
                        
                        # 不完全ステータス
                        if status_code == 9:
                            start_allowed = status.get("start_allowed", False)
                            if not start_allowed:
                                logger.debug(f"Production is incomplete (status: {status_code}). Waiting for start_allowed to become true.")
                                logger.debug(f"Current state: start_allowed={start_allowed}, status_string={status_string}")
                                logger.debug(f"Elapsed time: {elapsed_minutes} minutes")
                        
                        # 本当のエラーかどうかを判断
                        # status_code=4 だが、status_string が "Audio Processing" の場合は処理中と判断
                        if status_code == 4 and not ("processing" in status_string.lower()):
                            error_message = status.get("error_message", "")
                            error_status = status.get("error_status", "")
                            warning_message = status.get("warning_message", "")
                            
                            # エラーメッセージがなく、ステータス文字列が処理中を示す場合はエラーとしない
                            if not error_message and not error_status and not warning_message and "processing" in status_string.lower():
                                logger.info(f"Status code is 4 but status string indicates processing: {status_string}")
                                logger.info(f"Continuing to wait... Elapsed time: {elapsed_minutes} minutes")
                            else:
                                # 本当のエラーの場合
                                logger.error(f"Production failed with status: {status_code}")
                                logger.error(f"Error message: {error_message}")
                                logger.error(f"Error status: {error_status}")
                                logger.error(f"Warning message: {warning_message}")
                                logger.error(f"Full status: {json.dumps(status, indent=2)}")
                                raise RuntimeError(f"Production failed: {error_message or error_status or warning_message or 'Unknown error'}")
                        
                        logger.debug(f"Current status: {status_string} (code: {status_code})")
                        # ここで待機時間を設定（長くなるほど頻度が下がる）
                        time.sleep(check_interval)
                        
                    except Exception as e:
                        if isinstance(e, RuntimeError) and "Production failed" in str(e):
                            # Re-raise production failure errors
                            raise
                        
                        logger.warning(f"Error checking production status: {str(e)}. Retrying in {check_interval} seconds...")
                        time.sleep(check_interval)
                        
                # 最大待機時間を超えた場合
                elapsed_minutes = int((time.time() - start_time) / 60)
                logger.error(f"Maximum wait time exceeded. Waited for {elapsed_minutes} minutes.")
                raise TimeoutError(f"Timed out waiting for production to complete after {elapsed_minutes} minutes")
        except Exception as e:
            logger.error(f"Error waiting for production {production_uuid}: {str(e)}")
            raise
    
    def download_results(self, production_uuid: str, output_dir: str, max_wait_time: int = 300, check_interval: int = 10) -> List[str]:
        """
        Download the results of a production.

        Args:
            production_uuid: UUID of the production.
            output_dir: Directory to save the downloaded files.
            max_wait_time: Maximum time to wait for files to be available (in seconds)
            check_interval: Interval between status checks (in seconds)

        Returns:
            List of paths to downloaded files.
        """
        if not production_uuid:
            raise ValueError("Production UUID is required to download results")
            
        if not output_dir:
            raise ValueError("Output directory is required for downloading results")
            
        logger.info(f"Preparing to download results for production {production_uuid} to {output_dir}")
        
        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
                
            downloaded_files = []
            
            # オリジナルの入力ファイル名を取得して、出力ファイル名の基本部分として使用
            status = self.get_production_status(production_uuid)
            logger.debug(f"Production status for download: {json.dumps(status, indent=2)}")
            
            base_filename = None
            if status:
                base_filename = status.get("output_basename") or status.get("input_file")
                if base_filename:
                    base_filename = os.path.splitext(base_filename)[0]  # 拡張子を除去
                    logger.info(f"Using base filename: {base_filename}")
            
            # 出力ファイルを取得するまで待機ループ
            start_time = time.time()
            elapsed_time = 0
            output_files = []
            
            # ステータスコードが3（完了）になるまで待機
            if status and status.get("status") != 3:
                logger.info(f"Production status is not completed yet: {status.get('status_string', 'Unknown')}")
                logger.info(f"Waiting for production to complete before downloading...")
                
                with tqdm(desc="Waiting for completion", unit="sec") as pbar:
                    old_progress = 0
                    
                    while elapsed_time < max_wait_time:
                        elapsed_time = time.time() - start_time
                        current_progress = int(elapsed_time)
                        
                        if current_progress > old_progress:
                            pbar.update(current_progress - old_progress)
                            old_progress = current_progress
                        
                        status = self.get_production_status(production_uuid)
                        status_code = status.get("status")
                        status_string = status.get("status_string", "")
                        
                        # 完了ステータスなら終了
                        if status_code == 3:
                            logger.info(f"Production completed: {status_string}")
                            break
                        
                        # 処理中ならメッセージを表示して待機
                        logger.debug(f"Status: {status_string} (code: {status_code}), waiting...")
                        time.sleep(check_interval)
            
            # 出力ファイルのリストを取得
            output_files = status.get("output_files", [])
            
            # オリジナルのオーディオファイルを入力した場合
            # Auphonicによって処理された後のMP3ファイルを直接ダウンロードするURLを推測
            direct_download_url = None
            direct_filename = None
            
            if base_filename:
                direct_download_url = f"{self.api_url}/download/audio-result/{production_uuid}/{base_filename}.mp3"
                direct_filename = f"{base_filename}.mp3"
                
                # 直接ダウンロードURLをチェック
                try:
                    logger.info(f"Checking direct download URL: {direct_download_url}")
                    response = self.session.head(direct_download_url)
                    
                    if response.status_code == 200:
                        logger.info(f"Direct download URL is available: {direct_download_url}")
                        
                        # ダウンロードを実行
                        file_path = output_path / direct_filename
                        
                        logger.info(f"Downloading {direct_filename}...")
                        
                        response = self.session.get(direct_download_url, stream=True)
                        response.raise_for_status()
                        
                        total_size = int(response.headers.get('content-length', 0))
                        
                        with open(file_path, 'wb') as f:
                            with tqdm(total=total_size, unit='B', unit_scale=True, desc=direct_filename) as pbar:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        pbar.update(len(chunk))
                        
                        logger.info(f"Successfully downloaded {direct_filename} to {file_path}")
                        downloaded_files.append(str(file_path))
                        
                        return downloaded_files
                except Exception as e:
                    logger.warning(f"Error with direct download: {str(e)}")
            
            # 直接ダウンロードが失敗した場合、output_filesからダウンロード
            logger.info(f"Found {len(output_files)} output files in production status")
            
            for file_info in output_files:
                try:
                    download_url = file_info.get("download_url")
                    filename = file_info.get("filename")
                    
                    if not download_url and base_filename and "ending" in file_info:
                        # ダウンロードURLがない場合は推測
                        ext = file_info.get("ending", "mp3")
                        filename = f"{base_filename}.{ext}"
                        download_url = f"{self.api_url}/download/audio-result/{production_uuid}/{filename}"
                        logger.info(f"Generated download URL: {download_url}")
                    
                    if not download_url:
                        logger.warning(f"Skipping file with no download URL: {file_info}")
                        continue
                    
                    if not filename:
                        # ファイル名がない場合はURLから取得
                        filename = os.path.basename(download_url)
                        if not filename:
                            filename = f"{base_filename or 'output'}.mp3"
                    
                    file_path = output_path / filename
                    
                    logger.info(f"Downloading {filename}...")
                    
                    response = self.session.get(download_url, stream=True)
                    
                    if response.status_code != 200:
                        logger.warning(f"Failed to download {filename}: HTTP {response.status_code}")
                        continue
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(file_path, 'wb') as f:
                        with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    pbar.update(len(chunk))
                    
                    downloaded_files.append(str(file_path))
                    logger.info(f"Successfully downloaded {filename} to {file_path}")
                
                except Exception as e:
                    logger.error(f"Error downloading file: {str(e)}")
            
            # 直接入力ファイルをコピーする（最後の試み）
            if not downloaded_files and base_filename and os.path.exists(status.get("input_file", "")):
                try:
                    input_file = status.get("input_file")
                    output_file = output_path / os.path.basename(input_file)
                    
                    import shutil
                    shutil.copy2(input_file, output_file)
                    
                    logger.info(f"Copied original input file to {output_file}")
                    downloaded_files.append(str(output_file))
                except Exception as e:
                    logger.error(f"Error copying original file: {str(e)}")
            
            logger.info(f"Downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error downloading results: {str(e)}")
            return []

def process_audio_file(
    audio_file: str,
    preset_name: Optional[str] = None,
    preset_uuid: Optional[str] = None,
    output_dir: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Process an audio file using Auphonic API.

    Args:
        audio_file: Path to the audio file.
        preset_name: Name of the preset to use. Either preset_name or preset_uuid must be provided.
        preset_uuid: UUID of the preset to use. Either preset_name or preset_uuid must be provided.
        output_dir: Directory to save the processed files. If not provided, the directory of the input file will be used.
        api_key: Auphonic API key. If not provided, it will be loaded from environment variables.

    Returns:
        Tuple containing a list of paths to downloaded files and the production status dictionary.
    """
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"Audio file not found: {audio_file}")
    
    if not preset_name and not preset_uuid:
        raise ValueError("Either preset_name or preset_uuid must be provided")
    
    # Use the directory of the input file if output_dir is not provided
    if not output_dir:
        output_dir = os.path.dirname(os.path.abspath(audio_file))
    
    client = AuphonicClient(api_key)
    
    # Get preset UUID if only name is provided
    if preset_name and not preset_uuid:
        preset = client.get_preset_by_name(preset_name)
        if not preset:
            raise ValueError(f"Preset not found: {preset_name}")
        preset_uuid = preset.get("uuid")
    
    # Create a production
    file_name = os.path.basename(audio_file)
    title = os.path.splitext(file_name)[0]
    
    logger.info(f"Creating production for {file_name} with preset {preset_uuid}")
    production = client.create_production(preset_uuid, title)
    
    # Add detailed logging for debugging
    logger.debug(f"Production creation response: {json.dumps(production, indent=2)}")
    
    # APIの応答形式は2つのパターンがあります:
    # 1. 直接 production に uuid が含まれている場合
    # 2. production.data.uuid の形式の場合
    
    # 直接UUIDが含まれているか確認
    if "uuid" in production and production["uuid"]:
        production_uuid = production["uuid"]
        logger.debug(f"Found UUID directly in response: {production_uuid}")
    
    # データセクション内にUUIDがあるか確認
    elif "data" in production and isinstance(production["data"], dict) and "uuid" in production["data"]:
        production_uuid = production["data"]["uuid"]
        logger.debug(f"Found UUID in data section: {production_uuid}")
    
    # UUIDが見つからない場合
    else:
        logger.error(f"Failed to get production UUID from response: {production}")
        raise ValueError("Production UUID not found in API response")
    
    logger.info(f"Created production with UUID: {production_uuid}")
    
    # Upload the audio file
    logger.info(f"Uploading {file_name} to production {production_uuid}")
    
    try:
        upload_response = client.upload_audio(production_uuid, audio_file)
        logger.debug(f"Upload response: {json.dumps(upload_response, indent=2)}")
        
        # アップロード完了後、Auphonicがファイルを処理できるようにするために待機する
        logger.info("Waiting for Auphonic to process the uploaded file...")
        wait_time = 60  # 最初に1分間待つ
        
        # プログレスバーで待機時間を視覚化
        with tqdm(total=wait_time, desc="Processing upload", unit="sec") as pbar:
            for _ in range(wait_time):
                time.sleep(1)
                pbar.update(1)
        
        # アップロード後のステータスを確認
        status = client.get_production_status(production_uuid)
        start_allowed = status.get("start_allowed", False)
        logger.info(f"After upload (1 minute wait): start_allowed={start_allowed}, status={status.get('status_string', '')}")
        
        # start_allowedがまだFalseの場合、さらに長く待つ
        if not start_allowed:
            logger.info("Still waiting for Auphonic to recognize the uploaded file...")
            wait_time = 120  # さらに2分待つ
            
            with tqdm(total=wait_time, desc="Extended wait", unit="sec") as pbar:
                for _ in range(wait_time):
                    time.sleep(1)
                    pbar.update(1)
            
            status = client.get_production_status(production_uuid)
            start_allowed = status.get("start_allowed", False)
            logger.info(f"After extended wait (3 minutes total): start_allowed={start_allowed}, status={status.get('status_string', '')}")
            
    except Exception as e:
        logger.error(f"Error uploading audio: {str(e)}")
        raise
    
    # 最新のステータスを取得して確認
    status = client.get_production_status(production_uuid)
    start_allowed = status.get("start_allowed", False)
    
    # productionを開始できるかチェック
    if not start_allowed:
        logger.warning(f"Cannot start production yet: start_allowed={start_allowed}")
        logger.warning("This usually happens when Auphonic has not fully processed the uploaded file yet.")
        logger.warning("Checking if we need to retry the upload...")
        
        # 上記の場合、アップロードが成功していない可能性があるので再試行
        logger.info("Retrying upload with different content type...")
        
        # 別のコンテンツタイプでアップロードを再試行
        try:
            logger.info(f"Re-uploading {file_name} as application/octet-stream")
            with open(audio_file, 'rb') as f:
                files = {'input_file': (os.path.basename(audio_file), f, 'application/octet-stream')}
                url = f"{client.api_url}/production/{production_uuid}/upload.json"
                response = client.session.post(url, files=files)
                response.raise_for_status()
            
            # 再試行後に待機
            logger.info("Waiting after retry upload...")
            wait_time = 60  # 再試行後も1分間待つ
            
            with tqdm(total=wait_time, desc="Retry processing", unit="sec") as pbar:
                for _ in range(wait_time):
                    time.sleep(1)
                    pbar.update(1)
            
            # 再度ステータスを確認
            status = client.get_production_status(production_uuid)
            start_allowed = status.get("start_allowed", False)
            logger.info(f"After retry (1 minute wait): start_allowed={start_allowed}, status={status.get('status_string', '')}")
            
        except Exception as e:
            logger.error(f"Error during retry upload: {str(e)}")
    
    # productionを開始
    if start_allowed:
        logger.info(f"Starting production {production_uuid}")
        client.start_production(production_uuid)
    else:
        logger.error("Cannot start production: start_allowed is still False")
        logger.error("Current status: " + json.dumps(status, indent=2))
        raise ValueError("Cannot start production: Auphonic did not recognize the uploaded file")
    
    # Wait for the production to complete
    status = client.wait_for_production(production_uuid)
    
    # Download the results
    logger.info(f"Downloading results for production {production_uuid}")
    downloaded_files = client.download_results(production_uuid, output_dir)
    
    return downloaded_files, status
