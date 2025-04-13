"""
Prediction Tracker Module

This module provides functionality for tracking and analyzing predictions made in podcast episodes.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import statistics
from .models import (
    Prediction,
    Timeframe,
    SpeakerProfile
)

class PredictionTracker:
    """Tracks and analyzes predictions made in podcast episodes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.predictions: Dict[str, Prediction] = {}
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
    
    def add_prediction(self, prediction: Prediction) -> None:
        """Add a new prediction to the tracker."""
        self.predictions[prediction.id] = prediction
        
        # Update speaker profile
        if prediction.speaker_id not in self.speaker_profiles:
            self.speaker_profiles[prediction.speaker_id] = SpeakerProfile(
                id=prediction.speaker_id,
                name="Unknown"  # This should be updated with actual speaker name
            )
    
    def update_prediction_outcome(
        self,
        prediction_id: str,
        outcome: bool,
        evidence: List[str]
    ) -> None:
        """Update the outcome of a prediction."""
        if prediction := self.predictions.get(prediction_id):
            prediction.outcome = outcome
            prediction.outcome_observed_at = datetime.now()
            prediction.outcome_evidence = evidence
            
            # Update speaker's prediction accuracy
            if speaker := self.speaker_profiles.get(prediction.speaker_id):
                speaker.update_prediction_accuracy(prediction)
    
    def get_predictions(
        self,
        speaker_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        timeframe: Optional[Timeframe] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Prediction]:
        """Get predictions matching the specified criteria."""
        predictions = list(self.predictions.values())
        
        if speaker_id:
            predictions = [p for p in predictions if p.speaker_id == speaker_id]
        
        if entity_id:
            predictions = [p for p in predictions if entity_id in p.entities]
        
        if timeframe:
            predictions = [p for p in predictions if p.timeframe == timeframe]
        
        if start_time:
            predictions = [p for p in predictions if p.created_at >= start_time]
        
        if end_time:
            predictions = [p for p in predictions if p.created_at <= end_time]
        
        return predictions
    
    def get_prediction_accuracy(
        self,
        speaker_id: str,
        window_days: int = 365
    ) -> float:
        """Calculate a speaker's prediction accuracy over a time window."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        predictions = self.get_predictions(
            speaker_id=speaker_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Only consider predictions with known outcomes
        predictions = [p for p in predictions if p.outcome is not None]
        
        if not predictions:
            return 0.0
        
        correct_predictions = sum(1 for p in predictions if p.outcome)
        return correct_predictions / len(predictions)
    
    def get_prediction_confidence_distribution(
        self,
        speaker_id: str
    ) -> Dict[str, float]:
        """Get the distribution of prediction confidence levels for a speaker."""
        predictions = self.get_predictions(speaker_id=speaker_id)
        
        if not predictions:
            return {}
        
        confidences = [p.confidence for p in predictions]
        
        return {
            "mean": statistics.mean(confidences),
            "median": statistics.median(confidences),
            "stdev": statistics.stdev(confidences) if len(confidences) > 1 else 0.0,
            "min": min(confidences),
            "max": max(confidences)
        }
    
    def get_timeframe_accuracy(
        self,
        speaker_id: str,
        timeframe: Timeframe
    ) -> float:
        """Calculate a speaker's prediction accuracy for a specific timeframe."""
        predictions = self.get_predictions(
            speaker_id=speaker_id,
            timeframe=timeframe
        )
        
        # Only consider predictions with known outcomes
        predictions = [p for p in predictions if p.outcome is not None]
        
        if not predictions:
            return 0.0
        
        correct_predictions = sum(1 for p in predictions if p.outcome)
        return correct_predictions / len(predictions)
    
    def get_entity_prediction_summary(
        self,
        entity_id: str,
        window_days: int = 90
    ) -> Dict:
        """Get a summary of predictions related to an entity."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        predictions = self.get_predictions(
            entity_id=entity_id,
            start_time=start_time,
            end_time=end_time
        )
        
        if not predictions:
            return {}
        
        # Group predictions by timeframe
        timeframe_predictions: Dict[Timeframe, List[Prediction]] = {}
        for prediction in predictions:
            if prediction.timeframe not in timeframe_predictions:
                timeframe_predictions[prediction.timeframe] = []
            timeframe_predictions[prediction.timeframe].append(prediction)
        
        # Calculate metrics for each timeframe
        timeframe_metrics = {}
        for timeframe, preds in timeframe_predictions.items():
            confidences = [p.confidence for p in preds]
            outcomes = [p.outcome for p in preds if p.outcome is not None]
            
            timeframe_metrics[timeframe.value] = {
                "total_predictions": len(preds),
                "average_confidence": statistics.mean(confidences),
                "outcome_accuracy": (
                    sum(1 for o in outcomes if o) / len(outcomes)
                    if outcomes else None
                )
            }
        
        # Group predictions by speaker
        speaker_predictions: Dict[str, List[Prediction]] = {}
        for prediction in predictions:
            if prediction.speaker_id not in speaker_predictions:
                speaker_predictions[prediction.speaker_id] = []
            speaker_predictions[prediction.speaker_id].append(prediction)
        
        # Calculate speaker-specific metrics
        speaker_metrics = {}
        for speaker_id, preds in speaker_predictions.items():
            confidences = [p.confidence for p in preds]
            outcomes = [p.outcome for p in preds if p.outcome is not None]
            
            speaker_metrics[speaker_id] = {
                "total_predictions": len(preds),
                "average_confidence": statistics.mean(confidences),
                "outcome_accuracy": (
                    sum(1 for o in outcomes if o) / len(outcomes)
                    if outcomes else None
                )
            }
        
        return {
            "timeframe_metrics": timeframe_metrics,
            "speaker_metrics": speaker_metrics,
            "overall_metrics": {
                "total_predictions": len(predictions),
                "average_confidence": statistics.mean([p.confidence for p in predictions]),
                "timeframe_distribution": {
                    tf.value: len(preds)
                    for tf, preds in timeframe_predictions.items()
                }
            },
            "time_window": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": window_days
            }
        }
    
    def detect_prediction_patterns(
        self,
        entity_id: str,
        min_confidence: float = 0.7,
        window_days: int = 30
    ) -> List[Dict]:
        """Detect patterns in predictions about an entity."""
        patterns = []
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        predictions = self.get_predictions(
            entity_id=entity_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Filter by confidence
        predictions = [p for p in predictions if p.confidence >= min_confidence]
        
        if len(predictions) < 2:
            return patterns
        
        # Group predictions by timeframe
        timeframe_groups: Dict[Timeframe, List[Prediction]] = {}
        for prediction in predictions:
            if prediction.timeframe not in timeframe_groups:
                timeframe_groups[prediction.timeframe] = []
            timeframe_groups[prediction.timeframe].append(prediction)
        
        # Analyze each timeframe group
        for timeframe, preds in timeframe_groups.items():
            if len(preds) >= 2:
                # Calculate consensus
                avg_confidence = statistics.mean([p.confidence for p in preds])
                consensus_score = len(preds) * avg_confidence
                
                patterns.append({
                    "timeframe": timeframe.value,
                    "total_predictions": len(preds),
                    "consensus_score": consensus_score,
                    "average_confidence": avg_confidence,
                    "speakers": list(set(p.speaker_id for p in preds)),
                    "predictions": [
                        {
                            "speaker_id": p.speaker_id,
                            "confidence": p.confidence,
                            "description": p.description
                        }
                        for p in preds
                    ]
                })
        
        return patterns
    
    def get_speaker_credibility_score(
        self,
        speaker_id: str,
        window_days: int = 365
    ) -> float:
        """Calculate a comprehensive credibility score for a speaker."""
        if speaker := self.speaker_profiles.get(speaker_id):
            # Get recent prediction accuracy
            recent_accuracy = self.get_prediction_accuracy(speaker_id, window_days)
            
            # Get confidence distribution
            confidence_dist = self.get_prediction_confidence_distribution(speaker_id)
            
            # Calculate credibility score
            # Weight recent accuracy more heavily than historical accuracy
            credibility_score = (
                0.6 * recent_accuracy +
                0.2 * speaker.prediction_accuracy +
                0.2 * (1 - confidence_dist["stdev"])  # Lower standard deviation is better
            )
            
            return credibility_score
        
        return 0.0 