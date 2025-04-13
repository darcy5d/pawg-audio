"""
Insight Validator Module

This module provides functionality for validating and assessing the quality of extracted insights.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json
import logging
from .models import Insight, Entity, Prediction, Relationship, Sentiment

@dataclass
class ValidationResult:
    """Represents the result of insight validation."""
    insight: Insight
    quality_score: float
    completeness_score: float
    consistency_score: float
    requires_review: bool
    validation_notes: List[str]
    suggested_improvements: List[str]

class InsightValidator:
    """Validates and assesses the quality of extracted insights."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_quality_threshold = 0.7
        self.min_completeness_threshold = 0.6
        self.min_consistency_threshold = 0.8
    
    async def validate_insight(self, insight: Insight) -> ValidationResult:
        """Validate an insight and assess its quality."""
        quality_score = self._assess_quality(insight)
        completeness_score = self._assess_completeness(insight)
        consistency_score = self._assess_consistency(insight)
        
        requires_review = (
            quality_score < self.min_quality_threshold or
            completeness_score < self.min_completeness_threshold or
            consistency_score < self.min_consistency_threshold
        )
        
        validation_notes = []
        suggested_improvements = []
        
        if quality_score < self.min_quality_threshold:
            validation_notes.append("Quality score below threshold")
            suggested_improvements.append("Review evidence and confidence levels")
        
        if completeness_score < self.min_completeness_threshold:
            validation_notes.append("Completeness score below threshold")
            suggested_improvements.append("Add missing supporting evidence or counter-arguments")
        
        if consistency_score < self.min_consistency_threshold:
            validation_notes.append("Consistency score below threshold")
            suggested_improvements.append("Review relationships and sentiments for consistency")
        
        return ValidationResult(
            insight=insight,
            quality_score=quality_score,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            requires_review=requires_review,
            validation_notes=validation_notes,
            suggested_improvements=suggested_improvements
        )
    
    def _assess_quality(self, insight: Insight) -> float:
        """Assess the overall quality of an insight."""
        scores = []
        
        # Evidence quality
        if insight.supporting_evidence:
            scores.append(min(1.0, len(insight.supporting_evidence) / 3))
        else:
            scores.append(0.0)
        
        # Entity quality
        if insight.entities:
            scores.append(min(1.0, len(insight.entities) / 5))
        else:
            scores.append(0.0)
        
        # Prediction quality
        if insight.predictions:
            prediction_scores = [
                p.confidence * (1 if p.supporting_evidence else 0.5)
                for p in insight.predictions
            ]
            scores.append(sum(prediction_scores) / len(prediction_scores))
        else:
            scores.append(0.0)
        
        # Relationship quality
        if insight.relationships:
            relationship_scores = [
                r.confidence * (1 if r.evidence else 0.5)
                for r in insight.relationships
            ]
            scores.append(sum(relationship_scores) / len(relationship_scores))
        else:
            scores.append(0.0)
        
        # Sentiment quality
        if insight.sentiments:
            sentiment_scores = [
                s.confidence * (1 if s.evidence else 0.5)
                for s in insight.sentiments
            ]
            scores.append(sum(sentiment_scores) / len(sentiment_scores))
        else:
            scores.append(0.0)
        
        return sum(scores) / len(scores)
    
    def _assess_completeness(self, insight: Insight) -> float:
        """Assess the completeness of an insight."""
        scores = []
        
        # Content completeness
        scores.append(1.0 if insight.content else 0.0)
        
        # Evidence completeness
        scores.append(min(1.0, len(insight.supporting_evidence) / 2))
        scores.append(min(1.0, len(insight.counter_arguments) / 2))
        
        # Entity completeness
        if insight.entities:
            scores.append(min(1.0, len(insight.entities) / 3))
        else:
            scores.append(0.0)
        
        # Prediction completeness
        if insight.predictions:
            prediction_scores = [
                1.0 if p.supporting_evidence and p.timeframe else 0.5
                for p in insight.predictions
            ]
            scores.append(sum(prediction_scores) / len(prediction_scores))
        else:
            scores.append(0.0)
        
        return sum(scores) / len(scores)
    
    def _assess_consistency(self, insight: Insight) -> float:
        """Assess the consistency of an insight."""
        scores = []
        
        # Entity consistency
        if insight.entities:
            entity_scores = []
            for entity in insight.entities:
                # Check if entity appears in predictions
                in_predictions = any(
                    entity in p.entities for p in insight.predictions
                )
                # Check if entity appears in relationships
                in_relationships = any(
                    entity in [r.entity1, r.entity2] for r in insight.relationships
                )
                # Check if entity appears in sentiments
                in_sentiments = any(
                    entity == s.entity for s in insight.sentiments
                )
                
                consistency = sum([
                    1.0 if in_predictions else 0.0,
                    1.0 if in_relationships else 0.0,
                    1.0 if in_sentiments else 0.0
                ]) / 3
                entity_scores.append(consistency)
            
            scores.append(sum(entity_scores) / len(entity_scores))
        else:
            scores.append(0.0)
        
        # Prediction consistency
        if insight.predictions:
            prediction_scores = []
            for prediction in insight.predictions:
                # Check if prediction entities are consistent with insight entities
                entity_consistency = sum(
                    1.0 if e in insight.entities else 0.0
                    for e in prediction.entities
                ) / len(prediction.entities) if prediction.entities else 0.0
                
                # Check if prediction evidence is consistent with insight evidence
                evidence_consistency = sum(
                    1.0 if e in insight.supporting_evidence else 0.0
                    for e in prediction.supporting_evidence
                ) / len(prediction.supporting_evidence) if prediction.supporting_evidence else 0.0
                
                prediction_scores.append(
                    (entity_consistency + evidence_consistency) / 2
                )
            
            scores.append(sum(prediction_scores) / len(prediction_scores))
        else:
            scores.append(0.0)
        
        # Relationship consistency
        if insight.relationships:
            relationship_scores = []
            for relationship in insight.relationships:
                # Check if relationship entities are consistent with insight entities
                entity_consistency = sum(
                    1.0 if e in insight.entities else 0.0
                    for e in [relationship.entity1, relationship.entity2]
                ) / 2
                
                # Check if relationship evidence is consistent with insight evidence
                evidence_consistency = sum(
                    1.0 if e in insight.supporting_evidence else 0.0
                    for e in relationship.evidence
                ) / len(relationship.evidence) if relationship.evidence else 0.0
                
                relationship_scores.append(
                    (entity_consistency + evidence_consistency) / 2
                )
            
            scores.append(sum(relationship_scores) / len(relationship_scores))
        else:
            scores.append(0.0)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    async def validate_batch(
        self,
        insights: List[Insight]
    ) -> List[ValidationResult]:
        """Validate a batch of insights."""
        return [
            await self.validate_insight(insight)
            for insight in insights
        ]
    
    def flag_for_review(
        self,
        validation_results: List[ValidationResult]
    ) -> List[Insight]:
        """Flag insights that require human review."""
        return [
            result.insight
            for result in validation_results
            if result.requires_review
        ]
    
    def get_validation_summary(
        self,
        validation_results: List[ValidationResult]
    ) -> Dict:
        """Get a summary of validation results."""
        total_insights = len(validation_results)
        insights_requiring_review = sum(
            1 for r in validation_results if r.requires_review
        )
        
        avg_quality = sum(r.quality_score for r in validation_results) / total_insights
        avg_completeness = sum(r.completeness_score for r in validation_results) / total_insights
        avg_consistency = sum(r.consistency_score for r in validation_results) / total_insights
        
        return {
            "total_insights": total_insights,
            "insights_requiring_review": insights_requiring_review,
            "average_quality_score": avg_quality,
            "average_completeness_score": avg_completeness,
            "average_consistency_score": avg_consistency,
            "validation_thresholds": {
                "quality": self.min_quality_threshold,
                "completeness": self.min_completeness_threshold,
                "consistency": self.min_consistency_threshold
            }
        } 