#!/usr/bin/env python3
import os
import json
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from database.models import Episode, ProcessingStatus
from .base_worker import BaseWorker
from ..utils.audio import convert_to_mp3, split_audio
from ..config.settings import TRANSCRIPTS_DIR

logger = logging.getLogger(__name__)

class TranscribeWorker(BaseWorker):
    """Worker for transcribing podcast episodes using Whisper API."""
    
    def __init__(self, *args, use_api: bool = True, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the transcription worker.
        
        Args:
            use_api: Whether to use the Whisper API (True) or local model (False)
            api_key: OpenAI API key for Whisper API
            *args, **kwargs: Arguments passed to BaseWorker
        """
        super().__init__(*args, **kwargs)
        self.use_api = use_api
        self.api_key = api_key
        
        if use_api and not api_key:
            raise ValueError("API key required when use_api is True")
    
    async def _process_episode(self, episode: Episode) -> bool:
        """
        Transcribe an episode's audio file.
        
        Args:
            episode: Episode to transcribe
            
        Returns:
            bool: True if transcription was successful
        """
        if not episode.processing_status.is_downloaded:
            logger.error(f"Episode {episode.id} not downloaded yet")
            return False
        
        # Create transcripts directory
        feed_dir = os.path.join(TRANSCRIPTS_DIR, str(episode.feed_id))
        os.makedirs(feed_dir, exist_ok=True)
        
        # Prepare output paths
        transcript_path = os.path.join(feed_dir, f"{episode.id}_transcript.json")
        audio_path = episode.processing_status.download_path
        
        try:
            # Convert audio to MP3 if needed
            if not audio_path.endswith('.mp3'):
                audio_path = await convert_to_mp3(audio_path)
            
            # Split audio if it's too long (Whisper API has a 25MB limit)
            audio_segments = await split_audio(audio_path, max_size_mb=25)
            
            # Process each segment
            transcripts = []
            for i, segment_path in enumerate(audio_segments):
                if self.use_api:
                    segment_transcript = await self._transcribe_with_api(segment_path)
                else:
                    segment_transcript = await self._transcribe_locally(segment_path)
                
                transcripts.append(segment_transcript)
                
                # Update progress
                progress = ((i + 1) / len(audio_segments)) * 100
                logger.debug(f"Transcription progress for episode {episode.id}: {progress:.1f}%")
            
            # Combine transcripts
            combined_transcript = self._combine_transcripts(transcripts)
            
            # Save transcript
            with open(transcript_path, 'w') as f:
                json.dump(combined_transcript, f, indent=2)
            
            # Update episode status
            episode.processing_status.is_transcribed = True
            episode.processing_status.transcript_path = transcript_path
            
            # Update metrics
            self.metrics.increment('transcriptions_completed')
            self.metrics.update({
                'last_transcription_duration': episode.duration,
                'total_transcription_duration': self.metrics.get('total_transcription_duration', 0) + episode.duration
            })
            
            # Cleanup temporary files
            for segment_path in audio_segments:
                if segment_path != audio_path:  # Don't delete the original file
                    os.remove(segment_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error transcribing episode {episode.id}: {str(e)}")
            if os.path.exists(transcript_path):
                os.remove(transcript_path)
            raise
    
    async def _transcribe_with_api(self, audio_path: str) -> Dict:
        """
        Transcribe audio using the Whisper API.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict: Transcription result
        """
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with aiohttp.ClientSession() as session:
            with open(audio_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f)
                form.add_field('model', 'whisper-1')
                form.add_field('response_format', 'verbose_json')
                form.add_field('timestamp_granularities', ['word', 'segment'])
                
                async with session.post(url, headers=headers, data=form) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise Exception(f"Whisper API error: {error}")
                    
                    return await response.json()
    
    async def _transcribe_locally(self, audio_path: str) -> Dict:
        """
        Transcribe audio using local Whisper model.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict: Transcription result
        """
        # This is a placeholder. Implement local Whisper model processing here.
        raise NotImplementedError("Local transcription not implemented yet")
    
    def _combine_transcripts(self, transcripts: List[Dict]) -> Dict:
        """
        Combine multiple transcript segments into one.
        
        Args:
            transcripts: List of transcript segments
            
        Returns:
            Dict: Combined transcript
        """
        if not transcripts:
            return {}
        
        combined = transcripts[0].copy()
        
        # Combine segments and adjust timestamps
        offset = 0
        for i, transcript in enumerate(transcripts[1:], 1):
            # Add duration of previous segment to offset
            offset += transcripts[i-1]['duration']
            
            # Adjust timestamps in segments
            for segment in transcript['segments']:
                segment['start'] += offset
                segment['end'] += offset
                for word in segment.get('words', []):
                    word['start'] += offset
                    word['end'] += offset
            
            # Append segments
            combined['segments'].extend(transcript['segments'])
        
        # Update total duration
        combined['duration'] = sum(t['duration'] for t in transcripts)
        
        # Update text
        combined['text'] = ' '.join(t['text'].strip() for t in transcripts)
        
        return combined
    
    def _update_start_time(self, status: ProcessingStatus):
        """Update transcription start time."""
        status.transcription_started_at = datetime.utcnow()
    
    def _update_completion_time(self, status: ProcessingStatus):
        """Update transcription completion time."""
        status.transcription_completed_at = datetime.utcnow() 