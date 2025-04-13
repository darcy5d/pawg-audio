#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from ..utils.rate_limiter import RateLimiter
from ..utils.metrics import MetricsCollector
from database.models import Episode, ProcessingStatus

logger = logging.getLogger(__name__)

class BaseWorker:
    def __init__(
        self,
        session: Session,
        rate_limiter: RateLimiter,
        metrics: MetricsCollector,
        max_retries: int = 3,
        retry_delay: int = 5
    ):
        """
        Initialize the base worker.
        
        Args:
            session: SQLAlchemy database session
            rate_limiter: Rate limiter for API calls
            metrics: Metrics collector
            max_retries: Maximum number of retries for failed tasks
            retry_delay: Base delay (in seconds) between retries
        """
        self.session = session
        self.rate_limiter = rate_limiter
        self.metrics = metrics
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    async def process(self, episode_id: int) -> bool:
        """
        Process an episode with retries and error handling.
        
        Args:
            episode_id: ID of the episode to process
            
        Returns:
            bool: True if processing was successful
        """
        episode = self.session.query(Episode).get(episode_id)
        if not episode:
            logger.error(f"Episode {episode_id} not found")
            return False
        
        status = episode.processing_status
        if not status:
            logger.error(f"No processing status found for episode {episode_id}")
            return False
        
        # Update status timestamps
        self._update_start_time(status)
        
        retries = 0
        while retries <= self.max_retries:
            try:
                # Wait for rate limiter
                await self.rate_limiter.acquire()
                
                # Process the episode
                success = await self._process_episode(episode)
                
                if success:
                    # Update status
                    self._update_completion_time(status)
                    self.session.commit()
                    return True
                
            except Exception as e:
                logger.error(f"Error processing episode {episode_id} (attempt {retries + 1}): {str(e)}")
                status.error_message = str(e)
                status.retry_count += 1
                self.session.commit()
                
                if retries < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** retries)
                    logger.info(f"Retrying episode {episode_id} in {delay} seconds")
                    await asyncio.sleep(delay)
                
            retries += 1
        
        logger.error(f"Failed to process episode {episode_id} after {self.max_retries} retries")
        return False
    
    async def _process_episode(self, episode: Episode) -> bool:
        """
        Process a single episode. To be implemented by subclasses.
        
        Args:
            episode: Episode to process
            
        Returns:
            bool: True if processing was successful
        """
        raise NotImplementedError("Subclasses must implement _process_episode")
    
    def _update_start_time(self, status: ProcessingStatus):
        """Update the appropriate start timestamp based on worker type."""
        raise NotImplementedError("Subclasses must implement _update_start_time")
    
    def _update_completion_time(self, status: ProcessingStatus):
        """Update the appropriate completion timestamp based on worker type."""
        raise NotImplementedError("Subclasses must implement _update_completion_time") 