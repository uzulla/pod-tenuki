"""Tests for configuration utilities."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, Mock


@pytest.mark.unit
class TestConfig:
    """Test configuration utilities."""

    def test_validate_config_success(self, mock_env_vars, tmp_path):
        """Test successful configuration validation."""
        # Create a dummy credentials file
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        with patch.dict(os.environ, {
            'AUPHONIC_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_APPLICATION_CREDENTIALS': str(cred_file),
            'GOOGLE_CLOUD_PROJECT': 'test-project',
        }):
            # Reload config module to pick up new env vars
            import importlib
            from pod_tenuki.utils import config
            importlib.reload(config)

            # Should not raise any exception
            assert config.validate_config() is True

    def test_validate_config_missing_auphonic_key(self, monkeypatch, tmp_path):
        """Test validation fails when AUPHONIC_API_KEY is missing."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        with patch.dict(os.environ, {
            'AUPHONIC_API_KEY': '',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_APPLICATION_CREDENTIALS': str(cred_file),
            'GOOGLE_CLOUD_PROJECT': 'test-project',
        }, clear=True):
            import importlib
            from pod_tenuki.utils import config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.validate_config()
            assert 'AUPHONIC_API_KEY' in str(exc_info.value)

    def test_validate_config_missing_openai_key(self, monkeypatch, tmp_path):
        """Test validation fails when OPENAI_API_KEY is missing."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        with patch.dict(os.environ, {
            'AUPHONIC_API_KEY': 'test_key',
            'OPENAI_API_KEY': '',
            'GOOGLE_APPLICATION_CREDENTIALS': str(cred_file),
            'GOOGLE_CLOUD_PROJECT': 'test-project',
        }, clear=True):
            import importlib
            from pod_tenuki.utils import config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.validate_config()
            assert 'OPENAI_API_KEY' in str(exc_info.value)

    def test_validate_config_missing_google_credentials(self, monkeypatch):
        """Test validation fails when GOOGLE_APPLICATION_CREDENTIALS is missing."""
        with patch.dict(os.environ, {
            'AUPHONIC_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_APPLICATION_CREDENTIALS': '',
            'GOOGLE_CLOUD_PROJECT': 'test-project',
        }, clear=True):
            import importlib
            from pod_tenuki.utils import config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.validate_config()
            assert 'GOOGLE_APPLICATION_CREDENTIALS' in str(exc_info.value)

    def test_validate_config_google_credentials_file_not_found(self, monkeypatch):
        """Test validation fails when credentials file doesn't exist."""
        with patch.dict(os.environ, {
            'AUPHONIC_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_APPLICATION_CREDENTIALS': '/nonexistent/path/credentials.json',
            'GOOGLE_CLOUD_PROJECT': 'test-project',
        }, clear=True):
            import importlib
            from pod_tenuki.utils import config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.validate_config()
            assert 'GOOGLE_APPLICATION_CREDENTIALS' in str(exc_info.value)
            assert 'file not found' in str(exc_info.value)

    def test_validate_config_missing_google_project(self, monkeypatch, tmp_path):
        """Test validation fails when GOOGLE_CLOUD_PROJECT is missing."""
        cred_file = tmp_path / "credentials.json"
        cred_file.write_text('{}')

        with patch.dict(os.environ, {
            'AUPHONIC_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key',
            'GOOGLE_APPLICATION_CREDENTIALS': str(cred_file),
            'GOOGLE_CLOUD_PROJECT': '',
        }, clear=True):
            import importlib
            from pod_tenuki.utils import config
            importlib.reload(config)

            with pytest.raises(ValueError) as exc_info:
                config.validate_config()
            assert 'GOOGLE_CLOUD_PROJECT' in str(exc_info.value)
