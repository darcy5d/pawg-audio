"""
Trend Detection Models

This module defines the data structures for storing and managing trend detection results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum

class EntityType(Enum):
    """Enumeration of entity types."""
    COMPANY = "company"
    TECHNOLOGY = "technology"
    COUNTRY = "country"
    REGION = "region"
    PERSON = "person"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    MARKET = "market"
    CURRENCY = "currency"
    COMMODITY = "commodity"

class RelationshipType(Enum):
    """Enumeration of relationship types."""
    COMPETITIVE = "competitive"
    COMPLEMENTARY = "complementary"
    CAUSAL = "causal"
    PARTNERSHIP = "partnership"
    INVESTMENT = "investment"
    ACQUISITION = "acquisition"

class Timeframe(Enum):
    """Enumeration of prediction timeframes."""
    SHORT_TERM = "0-6 months"
    MEDIUM_TERM = "6-18 months"
    LONG_TERM = "18+ months"

@dataclass
class Entity:
    """Represents an entity in the trend detection system."""
    id: str
    name: str
    type: EntityType
    aliases: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EntityMention:
    """Represents a mention of an entity in a podcast episode."""
    entity_id: str
    episode_id: str
    timestamp: datetime
    context: str
    speaker_id: str
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)

@dataclass
class EntityRelationship:
    """Represents a relationship between entities."""
    entity1_id: str
    entity2_id: str
    relationship_type: RelationshipType
    strength: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    first_observed: datetime = field(default_factory=datetime.now)
    last_observed: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0

@dataclass
class SentimentAnalysis:
    """Represents sentiment analysis for an entity."""
    entity_id: str
    episode_id: str
    speaker_id: str
    score: float  # -1.0 to 1.0
    magnitude: float  # 0.0 to 1.0
    context: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class Prediction:
    """Represents a prediction made in a podcast episode."""
    id: str
    episode_id: str
    speaker_id: str
    description: str
    timeframe: Timeframe
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    counter_evidence: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)  # List of entity IDs
    created_at: datetime = field(default_factory=datetime.now)
    outcome: Optional[bool] = None
    outcome_observed_at: Optional[datetime] = None
    outcome_evidence: List[str] = field(default_factory=list)

@dataclass
class Trend:
    """Represents a detected trend across podcast episodes."""
    id: str
    name: str
    description: str
    entities: List[str] = field(default_factory=list)  # List of entity IDs
    supporting_episodes: List[str] = field(default_factory=list)
    confidence: float
    first_observed: datetime
    last_observed: datetime
    strength: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

@dataclass
class SpeakerProfile:
    """Represents a speaker's profile and credibility."""
    id: str
    name: str
    expertise: List[str] = field(default_factory=list)
    influence_score: float = 0.0  # 0.0 to 1.0
    prediction_accuracy: float = 0.0  # 0.0 to 1.0
    total_predictions: int = 0
    correct_predictions: int = 0
    sentiment_consistency: float = 0.0  # 0.0 to 1.0
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_prediction_accuracy(self, prediction: Prediction) -> None:
        """Update the speaker's prediction accuracy based on a new prediction outcome."""
        if prediction.outcome is not None:
            self.total_predictions += 1
            if prediction.outcome:
                self.correct_predictions += 1
            self.prediction_accuracy = self.correct_predictions / self.total_predictions
            self.updated_at = datetime.now()

    def update_influence_score(self, new_score: float) -> None:
        """Update the speaker's influence score."""
        self.influence_score = new_score
        self.updated_at = datetime.now()

    def update_sentiment_consistency(self, new_consistency: float) -> None:
        """Update the speaker's sentiment consistency score."""
        self.sentiment_consistency = new_consistency
        self.updated_at = datetime.now() 