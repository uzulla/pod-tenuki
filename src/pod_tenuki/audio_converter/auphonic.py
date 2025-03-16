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
        json_data = {
            "preset": preset_uuid,
            "metadata": {
                "title": title
            }
        }
        
        # Set Content-Type header to application/json
        headers = {"Content-Type": "application/json"}
        
        logger.debug(f"Creating production with preset {preset_uuid} and title {title}")
        logger.debug(f"Request payload: {json_data}")
        
        response = self.session.post(url, json=json_data, headers=headers)
        
        # Log response for debugging
        if response.status_code != 200:
            logger.error(f"Auphonic API error: {response.status_code} {response.text}")
        
        response.raise_for_status()
        return response.json()
    
    def upload_audio(self, production_uuid: str, audio_file: str) -> Dict[str, Any]:
        """
        Upload an audio file to a production.

        Args:
            production_uuid: UUID of the production.
            audio_file: Path to the audio file.

        Returns:
            Response data dictionary.
        """
        url = f"{self.api_url}/production/{production_uuid}/upload.json"
        
        with open(audio_file, 'rb') as f:
            file_size = os.path.getsize(audio_file)
            with tqdm(total=file_size, unit='B', unit_scale=True, desc=f"Uploading {Path(audio_file).name}") as pbar:
                files = {'input_file': f}
                response = self.session.post(
                    url, 
                    files=files,
                    data={'input_file': Path(audio_file).name}
                )
                pbar.update(file_size)
        
        response.raise_for_status()
        return response.json()
    
    def start_production(self, production_uuid: str) -> Dict[str, Any]:
        """
        Start processing a production.

        Args:
            production_uuid: UUID of the production.

        Returns:
            Response data dictionary.
        """
        url = f"{self.api_url}/production/{production_uuid}/start.json"
        response = self.session.post(url)
        response.raise_for_status()
        return response.json()
    
    def get_production_status(self, production_uuid: str) -> Dict[str, Any]:
        """
        Get the status of a production.

        Args:
            production_uuid: UUID of the production.

        Returns:
            Production status dictionary.
        """
        url = f"{self.api_url}/production/{production_uuid}.json"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def wait_for_production(self, production_uuid: str, check_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a production to complete.

        Args:
            production_uuid: UUID of the production.
            check_interval: Interval in seconds between status checks.

        Returns:
            Final production status dictionary.
        """
        logger.info(f"Waiting for production {production_uuid} to complete...")
        
        with tqdm(desc="Processing audio", unit="checks") as pbar:
            while True:
                status = self.get_production_status(production_uuid)
                status_string = status.get("status_string", "")
                
                if status.get("status") == 3:  # Status 3 means completed
                    logger.info(f"Production completed: {status_string}")
                    return status
                
                if status.get("status") == 4:  # Status 4 means error
                    error_message = status.get("error_message", "Unknown error")
                    logger.error(f"Production failed: {error_message}")
                    raise RuntimeError(f"Production failed: {error_message}")
                
                logger.debug(f"Current status: {status_string}")
                pbar.update(1)
                time.sleep(check_interval)
    
    def download_results(self, production_uuid: str, output_dir: str) -> List[str]:
        """
        Download the results of a production.

        Args:
            production_uuid: UUID of the production.
            output_dir: Directory to save the downloaded files.

        Returns:
            List of paths to downloaded files.
        """
        status = self.get_production_status(production_uuid)
        output_files = status.get("output_files", [])
        
        if not output_files:
            logger.warning("No output files available for download")
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        downloaded_files = []
        
        for file_info in output_files:
            download_url = file_info.get("download_url")
            filename = file_info.get("filename")
            
            if not download_url or not filename:
                continue
            
            file_path = output_path / filename
            
            logger.info(f"Downloading {filename}...")
            
            response = self.session.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            downloaded_files.append(str(file_path))
            logger.info(f"Downloaded {filename} to {file_path}")
        
        return downloaded_files

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
    production_uuid = production.get("uuid")
    
    # Upload the audio file
    logger.info(f"Uploading {file_name} to production {production_uuid}")
    client.upload_audio(production_uuid, audio_file)
    
    # Start the production
    logger.info(f"Starting production {production_uuid}")
    client.start_production(production_uuid)
    
    # Wait for the production to complete
    status = client.wait_for_production(production_uuid)
    
    # Download the results
    logger.info(f"Downloading results for production {production_uuid}")
    downloaded_files = client.download_results(production_uuid, output_dir)
    
    return downloaded_files, status
