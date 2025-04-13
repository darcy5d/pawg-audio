"""
Trend Detection Module

This module provides comprehensive trend analysis across podcast episodes,
including entity tracking, sentiment analysis, prediction tracking, and trend detection.
"""

from .entity_tracker import EntityTracker
from .sentiment_analyzer import SentimentAnalyzer
from .prediction_tracker import PredictionTracker
from .trend_detector import TrendDetector
from .models import (
    Entity,
    EntityMention,
    EntityRelationship,
    SentimentAnalysis,
    Prediction,
    Trend,
    SpeakerProfile
)

__all__ = [
    'EntityTracker',
    'SentimentAnalyzer',
    'PredictionTracker',
    'TrendDetector',
    'Entity',
    'EntityMention',
    'EntityRelationship',
    'SentimentAnalysis',
    'Prediction',
    'Trend',
    'SpeakerProfile'
] 