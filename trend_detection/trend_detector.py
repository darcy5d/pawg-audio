"""
Trend Detector Module

This module provides functionality for detecting patterns and emerging themes across podcast episodes.
"""

from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
import statistics
from collections import defaultdict
from .models import (
    Entity,
    EntityMention,
    SentimentAnalysis,
    Prediction,
    Trend,
    SpeakerProfile
)
from .entity_tracker import EntityTracker
from .sentiment_analyzer import SentimentAnalyzer
from .prediction_tracker import PredictionTracker

class TrendDetector:
    """Detects patterns and emerging themes across podcast episodes."""
    
    def __init__(
        self,
        entity_tracker: EntityTracker,
        sentiment_analyzer: SentimentAnalyzer,
        prediction_tracker: PredictionTracker
    ):
        self.logger = logging.getLogger(__name__)
        self.entity_tracker = entity_tracker
        self.sentiment_analyzer = sentiment_analyzer
        self.prediction_tracker = prediction_tracker
        self.trends: Dict[str, Trend] = {}
    
    def detect_emerging_narratives(
        self,
        min_mentions: int = 5,
        window_days: int = 30,
        min_confidence: float = 0.7
    ) -> List[Trend]:
        """Detect emerging narratives based on entity mentions and relationships."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        # Get all entities mentioned in the time window
        mentioned_entities = set()
        for entity_id, mentions in self.entity_tracker.mentions.items():
            recent_mentions = [
                m for m in mentions
                if start_time <= m.timestamp <= end_time
            ]
            if len(recent_mentions) >= min_mentions:
                mentioned_entities.add(entity_id)
        
        # Group entities by relationships
        entity_groups: Dict[str, Set[str]] = defaultdict(set)
        for entity_id in mentioned_entities:
            related_entities = self.entity_tracker.get_related_entities(entity_id)
            for related in related_entities:
                if related.id in mentioned_entities:
                    entity_groups[entity_id].add(related.id)
        
        # Identify clusters of related entities
        clusters = []
        visited = set()
        
        for entity_id in mentioned_entities:
            if entity_id not in visited:
                cluster = set()
                self._explore_cluster(entity_id, entity_groups, visited, cluster)
                if len(cluster) >= 3:  # Minimum cluster size
                    clusters.append(cluster)
        
        # Create trends from clusters
        trends = []
        for cluster in clusters:
            # Calculate cluster metrics
            mention_frequencies = [
                self.entity_tracker.get_mention_frequency(eid, window_days)
                for eid in cluster
            ]
            avg_frequency = statistics.mean(mention_frequencies)
            
            # Get sentiment trends
            sentiment_trends = [
                self.sentiment_analyzer.get_sentiment_trend(eid, window_days)
                for eid in cluster
            ]
            avg_sentiment_trend = statistics.mean(sentiment_trends)
            
            # Get predictions
            predictions = []
            for entity_id in cluster:
                entity_predictions = self.prediction_tracker.get_predictions(
                    entity_id=entity_id,
                    start_time=start_time,
                    end_time=end_time
                )
                predictions.extend(entity_predictions)
            
            # Calculate trend confidence
            confidence = min(1.0, (
                0.4 * (avg_frequency / 2) +  # Normalize frequency
                0.3 * (avg_sentiment_trend + 1) / 2 +  # Normalize sentiment trend
                0.3 * len(predictions) / 10  # Normalize prediction count
            ))
            
            if confidence >= min_confidence:
                trend = Trend(
                    id=f"trend_{len(trends)}",
                    name=f"Emerging Narrative {len(trends) + 1}",
                    description=self._generate_trend_description(cluster, predictions),
                    entities=list(cluster),
                    supporting_episodes=list(set(
                        m.episode_id
                        for eid in cluster
                        for m in self.entity_tracker.get_mentions(eid, start_time, end_time)
                    )),
                    confidence=confidence,
                    first_observed=start_time,
                    last_observed=end_time,
                    strength=avg_frequency,
                    evidence=self._collect_trend_evidence(cluster, predictions)
                )
                trends.append(trend)
        
        return trends
    
    def detect_consensus_divergence(
        self,
        entity_id: str,
        min_confidence: float = 0.7,
        window_days: int = 30
    ) -> Dict:
        """Detect consensus or divergence in opinions about an entity."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        # Get sentiment analyses
        sentiments = self.sentiment_analyzer.get_sentiment_history(
            entity_id,
            start_time,
            end_time
        )
        
        # Get predictions
        predictions = self.prediction_tracker.get_predictions(
            entity_id=entity_id,
            start_time=start_time,
            end_time=end_time
        )
        
        # Group by speaker
        speaker_sentiments: Dict[str, List[SentimentAnalysis]] = defaultdict(list)
        for sentiment in sentiments:
            speaker_sentiments[sentiment.speaker_id].append(sentiment)
        
        speaker_predictions: Dict[str, List[Prediction]] = defaultdict(list)
        for prediction in predictions:
            speaker_predictions[prediction.speaker_id].append(prediction)
        
        # Calculate consensus metrics
        sentiment_scores = [s.score for s in sentiments]
        sentiment_consensus = 1.0 - statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 1.0
        
        prediction_confidences = [p.confidence for p in predictions]
        prediction_consensus = 1.0 - statistics.stdev(prediction_confidences) if len(prediction_confidences) > 1 else 1.0
        
        # Identify contrarian viewpoints
        contrarian_speakers = []
        for speaker_id, speaker_sents in speaker_sentiments.items():
            speaker_scores = [s.score for s in speaker_sents]
            avg_score = statistics.mean(speaker_scores)
            
            # A speaker is contrarian if their average sentiment differs significantly
            # from the overall average and they have strong evidence
            if abs(avg_score - statistics.mean(sentiment_scores)) > 0.5:
                contrarian_speakers.append({
                    "speaker_id": speaker_id,
                    "average_sentiment": avg_score,
                    "evidence": [s.evidence for s in speaker_sents],
                    "predictions": [
                        {
                            "description": p.description,
                            "confidence": p.confidence
                        }
                        for p in speaker_predictions.get(speaker_id, [])
                    ]
                })
        
        return {
            "sentiment_consensus": sentiment_consensus,
            "prediction_consensus": prediction_consensus,
            "overall_consensus": (sentiment_consensus + prediction_consensus) / 2,
            "contrarian_speakers": contrarian_speakers,
            "time_window": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "days": window_days
            }
        }
    
    def detect_leading_indicators(
        self,
        entity_id: str,
        min_confidence: float = 0.7,
        window_days: int = 90
    ) -> List[Dict]:
        """Detect potential leading indicators for market or geopolitical shifts."""
        indicators = []
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        
        # Get entity's network
        network = self.entity_tracker.get_entity_network(entity_id)
        
        # Analyze each level of the network
        for depth, entities in network.items():
            for entity in entities:
                # Check sentiment correlation
                sentiment_correlation = self.sentiment_analyzer.get_correlated_sentiment(
                    entity_id,
                    entity.id,
                    window_days
                )
                
                # Check prediction patterns
                predictions = self.prediction_tracker.get_predictions(
                    entity_id=entity.id,
                    start_time=start_time,
                    end_time=end_time
                )
                
                # Calculate indicator strength
                strength = (
                    0.6 * abs(sentiment_correlation) +
                    0.4 * len(predictions) / 10
                )
                
                if strength >= min_confidence:
                    indicators.append({
                        "entity": {
                            "id": entity.id,
                            "name": entity.name,
                            "type": entity.type.value
                        },
                        "network_depth": depth,
                        "sentiment_correlation": sentiment_correlation,
                        "prediction_count": len(predictions),
                        "strength": strength,
                        "evidence": self._collect_indicator_evidence(entity.id, predictions)
                    })
        
        # Sort by strength
        indicators.sort(key=lambda x: x["strength"], reverse=True)
        return indicators
    
    def _explore_cluster(
        self,
        entity_id: str,
        entity_groups: Dict[str, Set[str]],
        visited: Set[str],
        cluster: Set[str]
    ) -> None:
        """Recursively explore a cluster of related entities."""
        if entity_id in visited:
            return
        
        visited.add(entity_id)
        cluster.add(entity_id)
        
        for related_id in entity_groups[entity_id]:
            self._explore_cluster(related_id, entity_groups, visited, cluster)
    
    def _generate_trend_description(
        self,
        cluster: Set[str],
        predictions: List[Prediction]
    ) -> str:
        """Generate a description for a detected trend."""
        entities = [self.entity_tracker.get_entity(eid) for eid in cluster]
        entity_names = [e.name for e in entities if e]
        
        # Group predictions by timeframe
        timeframe_predictions: Dict[str, List[Prediction]] = defaultdict(list)
        for prediction in predictions:
            timeframe_predictions[prediction.timeframe.value].append(prediction)
        
        description = f"Emerging narrative involving {', '.join(entity_names)}. "
        
        # Add prediction context
        for timeframe, preds in timeframe_predictions.items():
            if preds:
                description += f"In the {timeframe}, key predictions include: "
                description += "; ".join(p.description for p in preds[:3])
                if len(preds) > 3:
                    description += f" (and {len(preds) - 3} more)"
                description += ". "
        
        return description.strip()
    
    def _collect_trend_evidence(
        self,
        cluster: Set[str],
        predictions: List[Prediction]
    ) -> List[str]:
        """Collect evidence supporting a detected trend."""
        evidence = []
        
        # Add entity relationship evidence
        for entity_id in cluster:
            relationships = self.entity_tracker.get_relationships(entity_id)
            for rel in relationships:
                if rel.entity1_id in cluster and rel.entity2_id in cluster:
                    evidence.append(
                        f"Relationship between {self.entity_tracker.get_entity(rel.entity1_id).name} "
                        f"and {self.entity_tracker.get_entity(rel.entity2_id).name}: "
                        f"{rel.relationship_type.value}"
                    )
        
        # Add prediction evidence
        for prediction in predictions:
            evidence.append(
                f"Prediction by speaker {prediction.speaker_id}: {prediction.description} "
                f"(confidence: {prediction.confidence})"
            )
        
        return evidence
    
    def _collect_indicator_evidence(
        self,
        entity_id: str,
        predictions: List[Prediction]
    ) -> List[str]:
        """Collect evidence for a potential leading indicator."""
        evidence = []
        
        # Add sentiment evidence
        sentiments = self.sentiment_analyzer.get_sentiment_history(entity_id)
        if sentiments:
            avg_sentiment = statistics.mean(s.score for s in sentiments)
            evidence.append(
                f"Average sentiment: {avg_sentiment:.2f} "
                f"(based on {len(sentiments)} analyses)"
            )
        
        # Add prediction evidence
        for prediction in predictions:
            evidence.append(
                f"Prediction: {prediction.description} "
                f"(confidence: {prediction.confidence})"
            )
        
        return evidence 