#!/usr/bin/env python3
import os
import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from database.models import Episode, ProcessingStatus
from .base_worker import BaseWorker
from ..utils.audio import get_audio_format, optimize_audio
from ..config.settings import DOWNLOAD_DIR

logger = logging.getLogger(__name__)

class DownloadWorker(BaseWorker):
    """Worker for downloading podcast episodes."""
    
    async def _process_episode(self, episode: Episode) -> bool:
        """
        Download and process an episode's audio file.
        
        Args:
            episode: Episode to download
            
        Returns:
            bool: True if download was successful
        """
        # Create download directory if it doesn't exist
        feed_dir = os.path.join(DOWNLOAD_DIR, str(episode.feed_id))
        os.makedirs(feed_dir, exist_ok=True)
        
        # Generate filename
        ext = get_audio_format(episode.audio_url)
        filename = f"{episode.id}_{episode.guid.replace('/', '_')}.{ext}"
        filepath = os.path.join(feed_dir, filename)
        
        try:
            # Download the file
            async with aiohttp.ClientSession() as session:
                async with session.get(episode.audio_url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download episode {episode.id}: HTTP {response.status}")
                        return False
                    
                    # Get content length if available
                    content_length = response.headers.get('Content-Length')
                    total_size = int(content_length) if content_length else None
                    
                    # Stream the download
                    with open(filepath, 'wb') as f:
                        downloaded = 0
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            if total_size:
                                progress = (downloaded / total_size) * 100
                                logger.debug(f"Download progress for episode {episode.id}: {progress:.1f}%")
            
            # Optimize audio file if needed
            optimized_path = await optimize_audio(filepath)
            if optimized_path != filepath:
                os.replace(optimized_path, filepath)
            
            # Update episode status
            episode.processing_status.is_downloaded = True
            episode.processing_status.download_path = filepath
            episode.audio_size = os.path.getsize(filepath)
            
            # Update metrics
            self.metrics.increment('downloads_completed')
            self.metrics.update({
                'last_download_size': episode.audio_size,
                'total_download_size': self.metrics.get('total_download_size', 0) + episode.audio_size
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading episode {episode.id}: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            raise
    
    def _update_start_time(self, status: ProcessingStatus):
        """Update download start time."""
        status.download_started_at = datetime.utcnow()
    
    def _update_completion_time(self, status: ProcessingStatus):
        """Update download completion time."""
        status.download_completed_at = datetime.utcnow() 