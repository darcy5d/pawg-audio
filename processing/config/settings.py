#!/usr/bin/env python3
import os
from dataclasses import dataclass
from typing import Optional

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "transcripts")

# Create directories if they don't exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)

@dataclass
class ProcessingConfig:
    """Configuration for the processing pipeline."""
    
    # Worker counts
    num_download_workers: int = 3
    num_transcribe_workers: int = 2
    num_analyze_workers: int = 2
    
    # Rate limits (calls per minute)
    download_rate_limit: int = 30
    transcribe_rate_limit: int = 20
    analyze_rate_limit: int = 30
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    # Queue management
    queue_check_interval: int = 10  # seconds
    metrics_interval: int = 30  # seconds
    
    # Whisper API configuration
    use_whisper_api: bool = True
    whisper_api_key: Optional[str] = None
    
    # Audio processing
    max_segment_size: int = 25  # MB
    audio_formats: list = None  # Supported audio formats
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.audio_formats is None:
            self.audio_formats = ['mp3', 'm4a', 'wav', 'ogg', 'opus']
        
        # Load API key from environment
        if self.use_whisper_api and not self.whisper_api_key:
            self.whisper_api_key = os.environ.get('OPENAI_API_KEY')
            
            if not self.whisper_api_key:
                raise ValueError("OpenAI API key required but not found in environment")

# Default configuration
default_config = ProcessingConfig() 