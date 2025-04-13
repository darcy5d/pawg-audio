"""
Speaker Identification Module

This module provides comprehensive speaker identification and tracking capabilities
for podcast episodes, including metadata extraction, LLM-based diarization,
and speaker database management.
"""

from .speaker_identifier import SpeakerIdentifier
from .speaker_database import SpeakerDatabase
from .transcript_segmenter import TranscriptSegmenter
from .prompts import SpeakerIdentificationPrompts

__all__ = [
    'SpeakerIdentifier',
    'SpeakerDatabase',
    'TranscriptSegmenter',
    'SpeakerIdentificationPrompts'
] 