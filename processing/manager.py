#!/usr/bin/env python3
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database.models import Episode, ProcessingStatus, Feed
from .workers.download_worker import DownloadWorker
from .workers.transcribe_worker import TranscribeWorker
from .workers.analyze_worker import AnalyzeWorker
from .utils.rate_limiter import RateLimiter
from .utils.metrics import MetricsCollector
from .config.settings import ProcessingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProcessingManager:
    def __init__(
        self,
        session: Session,
        config: ProcessingConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        """
        Initialize the processing manager.
        
        Args:
            session: SQLAlchemy database session
            config: Processing configuration
            metrics_collector: Optional metrics collector for monitoring
        """
        self.session = session
        self.config = config
        self.metrics = metrics_collector or MetricsCollector()
        
        # Initialize workers
        self.download_workers = [
            DownloadWorker(
                session=session,
                rate_limiter=RateLimiter(
                    max_calls=config.download_rate_limit,
                    time_window=60
                ),
                metrics=self.metrics
            ) for _ in range(config.num_download_workers)
        ]
        
        self.transcribe_workers = [
            TranscribeWorker(
                session=session,
                rate_limiter=RateLimiter(
                    max_calls=config.transcribe_rate_limit,
                    time_window=60
                ),
                metrics=self.metrics,
                use_api=config.use_whisper_api,
                api_key=config.whisper_api_key
            ) for _ in range(config.num_transcribe_workers)
        ]
        
        self.analyze_workers = [
            AnalyzeWorker(
                session=session,
                rate_limiter=RateLimiter(
                    max_calls=config.analyze_rate_limit,
                    time_window=60
                ),
                metrics=self.metrics
            ) for _ in range(config.num_analyze_workers)
        ]
        
        # Task queues
        self.download_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.transcribe_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.analyze_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # Track active tasks
        self.active_downloads: Set[int] = set()
        self.active_transcriptions: Set[int] = set()
        self.active_analyses: Set[int] = set()
        
        # Status tracking
        self.is_running = False
        self.start_time = None
        self.total_processed = 0
        self.failed_tasks = []
    
    async def start(self):
        """Start the processing pipeline."""
        if self.is_running:
            logger.warning("Processing manager is already running")
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        logger.info("Starting processing pipeline")
        
        # Start worker tasks
        worker_tasks = []
        for worker in self.download_workers:
            worker_tasks.append(asyncio.create_task(
                self._run_download_worker(worker)
            ))
        
        for worker in self.transcribe_workers:
            worker_tasks.append(asyncio.create_task(
                self._run_transcribe_worker(worker)
            ))
        
        for worker in self.analyze_workers:
            worker_tasks.append(asyncio.create_task(
                self._run_analyze_worker(worker)
            ))
        
        # Start queue management
        queue_task = asyncio.create_task(self._manage_queues())
        
        # Start metrics collection
        metrics_task = asyncio.create_task(self._collect_metrics())
        
        try:
            # Wait for all tasks
            await asyncio.gather(
                *worker_tasks,
                queue_task,
                metrics_task
            )
        except Exception as e:
            logger.error(f"Error in processing pipeline: {str(e)}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the processing pipeline gracefully."""
        logger.info("Stopping processing pipeline")
        self.is_running = False
        
        # Wait for queues to empty
        await self.download_queue.join()
        await self.transcribe_queue.join()
        await self.analyze_queue.join()
        
        # Final metrics collection
        await self._collect_metrics()
        
        logger.info("Processing pipeline stopped")
    
    async def _manage_queues(self):
        """Manage task queues and prioritization."""
        while self.is_running:
            try:
                # Find unprocessed episodes
                unprocessed = self.session.query(Episode).join(
                    ProcessingStatus
                ).filter(
                    or_(
                        and_(
                            ProcessingStatus.is_downloaded == False,
                            ProcessingStatus.retry_count < self.config.max_retries
                        ),
                        and_(
                            ProcessingStatus.is_downloaded == True,
                            ProcessingStatus.is_transcribed == False,
                            ProcessingStatus.retry_count < self.config.max_retries
                        ),
                        and_(
                            ProcessingStatus.is_transcribed == True,
                            ProcessingStatus.is_analyzed == False,
                            ProcessingStatus.retry_count < self.config.max_retries
                        )
                    )
                ).order_by(Episode.publish_date.desc()).limit(100).all()
                
                for episode in unprocessed:
                    status = episode.processing_status
                    
                    # Calculate priority based on recency and retry count
                    age_hours = (datetime.utcnow() - episode.publish_date).total_seconds() / 3600
                    priority = age_hours + (status.retry_count * 24)  # Add 24 hours per retry
                    
                    if not status.is_downloaded and episode.id not in self.active_downloads:
                        await self.download_queue.put((priority, episode.id))
                    elif status.is_downloaded and not status.is_transcribed and episode.id not in self.active_transcriptions:
                        await self.transcribe_queue.put((priority, episode.id))
                    elif status.is_transcribed and not status.is_analyzed and episode.id not in self.active_analyses:
                        await self.analyze_queue.put((priority, episode.id))
            
            except Exception as e:
                logger.error(f"Error managing queues: {str(e)}")
            
            await asyncio.sleep(self.config.queue_check_interval)
    
    async def _run_download_worker(self, worker: DownloadWorker):
        """Run a download worker."""
        while self.is_running:
            try:
                priority, episode_id = await self.download_queue.get()
                self.active_downloads.add(episode_id)
                
                try:
                    await worker.process(episode_id)
                    self.total_processed += 1
                except Exception as e:
                    logger.error(f"Download worker error for episode {episode_id}: {str(e)}")
                    self.failed_tasks.append((episode_id, "download", str(e)))
                
                self.active_downloads.remove(episode_id)
                self.download_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error in download worker loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _run_transcribe_worker(self, worker: TranscribeWorker):
        """Run a transcription worker."""
        while self.is_running:
            try:
                priority, episode_id = await self.transcribe_queue.get()
                self.active_transcriptions.add(episode_id)
                
                try:
                    await worker.process(episode_id)
                    self.total_processed += 1
                except Exception as e:
                    logger.error(f"Transcribe worker error for episode {episode_id}: {str(e)}")
                    self.failed_tasks.append((episode_id, "transcribe", str(e)))
                
                self.active_transcriptions.remove(episode_id)
                self.transcribe_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error in transcribe worker loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _run_analyze_worker(self, worker: AnalyzeWorker):
        """Run an analysis worker."""
        while self.is_running:
            try:
                priority, episode_id = await self.analyze_queue.get()
                self.active_analyses.add(episode_id)
                
                try:
                    await worker.process(episode_id)
                    self.total_processed += 1
                except Exception as e:
                    logger.error(f"Analyze worker error for episode {episode_id}: {str(e)}")
                    self.failed_tasks.append((episode_id, "analyze", str(e)))
                
                self.active_analyses.remove(episode_id)
                self.analyze_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error in analyze worker loop: {str(e)}")
                await asyncio.sleep(1)
    
    async def _collect_metrics(self):
        """Collect and report processing metrics."""
        while self.is_running:
            try:
                # Calculate processing rates
                elapsed = (datetime.utcnow() - self.start_time).total_seconds()
                rate = self.total_processed / elapsed if elapsed > 0 else 0
                
                # Get queue sizes
                download_size = self.download_queue.qsize()
                transcribe_size = self.transcribe_queue.qsize()
                analyze_size = self.analyze_queue.qsize()
                
                # Update metrics
                self.metrics.update({
                    'processing_rate': rate,
                    'total_processed': self.total_processed,
                    'failed_tasks': len(self.failed_tasks),
                    'download_queue': download_size,
                    'transcribe_queue': transcribe_size,
                    'analyze_queue': analyze_size,
                    'active_downloads': len(self.active_downloads),
                    'active_transcriptions': len(self.active_transcriptions),
                    'active_analyses': len(self.active_analyses)
                })
                
                # Log metrics
                logger.info(f"Processing metrics: {self.metrics.get_all()}")
            
            except Exception as e:
                logger.error(f"Error collecting metrics: {str(e)}")
            
            await asyncio.sleep(self.config.metrics_interval)
    
    def get_status(self) -> Dict:
        """Get current processing status."""
        return {
            'is_running': self.is_running,
            'start_time': self.start_time,
            'total_processed': self.total_processed,
            'failed_tasks': len(self.failed_tasks),
            'metrics': self.metrics.get_all(),
            'queues': {
                'download': self.download_queue.qsize(),
                'transcribe': self.transcribe_queue.qsize(),
                'analyze': self.analyze_queue.qsize()
            },
            'active_tasks': {
                'downloads': len(self.active_downloads),
                'transcriptions': len(self.active_transcriptions),
                'analyses': len(self.active_analyses)
            }
        } 