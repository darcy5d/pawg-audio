"""
Sentiment Analyzer Module

This module provides functionality for tracking and analyzing sentiment towards entities across podcast episodes.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics
from .models import (
    Entity,
    SentimentAnalysis,
    SpeakerProfile
)

class SentimentAnalyzer:
    """Analyzes sentiment towards entities across podcast episodes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sentiment_data: Dict[str, List[SentimentAnalysis]] = {}
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
    
    def add_sentiment(self, sentiment: SentimentAnalysis) -> None:
        """Add a new sentiment analysis."""
        if sentiment.entity_id not in self.sentiment_data:
            self.sentiment_data[sentiment.entity_id] = []
        self.sentiment_data[sentiment.entity_id].append(sentiment)
    
    def get_sentiment_history(
        self,
        entity_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[SentimentAnalysis]:
        """Get sentiment history for an entity within a time range."""
        sentiments = self.sentiment_data.get(entity_id, [])
        if start_time:
            sentiments = [s for s in sentiments if s.timestamp >= start_time]
        if end_time:
            sentiments = [s for s in sentiments if s.timestamp <= end_time]
        return sentiments
    
    def get_average_sentiment(
        self,
        entity_id: str,
        window_days: int = 30
    ) -> Tuple[float, float]:
        """Calculate the average sentiment score and magnitude for an entity in a time window."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        sentiments = self.get_sentiment_history(entity_id, start_time, end_time)
        
        if not sentiments:
            return 0.0, 0.0
        
        scores = [s.score for s in sentiments]
        magnitudes = [s.magnitude for s in sentiments]
        
        return statistics.mean(scores), statistics.mean(magnitudes)
    
    def get_sentiment_trend(
        self,
        entity_id: str,
        window_days: int = 90
    ) -> float:
        """Calculate the sentiment trend (slope) for an entity over a time window."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        sentiments = self.get_sentiment_history(entity_id, start_time, end_time)
        
        if len(sentiments) < 2:
            return 0.0
        
        # Calculate linear regression slope
        timestamps = [(s.timestamp - start_time).total_seconds() for s in sentiments]
        scores = [s.score for s in sentiments]
        
        n = len(timestamps)
        sum_x = sum(timestamps)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(timestamps, scores))
        sum_x2 = sum(x * x for x in timestamps)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def get_sentiment_volatility(
        self,
        entity_id: str,
        window_days: int = 30
    ) -> float:
        """Calculate the sentiment volatility for an entity in a time window."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        sentiments = self.get_sentiment_history(entity_id, start_time, end_time)
        
        if len(sentiments) < 2:
            return 0.0
        
        scores = [s.score for s in sentiments]
        return statistics.stdev(scores)
    
    def get_speaker_sentiment(
        self,
        speaker_id: str,
        entity_id: str
    ) -> List[SentimentAnalysis]:
        """Get sentiment analyses from a specific speaker about an entity."""
        sentiments = self.sentiment_data.get(entity_id, [])
        return [s for s in sentiments if s.speaker_id == speaker_id]
    
    def get_speaker_sentiment_consistency(
        self,
        speaker_id: str,
        entity_id: str
    ) -> float:
        """Calculate how consistent a speaker's sentiment is towards an entity."""
        speaker_sentiments = self.get_speaker_sentiment(speaker_id, entity_id)
        if len(speaker_sentiments) < 2:
            return 1.0  # Perfect consistency if only one sentiment
        
        scores = [s.score for s in speaker_sentiments]
        return 1.0 - statistics.stdev(scores)  # Higher value means more consistent
    
    def get_entity_sentiment_summary(
        self,
        entity_id: str,
        window_days: int = 30
    ) -> Dict:
        """Get a comprehensive summary of sentiment towards an entity."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        sentiments = self.get_sentiment_history(entity_id, start_time, end_time)
        
        if not sentiments:
            return {}
        
        scores = [s.score for s in sentiments]
        magnitudes = [s.magnitude for s in sentiments]
        
        # Group sentiments by speaker
        speaker_sentiments: Dict[str, List[SentimentAnalysis]] = {}
        for sentiment in sentiments:
            if sentiment.speaker_id not in speaker_sentiments:
                speaker_sentiments[sentiment.speaker_id] = []
            speaker_sentiments[sentiment.speaker_id].append(sentiment)
        
        # Calculate speaker-specific metrics
        speaker_metrics = {}
        for speaker_id, speaker_sents in speaker_sentiments.items():
            speaker_scores = [s.score for s in speaker_sents]
            speaker_metrics[speaker_id] = {
                "average_score": statistics.mean(speaker_scores),
                "consistency": self.get_speaker_sentiment_consistency(speaker_id, entity_id),
                "total_mentions": len(speaker_sents)
            }
        
        return {
            "overall_metrics": {
                "average_score": statistics.mean(scores),
                "average_magnitude": statistics.mean(magnitudes),
                "volatility": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "trend": self.get_sentiment_trend(entity_id, window_days),
                "total_mentions": len(sentiments)
            },
            "speaker_metrics": speaker_metrics,
            "time_window": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": window_days
            }
        }
    
    def detect_sentiment_shifts(
        self,
        entity_id: str,
        min_magnitude: float = 0.5,
        window_days: int = 30
    ) -> List[Dict]:
        """Detect significant shifts in sentiment towards an entity."""
        shifts = []
        sentiments = self.get_sentiment_history(entity_id)
        
        if len(sentiments) < 2:
            return shifts
        
        # Sort sentiments by timestamp
        sentiments.sort(key=lambda x: x.timestamp)
        
        # Use a sliding window to detect shifts
        for i in range(len(sentiments) - 1):
            current = sentiments[i]
            next_sentiment = sentiments[i + 1]
            
            # Calculate the magnitude of change
            score_change = abs(next_sentiment.score - current.score)
            time_diff = (next_sentiment.timestamp - current.timestamp).days
            
            if score_change >= min_magnitude and time_diff <= window_days:
                shifts.append({
                    "timestamp": next_sentiment.timestamp.isoformat(),
                    "previous_score": current.score,
                    "new_score": next_sentiment.score,
                    "change_magnitude": score_change,
                    "days_since_previous": time_diff,
                    "speaker_id": next_sentiment.speaker_id,
                    "context": next_sentiment.context
                })
        
        return shifts
    
    def get_correlated_sentiment(
        self,
        entity1_id: str,
        entity2_id: str,
        window_days: int = 90
    ) -> float:
        """Calculate the correlation between sentiment towards two entities."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        sentiments1 = self.get_sentiment_history(entity1_id, start_time, end_time)
        sentiments2 = self.get_sentiment_history(entity2_id, start_time, end_time)
        
        if len(sentiments1) < 2 or len(sentiments2) < 2:
            return 0.0
        
        # Align sentiment scores by timestamp
        scores1 = [s.score for s in sentiments1]
        scores2 = [s.score for s in sentiments2]
        
        try:
            correlation = statistics.correlation(scores1, scores2)
            return correlation
        except statistics.StatisticsError:
            return 0.0 