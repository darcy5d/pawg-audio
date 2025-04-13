"""
Entity Tracker Module

This module provides functionality for tracking entities and their relationships across podcast episodes.
"""

from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
from .models import (
    Entity,
    EntityType,
    EntityMention,
    EntityRelationship,
    RelationshipType
)

class EntityTracker:
    """Tracks entities and their relationships across podcast episodes."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.entities: Dict[str, Entity] = {}
        self.mentions: Dict[str, List[EntityMention]] = {}
        self.relationships: Dict[Tuple[str, str], EntityRelationship] = {}
        self.entity_aliases: Dict[str, str] = {}  # Maps aliases to entity IDs
    
    def add_entity(self, entity: Entity) -> None:
        """Add a new entity to the tracker."""
        self.entities[entity.id] = entity
        for alias in entity.aliases:
            self.entity_aliases[alias.lower()] = entity.id
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by its ID."""
        return self.entities.get(entity_id)
    
    def find_entity_by_name(self, name: str) -> Optional[Entity]:
        """Find an entity by its name or alias."""
        entity_id = self.entity_aliases.get(name.lower())
        if entity_id:
            return self.entities.get(entity_id)
        return None
    
    def add_mention(self, mention: EntityMention) -> None:
        """Add a new entity mention."""
        if mention.entity_id not in self.mentions:
            self.mentions[mention.entity_id] = []
        self.mentions[mention.entity_id].append(mention)
    
    def get_mentions(
        self,
        entity_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[EntityMention]:
        """Get mentions of an entity within a time range."""
        mentions = self.mentions.get(entity_id, [])
        if start_time:
            mentions = [m for m in mentions if m.timestamp >= start_time]
        if end_time:
            mentions = [m for m in mentions if m.timestamp <= end_time]
        return mentions
    
    def add_relationship(self, relationship: EntityRelationship) -> None:
        """Add a new relationship between entities."""
        key = (min(relationship.entity1_id, relationship.entity2_id),
               max(relationship.entity1_id, relationship.entity2_id))
        self.relationships[key] = relationship
    
    def get_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[EntityRelationship]:
        """Get relationships for an entity, optionally filtered by type."""
        relationships = []
        for (e1, e2), rel in self.relationships.items():
            if entity_id in (e1, e2):
                if relationship_type is None or rel.relationship_type == relationship_type:
                    relationships.append(rel)
        return relationships
    
    def get_related_entities(
        self,
        entity_id: str,
        relationship_type: Optional[RelationshipType] = None
    ) -> List[Entity]:
        """Get entities related to a given entity."""
        related_entities = []
        for rel in self.get_relationships(entity_id, relationship_type):
            related_id = rel.entity2_id if rel.entity1_id == entity_id else rel.entity1_id
            if entity := self.get_entity(related_id):
                related_entities.append(entity)
        return related_entities
    
    def get_mention_frequency(
        self,
        entity_id: str,
        window_days: int = 30
    ) -> float:
        """Calculate the frequency of mentions for an entity in a time window."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=window_days)
        mentions = self.get_mentions(entity_id, start_time, end_time)
        return len(mentions) / window_days
    
    def get_relationship_strength(
        self,
        entity1_id: str,
        entity2_id: str
    ) -> float:
        """Get the strength of the relationship between two entities."""
        key = (min(entity1_id, entity2_id), max(entity1_id, entity2_id))
        if relationship := self.relationships.get(key):
            return relationship.strength
        return 0.0
    
    def get_entity_network(
        self,
        entity_id: str,
        max_depth: int = 2
    ) -> Dict[str, List[Entity]]:
        """Get the network of entities connected to a given entity."""
        network = {}
        visited = set()
        
        def explore_network(current_id: str, depth: int) -> None:
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            if depth not in network:
                network[depth] = []
            
            for rel in self.get_relationships(current_id):
                related_id = rel.entity2_id if rel.entity1_id == current_id else rel.entity1_id
                if entity := self.get_entity(related_id):
                    network[depth].append(entity)
                    explore_network(related_id, depth + 1)
        
        explore_network(entity_id, 0)
        return network
    
    def get_entity_timeline(
        self,
        entity_id: str
    ) -> List[Tuple[datetime, str]]:
        """Get a timeline of events for an entity."""
        timeline = []
        
        # Add mentions
        for mention in self.get_mentions(entity_id):
            timeline.append((mention.timestamp, f"Mentioned in episode {mention.episode_id}"))
        
        # Add relationships
        for rel in self.get_relationships(entity_id):
            timeline.append((rel.first_observed, f"Relationship established: {rel.relationship_type.value}"))
            if rel.last_observed != rel.first_observed:
                timeline.append((rel.last_observed, f"Relationship updated: {rel.relationship_type.value}"))
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x[0])
        return timeline
    
    def get_entity_summary(self, entity_id: str) -> Dict:
        """Get a summary of an entity's presence in the podcast corpus."""
        entity = self.get_entity(entity_id)
        if not entity:
            return {}
        
        mentions = self.get_mentions(entity_id)
        relationships = self.get_relationships(entity_id)
        
        return {
            "entity": {
                "id": entity.id,
                "name": entity.name,
                "type": entity.type.value,
                "aliases": list(entity.aliases)
            },
            "mention_stats": {
                "total_mentions": len(mentions),
                "recent_frequency": self.get_mention_frequency(entity_id),
                "first_mention": min(m.timestamp for m in mentions) if mentions else None,
                "last_mention": max(m.timestamp for m in mentions) if mentions else None
            },
            "relationship_stats": {
                "total_relationships": len(relationships),
                "relationship_types": {
                    rt.value: len([r for r in relationships if r.relationship_type == rt])
                    for rt in RelationshipType
                }
            }
        } 