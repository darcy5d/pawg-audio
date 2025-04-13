"""
Core Services Layer

This module provides the core services for feed management, processing pipeline, and analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .config import ConfigManager
from .database import DatabaseManager
from content_analysis import ContentAnalyzer
from trend_detection import (
    EntityTracker,
    SentimentAnalyzer,
    PredictionTracker,
    TrendDetector
)

class FeedManager:
    """Manages podcast feed operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.logger = logging.getLogger(__name__)
        self.db = db_manager
    
    async def fetch_feed(self, feed_url: str) -> Dict[str, Any]:
        """Fetch and parse a podcast feed."""
        # TODO: Implement feed fetching logic
        pass
    
    async def update_feeds(self) -> None:
        """Update all active feeds."""
        feeds = self.db.get_active_feeds()
        for feed in feeds:
            try:
                feed_data = await self.fetch_feed(feed.url)
                # Update feed metadata
                feed.name = feed_data.get("title")
                feed.description = feed_data.get("description")
                feed.last_fetched = datetime.now()
                self.db.get_session().commit()
                
                # Process new episodes
                for episode_data in feed_data.get("episodes", []):
                    if not self.db.get_episode(episode_data["id"]):
                        self.db.add_episode({
                            **episode_data,
                            "feed_id": feed.id
                        })
            except Exception as e:
                self.logger.error(f"Error updating feed {feed.url}: {str(e)}")

class ProcessingPipeline:
    """Manages the processing pipeline for podcast episodes."""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        db_manager: DatabaseManager
    ):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_config()
        self.db = db_manager
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.processing.max_workers
        )
        self.content_analyzer = ContentAnalyzer()
        self.entity_tracker = EntityTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.prediction_tracker = PredictionTracker()
        self.trend_detector = TrendDetector(
            self.entity_tracker,
            self.sentiment_analyzer,
            self.prediction_tracker
        )
    
    async def process_episode(self, episode_id: int) -> None:
        """Process a single episode through the pipeline."""
        episode = self.db.get_episode(episode_id)
        if not episode:
            self.logger.error(f"Episode {episode_id} not found")
            return
        
        try:
            # 1. Content Analysis
            analysis_result = await self.content_analyzer.analyze(episode.transcript)
            
            # 2. Entity Tracking
            for entity in analysis_result.entities:
                self.entity_tracker.add_entity(entity)
                self.db.add_entity({
                    "episode_id": episode.id,
                    "name": entity.name,
                    "type": entity.type.value,
                    "confidence": entity.confidence,
                    "context": entity.context,
                    "metadata": entity.metadata
                })
            
            # 3. Sentiment Analysis
            for sentiment in analysis_result.sentiments:
                self.sentiment_analyzer.add_sentiment(sentiment)
                self.db.add_sentiment({
                    "episode_id": episode.id,
                    "entity_id": sentiment.entity.id,
                    "score": sentiment.score,
                    "magnitude": sentiment.magnitude,
                    "evidence": sentiment.evidence,
                    "confidence": sentiment.confidence
                })
            
            # 4. Prediction Tracking
            for prediction in analysis_result.predictions:
                self.prediction_tracker.add_prediction(prediction)
                self.db.add_prediction({
                    "episode_id": episode.id,
                    "description": prediction.description,
                    "timeframe": prediction.timeframe.value,
                    "confidence": prediction.confidence,
                    "supporting_evidence": prediction.supporting_evidence,
                    "counter_evidence": prediction.counter_evidence
                })
            
            # 5. Trend Detection
            trends = self.trend_detector.detect_emerging_narratives()
            # TODO: Store trends in database
            
            self.logger.info(f"Successfully processed episode {episode_id}")
        except Exception as e:
            self.logger.error(f"Error processing episode {episode_id}: {str(e)}")
    
    async def process_episodes(self, episode_ids: List[int]) -> None:
        """Process multiple episodes in parallel."""
        tasks = [self.process_episode(episode_id) for episode_id in episode_ids]
        await asyncio.gather(*tasks)

class AnalysisService:
    """Provides analysis capabilities for the system."""
    
    def __init__(
        self,
        config_manager: ConfigManager,
        db_manager: DatabaseManager
    ):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_config()
        self.db = db_manager
        self.entity_tracker = EntityTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.prediction_tracker = PredictionTracker()
        self.trend_detector = TrendDetector(
            self.entity_tracker,
            self.sentiment_analyzer,
            self.prediction_tracker
        )
    
    def get_entity_analysis(self, entity_id: int) -> Dict[str, Any]:
        """Get comprehensive analysis for an entity."""
        entity = self.db.get_entity(entity_id)
        if not entity:
            return {}
        
        # Get entity mentions
        mentions = self.entity_tracker.get_mentions(entity_id)
        
        # Get sentiment analysis
        sentiment_summary = self.sentiment_analyzer.get_entity_sentiment_summary(entity_id)
        
        # Get predictions
        predictions = self.prediction_tracker.get_predictions(entity_id=entity_id)
        
        # Get related entities
        related_entities = self.entity_tracker.get_related_entities(entity_id)
        
        return {
            "entity": {
                "id": entity.id,
                "name": entity.name,
                "type": entity.type,
                "confidence": entity.confidence
            },
            "mentions": {
                "total": len(mentions),
                "recent_frequency": self.entity_tracker.get_mention_frequency(entity_id),
                "first_mention": min(m.timestamp for m in mentions) if mentions else None,
                "last_mention": max(m.timestamp for m in mentions) if mentions else None
            },
            "sentiment": sentiment_summary,
            "predictions": [
                {
                    "description": p.description,
                    "timeframe": p.timeframe,
                    "confidence": p.confidence,
                    "outcome": p.outcome
                }
                for p in predictions
            ],
            "related_entities": [
                {
                    "id": e.id,
                    "name": e.name,
                    "type": e.type,
                    "relationship_strength": self.entity_tracker.get_relationship_strength(
                        entity_id,
                        e.id
                    )
                }
                for e in related_entities
            ]
        }
    
    def get_trend_analysis(
        self,
        window_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get trend analysis for the specified time window."""
        window = window_days or self.config.analysis.trend_window_days
        
        # Detect emerging narratives
        trends = self.trend_detector.detect_emerging_narratives(
            window_days=window,
            min_confidence=self.config.analysis.min_confidence
        )
        
        # Get consensus/divergence analysis
        consensus_analysis = {}
        for trend in trends:
            for entity_id in trend.entities:
                consensus = self.trend_detector.detect_consensus_divergence(
                    entity_id,
                    window_days=window
                )
                consensus_analysis[entity_id] = consensus
        
        return {
            "trends": [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "confidence": t.confidence,
                    "strength": t.strength,
                    "entities": t.entities,
                    "evidence": t.evidence
                }
                for t in trends
            ],
            "consensus_analysis": consensus_analysis,
            "time_window": {
                "days": window,
                "start": datetime.now() - timedelta(days=window),
                "end": datetime.now()
            }
        }
    
    def get_prediction_analysis(
        self,
        window_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get prediction analysis for the specified time window."""
        window = window_days or self.config.analysis.prediction_window_days
        
        # Get prediction patterns
        patterns = {}
        for entity_id in self.entity_tracker.entities:
            patterns[entity_id] = self.prediction_tracker.detect_prediction_patterns(
                entity_id,
                window_days=window
            )
        
        # Get leading indicators
        indicators = {}
        for entity_id in self.entity_tracker.entities:
            indicators[entity_id] = self.trend_detector.detect_leading_indicators(
                entity_id,
                window_days=window
            )
        
        return {
            "prediction_patterns": patterns,
            "leading_indicators": indicators,
            "time_window": {
                "days": window,
                "start": datetime.now() - timedelta(days=window),
                "end": datetime.now()
            }
        } 