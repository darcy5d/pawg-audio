#!/usr/bin/env python3
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from database.models import Episode, ProcessingStatus, Speaker, Insight, Entity
from .base_worker import BaseWorker
from ..utils.nlp import (
    extract_speakers,
    identify_topics,
    extract_insights,
    analyze_sentiment,
    extract_entities
)

logger = logging.getLogger(__name__)

class AnalyzeWorker(BaseWorker):
    """Worker for analyzing podcast episode transcripts."""
    
    async def _process_episode(self, episode: Episode) -> bool:
        """
        Analyze an episode's transcript.
        
        Args:
            episode: Episode to analyze
            
        Returns:
            bool: True if analysis was successful
        """
        if not episode.processing_status.is_transcribed:
            logger.error(f"Episode {episode.id} not transcribed yet")
            return False
        
        try:
            # Load transcript
            with open(episode.processing_status.transcript_path, 'r') as f:
                transcript = json.load(f)
            
            # Extract and process speakers
            speakers = await self._process_speakers(episode, transcript)
            
            # Process transcript segments
            total_segments = len(transcript['segments'])
            for i, segment in enumerate(transcript['segments']):
                # Identify speaker for this segment
                speaker_id = await self._identify_segment_speaker(segment, speakers)
                
                # Extract insights from segment
                await self._process_segment(episode, segment, speaker_id)
                
                # Update progress
                progress = ((i + 1) / total_segments) * 100
                logger.debug(f"Analysis progress for episode {episode.id}: {progress:.1f}%")
            
            # Extract and process entities
            await self._process_entities(episode, transcript)
            
            # Update episode status
            episode.processing_status.is_analyzed = True
            
            # Update metrics
            self.metrics.increment('analyses_completed')
            self.metrics.update({
                'last_analysis_segments': total_segments,
                'total_analysis_segments': self.metrics.get('total_analysis_segments', 0) + total_segments
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error analyzing episode {episode.id}: {str(e)}")
            raise
    
    async def _process_speakers(self, episode: Episode, transcript: Dict) -> Dict[str, int]:
        """
        Process and identify speakers in the transcript.
        
        Args:
            episode: Episode being analyzed
            transcript: Transcript data
            
        Returns:
            Dict[str, int]: Mapping of speaker names to IDs
        """
        # Extract speakers from transcript
        speakers = await extract_speakers(transcript)
        speaker_map = {}
        
        for speaker_name in speakers:
            # Check if speaker already exists
            speaker = self.session.query(Speaker).filter(Speaker.name == speaker_name).first()
            
            if not speaker:
                # Create new speaker
                speaker = Speaker(
                    name=speaker_name,
                    role='Unknown',  # Could be enhanced with role detection
                    created_at=datetime.utcnow()
                )
                self.session.add(speaker)
                self.session.flush()  # Get speaker ID
            
            speaker_map[speaker_name] = speaker.id
            
            # Add speaker to episode if not already present
            if speaker not in episode.speakers:
                episode.speakers.append(speaker)
        
        return speaker_map
    
    async def _identify_segment_speaker(self, segment: Dict, speakers: Dict[str, int]) -> Optional[int]:
        """
        Identify the speaker for a transcript segment.
        
        Args:
            segment: Transcript segment
            speakers: Mapping of speaker names to IDs
            
        Returns:
            Optional[int]: Speaker ID if identified
        """
        # This is a placeholder. Implement more sophisticated speaker identification here.
        # Could use speaker diarization results if available
        return None
    
    async def _process_segment(self, episode: Episode, segment: Dict, speaker_id: Optional[int]):
        """
        Process a transcript segment to extract insights.
        
        Args:
            episode: Episode being analyzed
            segment: Transcript segment
            speaker_id: ID of the speaker (if identified)
        """
        # Extract topics and insights
        topics = await identify_topics(segment['text'])
        insights = await extract_insights(segment['text'])
        sentiment = await analyze_sentiment(segment['text'])
        
        # Create insight records
        for insight_data in insights:
            insight = Insight(
                episode_id=episode.id,
                speaker_id=speaker_id,
                insight_type=insight_data['type'],
                content=insight_data['content'],
                confidence=insight_data['confidence'],
                timeframe=insight_data.get('timeframe'),
                reference_date=insight_data.get('reference_date'),
                start_timestamp=segment['start'],
                end_timestamp=segment['end'],
                sentiment_score=sentiment['score'],
                conviction_level=sentiment['conviction'],
                created_at=datetime.utcnow()
            )
            self.session.add(insight)
    
    async def _process_entities(self, episode: Episode, transcript: Dict):
        """
        Extract and process entities from the transcript.
        
        Args:
            episode: Episode being analyzed
            transcript: Transcript data
        """
        # Extract entities from full transcript
        entities = await extract_entities(transcript['text'])
        
        for entity_data in entities:
            # Check if entity already exists
            entity = self.session.query(Entity).filter(
                Entity.name == entity_data['name'],
                Entity.type == entity_data['type']
            ).first()
            
            if not entity:
                # Create new entity
                entity = Entity(
                    name=entity_data['name'],
                    type=entity_data['type'],
                    description=entity_data.get('description'),
                    aliases=entity_data.get('aliases'),
                    created_at=datetime.utcnow()
                )
                self.session.add(entity)
                self.session.flush()  # Get entity ID
            
            # Create entity mention for each insight that mentions this entity
            for mention in entity_data['mentions']:
                insight = self.session.query(Insight).filter(
                    Insight.episode_id == episode.id,
                    Insight.start_timestamp <= mention['timestamp'],
                    Insight.end_timestamp >= mention['timestamp']
                ).first()
                
                if insight and entity not in insight.entities:
                    insight.entities.append(entity)
    
    def _update_start_time(self, status: ProcessingStatus):
        """Update analysis start time."""
        status.analysis_started_at = datetime.utcnow()
    
    def _update_completion_time(self, status: ProcessingStatus):
        """Update analysis completion time."""
        status.analysis_completed_at = datetime.utcnow() 