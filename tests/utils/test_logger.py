"""Tests for logging utilities."""
import logging
import pytest
from pathlib import Path
from pod_tenuki.utils.logger import setup_logger, add_file_handler


@pytest.mark.unit
class TestLogger:
    """Test logging functionality."""

    def test_setup_logger_default(self):
        """Test setting up a logger with default parameters."""
        logger = setup_logger()

        assert logger.name == "pod_tenuki"
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

        # Check that handler is a StreamHandler
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logger_custom_name(self):
        """Test setting up a logger with custom name."""
        logger = setup_logger(name="test_logger")

        assert logger.name == "test_logger"

    def test_setup_logger_custom_level(self):
        """Test setting up a logger with custom level."""
        logger = setup_logger(name="test_logger_debug", level=logging.DEBUG)

        assert logger.level == logging.DEBUG

    def test_setup_logger_clears_existing_handlers(self):
        """Test that setup_logger clears existing handlers."""
        logger = setup_logger(name="test_logger_clear")

        # Set up again
        logger = setup_logger(name="test_logger_clear")

        # Should only have one handler (the new one)
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) == 1

    def test_logger_formatting(self):
        """Test that logger uses correct formatting."""
        logger = setup_logger(name="test_logger_format")

        # Get the formatter from the handler
        handler = logger.handlers[0]
        formatter = handler.formatter

        # Check format string contains expected elements
        assert "%(asctime)s" in formatter._fmt
        assert "%(name)s" in formatter._fmt
        assert "%(levelname)s" in formatter._fmt
        assert "%(message)s" in formatter._fmt

    def test_add_file_handler(self, temp_dir):
        """Test adding a file handler to logger."""
        logger = setup_logger(name="test_logger_file")
        log_file = temp_dir / "test.log"

        # Add file handler
        logger = add_file_handler(logger, str(log_file))

        # Check that file handler was added
        assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)

        # Log a message
        logger.info("Test message")

        # Check that log file was created
        assert log_file.exists()

        # Check that message was written
        content = log_file.read_text()
        assert "Test message" in content

    def test_add_file_handler_creates_directory(self, temp_dir):
        """Test that add_file_handler creates directory if it doesn't exist."""
        logger = setup_logger(name="test_logger_dir")
        log_dir = temp_dir / "logs" / "subdir"
        log_file = log_dir / "test.log"

        # Add file handler
        logger = add_file_handler(logger, str(log_file))

        # Log a message
        logger.info("Test message")

        # Check that directory and file were created
        assert log_dir.exists()
        assert log_file.exists()

    def test_add_file_handler_custom_level(self, temp_dir):
        """Test adding a file handler with custom level."""
        # Logger needs to be at DEBUG level for debug messages to be processed
        logger = setup_logger(name="test_logger_level", level=logging.DEBUG)
        log_file = temp_dir / "test.log"

        # Add file handler with DEBUG level
        logger = add_file_handler(logger, str(log_file), level=logging.DEBUG)

        # Log DEBUG message
        logger.debug("Debug message")

        # Check that DEBUG message was written to file
        content = log_file.read_text()
        assert "Debug message" in content

    def test_file_handler_formatting(self, temp_dir):
        """Test that file handler uses correct formatting."""
        logger = setup_logger(name="test_logger_file_format")
        log_file = temp_dir / "test.log"

        # Add file handler
        logger = add_file_handler(logger, str(log_file))

        # Log a message
        logger.info("Formatted message")

        # Read log file
        content = log_file.read_text()

        # Check format contains expected elements
        assert "test_logger_file_format" in content
        assert "INFO" in content
        assert "Formatted message" in content
