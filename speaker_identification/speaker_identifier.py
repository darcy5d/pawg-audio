"""
Speaker Identifier Module

This module provides the main speaker identification functionality,
coordinating between metadata extraction, transcript analysis, and speaker database management.
"""

import json
from typing import Dict, List, Optional, Tuple
import asyncio
from dataclasses import dataclass
import logging
from datetime import datetime

from .speaker_database import SpeakerDatabase, SpeakerProfile
from .transcript_segmenter import TranscriptSegmenter, TranscriptSegment
from .prompts import SpeakerIdentificationPrompts

@dataclass
class IdentificationResult:
    """Represents the result of a speaker identification process."""
    speaker: SpeakerProfile
    confidence: float
    evidence: List[str]
    segment: TranscriptSegment
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SpeakerIdentifier:
    """Main class for speaker identification and management."""
    
    def __init__(
        self,
        db_path: str = "speaker_database.json",
        max_tokens: int = 2000,
        overlap_tokens: int = 200,
        min_segment_tokens: int = 100
    ):
        self.speaker_db = SpeakerDatabase(db_path)
        self.segmenter = TranscriptSegmenter(
            max_tokens=max_tokens,
            overlap_tokens=overlap_tokens,
            min_segment_tokens=min_segment_tokens
        )
        self.prompts = SpeakerIdentificationPrompts()
        self.logger = logging.getLogger(__name__)

    async def identify_speakers_from_metadata(
        self,
        metadata: Dict,
        provider: str = "openai"
    ) -> List[IdentificationResult]:
        """Extract speaker information from episode metadata."""
        prompt = self.prompts.get_metadata_extraction_prompt(metadata)
        
        try:
            # Call appropriate LLM based on provider
            response = await self._call_llm(provider, prompt)
            result = json.loads(response)
            
            identifications = []
            for speaker_data in result.get('speakers', []):
                speaker = SpeakerProfile(
                    name=speaker_data['name'],
                    aliases=set(speaker_data.get('aliases', [])),
                    role=speaker_data.get('role'),
                    organization=speaker_data.get('organization'),
                    expertise=set(speaker_data.get('expertise', [])),
                    confidence_score=speaker_data.get('confidence', 0.0)
                )
                
                identifications.append(IdentificationResult(
                    speaker=speaker,
                    confidence=speaker_data.get('confidence', 0.0),
                    evidence=[f"Extracted from metadata: {speaker_data.get('episode_role', 'Unknown role')}"],
                    segment=None,
                    metadata={'source': 'metadata'}
                ))
            
            return identifications
            
        except Exception as e:
            self.logger.error(f"Error extracting speakers from metadata: {str(e)}")
            return []

    async def identify_speakers_from_transcript(
        self,
        transcript: str,
        provider: str = "openai",
        context: Optional[Dict] = None
    ) -> List[IdentificationResult]:
        """Identify speakers from transcript segments."""
        # Create segments
        segments = self.segmenter.create_segments(transcript)
        segments = self.segmenter.add_context_to_segments(segments)
        segments = self.segmenter.optimize_segments(segments)
        
        identifications = []
        for segment in segments:
            try:
                # Get appropriate prompt for the provider
                prompt = getattr(self.prompts, f"get_{provider}_prompt")(
                    segment.text,
                    segment.context
                )
                
                # Call LLM
                response = await self._call_llm(provider, prompt)
                result = json.loads(response)
                
                # Process speaker identifications
                speakers_data = self._extract_speakers_from_response(result, provider)
                for speaker_data in speakers_data:
                    speaker = SpeakerProfile(
                        name=speaker_data['name'],
                        aliases=set(speaker_data.get('aliases', [])),
                        role=speaker_data.get('role'),
                        organization=speaker_data.get('organization'),
                        expertise=set(speaker_data.get('expertise', [])),
                        confidence_score=speaker_data.get('confidence', 0.0)
                    )
                    
                    identifications.append(IdentificationResult(
                        speaker=speaker,
                        confidence=speaker_data.get('confidence', 0.0),
                        evidence=speaker_data.get('evidence', []),
                        segment=segment,
                        metadata={'source': 'transcript'}
                    ))
                    
            except Exception as e:
                self.logger.error(f"Error processing transcript segment: {str(e)}")
                continue
        
        return identifications

    async def verify_speaker_identity(
        self,
        speaker1: Dict,
        speaker2: Dict,
        provider: str = "openai",
        context: Optional[Dict] = None
    ) -> Tuple[bool, float, Dict]:
        """Verify if two speaker identifications refer to the same person."""
        prompt = self.prompts.get_speaker_verification_prompt(
            speaker1,
            speaker2,
            context
        )
        
        try:
            response = await self._call_llm(provider, prompt)
            result = json.loads(response)
            
            return (
                result['same_person'],
                result['confidence'],
                result.get('merged_profile', {})
            )
            
        except Exception as e:
            self.logger.error(f"Error verifying speaker identity: {str(e)}")
            return False, 0.0, {}

    def _extract_speakers_from_response(
        self,
        response: Dict,
        provider: str
    ) -> List[Dict]:
        """Extract speaker information from LLM response based on provider."""
        if provider == "openai":
            return response.get('speakers', [])
        elif provider == "anthropic":
            return [
                {
                    **speaker['identity'],
                    'confidence': speaker['confidence'],
                    'evidence': speaker['evidence']
                }
                for speaker in response.get('analysis', {}).get('speakers', [])
            ]
        elif provider == "deepseek":
            return [
                {
                    'name': speaker['name'],
                    'aliases': speaker['aliases'],
                    'role': speaker['role'],
                    'organization': speaker['organization'],
                    'expertise': speaker['expertise'],
                    'confidence': speaker['confidence'],
                    'evidence': speaker['evidence']
                }
                for speaker in response.get('speaker_analysis', {}).get('identified_speakers', [])
            ]
        return []

    async def _call_llm(self, provider: str, prompt: str) -> str:
        """Call the appropriate LLM based on provider."""
        # This is a placeholder - implement actual LLM calls based on your setup
        # You would typically use the appropriate API client for each provider
        raise NotImplementedError("LLM calling functionality needs to be implemented")

    async def process_episode(
        self,
        transcript: str,
        metadata: Optional[Dict] = None,
        providers: List[str] = ["openai", "anthropic", "deepseek"]
    ) -> List[SpeakerProfile]:
        """Process an entire episode to identify and track speakers."""
        all_identifications = []
        
        # Extract from metadata if available
        if metadata:
            for provider in providers:
                metadata_ids = await self.identify_speakers_from_metadata(
                    metadata,
                    provider
                )
                all_identifications.extend(metadata_ids)
        
        # Extract from transcript
        for provider in providers:
            transcript_ids = await self.identify_speakers_from_transcript(
                transcript,
                provider
            )
            all_identifications.extend(transcript_ids)
        
        # Process and merge identifications
        final_speakers = self._process_identifications(all_identifications)
        
        # Update speaker database
        for speaker in final_speakers:
            self.speaker_db.add_speaker(speaker)
        
        return final_speakers

    def _process_identifications(
        self,
        identifications: List[IdentificationResult]
    ) -> List[SpeakerProfile]:
        """Process and merge multiple speaker identifications."""
        # Group by speaker name
        name_groups = {}
        for ident in identifications:
            name = ident.speaker.name
            if name not in name_groups:
                name_groups[name] = []
            name_groups[name].append(ident)
        
        # Process each group
        final_speakers = []
        for name, group in name_groups.items():
            if len(group) == 1:
                # Single identification
                final_speakers.append(group[0].speaker)
            else:
                # Multiple identifications - merge them
                merged_speaker = self._merge_speaker_identifications(group)
                final_speakers.append(merged_speaker)
        
        return final_speakers

    def _merge_speaker_identifications(
        self,
        identifications: List[IdentificationResult]
    ) -> SpeakerProfile:
        """Merge multiple identifications of the same speaker."""
        # Start with the highest confidence identification
        base_ident = max(identifications, key=lambda x: x.confidence)
        merged = base_ident.speaker
        
        # Merge with other identifications
        for ident in identifications:
            if ident != base_ident:
                merged.aliases.update(ident.speaker.aliases)
                merged.expertise.update(ident.speaker.expertise)
                merged.organization = merged.organization or ident.speaker.organization
                merged.role = merged.role or ident.speaker.role
                merged.confidence_score = max(
                    merged.confidence_score,
                    ident.confidence
                )
        
        return merged 