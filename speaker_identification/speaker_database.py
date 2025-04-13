"""
Speaker Database Module

This module provides functionality for storing and managing speaker information,
including recurring speakers, their roles, expertise, and appearances across episodes.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path

@dataclass
class SpeakerProfile:
    """Represents a speaker's profile with their information and history."""
    name: str
    aliases: Set[str]
    organization: Optional[str] = None
    role: Optional[str] = None
    expertise: Set[str] = None
    first_seen: datetime = None
    last_seen: datetime = None
    episode_count: int = 0
    confidence_score: float = 0.0
    metadata: Dict = None

    def __post_init__(self):
        if self.expertise is None:
            self.expertise = set()
        if self.aliases is None:
            self.aliases = set()
        if self.metadata is None:
            self.metadata = {}

class SpeakerDatabase:
    """Manages speaker profiles and their appearances across episodes."""
    
    def __init__(self, db_path: str = "speaker_database.json"):
        self.db_path = Path(db_path)
        self.speakers: Dict[str, SpeakerProfile] = {}
        self._load_database()

    def _load_database(self) -> None:
        """Load speaker database from JSON file."""
        if self.db_path.exists():
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for speaker_data in data['speakers']:
                    speaker = SpeakerProfile(
                        name=speaker_data['name'],
                        aliases=set(speaker_data['aliases']),
                        organization=speaker_data.get('organization'),
                        role=speaker_data.get('role'),
                        expertise=set(speaker_data.get('expertise', [])),
                        first_seen=datetime.fromisoformat(speaker_data['first_seen']) if speaker_data.get('first_seen') else None,
                        last_seen=datetime.fromisoformat(speaker_data['last_seen']) if speaker_data.get('last_seen') else None,
                        episode_count=speaker_data.get('episode_count', 0),
                        confidence_score=speaker_data.get('confidence_score', 0.0),
                        metadata=speaker_data.get('metadata', {})
                    )
                    self.speakers[speaker.name] = speaker

    def _save_database(self) -> None:
        """Save speaker database to JSON file."""
        data = {
            'speakers': [
                {
                    'name': speaker.name,
                    'aliases': list(speaker.aliases),
                    'organization': speaker.organization,
                    'role': speaker.role,
                    'expertise': list(speaker.expertise),
                    'first_seen': speaker.first_seen.isoformat() if speaker.first_seen else None,
                    'last_seen': speaker.last_seen.isoformat() if speaker.last_seen else None,
                    'episode_count': speaker.episode_count,
                    'confidence_score': speaker.confidence_score,
                    'metadata': speaker.metadata
                }
                for speaker in self.speakers.values()
            ]
        }
        
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def add_speaker(self, speaker: SpeakerProfile) -> None:
        """Add or update a speaker profile."""
        if speaker.name in self.speakers:
            # Update existing speaker
            existing = self.speakers[speaker.name]
            existing.aliases.update(speaker.aliases)
            existing.expertise.update(speaker.expertise)
            existing.organization = speaker.organization or existing.organization
            existing.role = speaker.role or existing.role
            existing.last_seen = datetime.now()
            existing.episode_count += 1
            existing.confidence_score = max(existing.confidence_score, speaker.confidence_score)
            existing.metadata.update(speaker.metadata)
        else:
            # Add new speaker
            speaker.first_seen = datetime.now()
            speaker.last_seen = datetime.now()
            speaker.episode_count = 1
            self.speakers[speaker.name] = speaker
        
        self._save_database()

    def get_speaker(self, name: str) -> Optional[SpeakerProfile]:
        """Retrieve a speaker profile by name."""
        return self.speakers.get(name)

    def find_speaker_by_alias(self, alias: str) -> Optional[SpeakerProfile]:
        """Find a speaker by any of their aliases."""
        for speaker in self.speakers.values():
            if alias in speaker.aliases:
                return speaker
        return None

    def get_speakers_by_organization(self, organization: str) -> List[SpeakerProfile]:
        """Get all speakers associated with an organization."""
        return [
            speaker for speaker in self.speakers.values()
            if speaker.organization == organization
        ]

    def get_speakers_by_expertise(self, expertise: str) -> List[SpeakerProfile]:
        """Get all speakers with specific expertise."""
        return [
            speaker for speaker in self.speakers.values()
            if expertise in speaker.expertise
        ]

    def update_speaker_confidence(self, name: str, confidence: float) -> None:
        """Update a speaker's confidence score."""
        if name in self.speakers:
            self.speakers[name].confidence_score = confidence
            self._save_database()

    def merge_speakers(self, name1: str, name2: str) -> None:
        """Merge two speaker profiles."""
        if name1 not in self.speakers or name2 not in self.speakers:
            return

        speaker1 = self.speakers[name1]
        speaker2 = self.speakers[name2]

        # Merge profiles
        speaker1.aliases.update(speaker2.aliases)
        speaker1.expertise.update(speaker2.expertise)
        speaker1.organization = speaker1.organization or speaker2.organization
        speaker1.role = speaker1.role or speaker2.role
        speaker1.first_seen = min(speaker1.first_seen, speaker2.first_seen)
        speaker1.last_seen = max(speaker1.last_seen, speaker2.last_seen)
        speaker1.episode_count += speaker2.episode_count
        speaker1.confidence_score = max(speaker1.confidence_score, speaker2.confidence_score)
        speaker1.metadata.update(speaker2.metadata)

        # Remove the merged speaker
        del self.speakers[name2]
        self._save_database() 