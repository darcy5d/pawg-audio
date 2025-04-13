"""
Content Analysis Models

This module defines the data structures for storing and managing content analysis results.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from datetime import datetime
from enum import Enum

class Timeframe(Enum):
    """Enumeration of prediction timeframes."""
    SHORT_TERM = "0-6 months"
    MEDIUM_TERM = "6-18 months"
    LONG_TERM = "18+ months"

class Domain(Enum):
    """Enumeration of analysis domains."""
    FINANCIAL = "financial"
    GEOPOLITICAL = "geopolitical"
    TECHNOLOGY = "technology"
    GENERAL = "general"

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

@dataclass
class Entity:
    """Represents an entity mentioned in the content."""
    name: str
    type: EntityType
    aliases: Set[str] = field(default_factory=set)
    metadata: Dict = field(default_factory=dict)
    confidence: float = 1.0

@dataclass
class Sentiment:
    """Represents sentiment analysis for an entity or topic."""
    entity: Entity
    score: float  # -1.0 to 1.0
    magnitude: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    context: str = ""
    confidence: float = 1.0

@dataclass
class Prediction:
    """Represents a prediction made in the content."""
    description: str
    timeframe: Timeframe
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    counter_evidence: List[str] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    domain: Domain = Domain.GENERAL

@dataclass
class Relationship:
    """Represents a relationship between entities."""
    entity1: Entity
    entity2: Entity
    relationship_type: str
    description: str
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class Insight:
    """Represents a structured insight extracted from the content."""
    id: str
    content: str
    domain: Domain
    entities: List[Entity] = field(default_factory=list)
    predictions: List[Prediction] = field(default_factory=list)
    sentiments: List[Sentiment] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    counter_arguments: List[str] = field(default_factory=list)
    confidence: float = 1.0
    requires_review: bool = False
    review_notes: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert the insight to a dictionary for storage."""
        return {
            "id": self.id,
            "content": self.content,
            "domain": self.domain.value,
            "entities": [
                {
                    "name": e.name,
                    "type": e.type.value,
                    "aliases": list(e.aliases),
                    "metadata": e.metadata,
                    "confidence": e.confidence
                }
                for e in self.entities
            ],
            "predictions": [
                {
                    "description": p.description,
                    "timeframe": p.timeframe.value,
                    "confidence": p.confidence,
                    "supporting_evidence": p.supporting_evidence,
                    "counter_evidence": p.counter_evidence,
                    "entities": [
                        {
                            "name": e.name,
                            "type": e.type.value,
                            "aliases": list(e.aliases)
                        }
                        for e in p.entities
                    ],
                    "domain": p.domain.value
                }
                for p in self.predictions
            ],
            "sentiments": [
                {
                    "entity": {
                        "name": s.entity.name,
                        "type": s.entity.type.value,
                        "aliases": list(s.entity.aliases)
                    },
                    "score": s.score,
                    "magnitude": s.magnitude,
                    "evidence": s.evidence,
                    "context": s.context,
                    "confidence": s.confidence
                }
                for s in self.sentiments
            ],
            "relationships": [
                {
                    "entity1": {
                        "name": r.entity1.name,
                        "type": r.entity1.type.value,
                        "aliases": list(r.entity1.aliases)
                    },
                    "entity2": {
                        "name": r.entity2.name,
                        "type": r.entity2.type.value,
                        "aliases": list(r.entity2.aliases)
                    },
                    "relationship_type": r.relationship_type,
                    "description": r.description,
                    "evidence": r.evidence,
                    "confidence": r.confidence
                }
                for r in self.relationships
            ],
            "supporting_evidence": self.supporting_evidence,
            "counter_arguments": self.counter_arguments,
            "confidence": self.confidence,
            "requires_review": self.requires_review,
            "review_notes": self.review_notes,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Insight':
        """Create an insight from a dictionary."""
        return cls(
            id=data["id"],
            content=data["content"],
            domain=Domain(data["domain"]),
            entities=[
                Entity(
                    name=e["name"],
                    type=EntityType(e["type"]),
                    aliases=set(e["aliases"]),
                    metadata=e["metadata"],
                    confidence=e["confidence"]
                )
                for e in data["entities"]
            ],
            predictions=[
                Prediction(
                    description=p["description"],
                    timeframe=Timeframe(p["timeframe"]),
                    confidence=p["confidence"],
                    supporting_evidence=p["supporting_evidence"],
                    counter_evidence=p["counter_evidence"],
                    entities=[
                        Entity(
                            name=e["name"],
                            type=EntityType(e["type"]),
                            aliases=set(e["aliases"])
                        )
                        for e in p["entities"]
                    ],
                    domain=Domain(p["domain"])
                )
                for p in data["predictions"]
            ],
            sentiments=[
                Sentiment(
                    entity=Entity(
                        name=s["entity"]["name"],
                        type=EntityType(s["entity"]["type"]),
                        aliases=set(s["entity"]["aliases"])
                    ),
                    score=s["score"],
                    magnitude=s["magnitude"],
                    evidence=s["evidence"],
                    context=s["context"],
                    confidence=s["confidence"]
                )
                for s in data["sentiments"]
            ],
            relationships=[
                Relationship(
                    entity1=Entity(
                        name=r["entity1"]["name"],
                        type=EntityType(r["entity1"]["type"]),
                        aliases=set(r["entity1"]["aliases"])
                    ),
                    entity2=Entity(
                        name=r["entity2"]["name"],
                        type=EntityType(r["entity2"]["type"]),
                        aliases=set(r["entity2"]["aliases"])
                    ),
                    relationship_type=r["relationship_type"],
                    description=r["description"],
                    evidence=r["evidence"],
                    confidence=r["confidence"]
                )
                for r in data["relationships"]
            ],
            supporting_evidence=data["supporting_evidence"],
            counter_arguments=data["counter_arguments"],
            confidence=data["confidence"],
            requires_review=data["requires_review"],
            review_notes=data["review_notes"],
            metadata=data["metadata"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        ) 