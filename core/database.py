"""
Data Access Layer

This module provides database interactions and models for the system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
from .config import ConfigManager, DatabaseConfig

Base = declarative_base()

class Feed(Base):
    """Database model for podcast feeds."""
    __tablename__ = "feeds"
    
    id = Column(Integer, primary_key=True)
    url = Column(String, unique=True, nullable=False)
    name = Column(String)
    description = Column(String)
    last_fetched = Column(DateTime)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    episodes = relationship("Episode", back_populates="feed")

class Episode(Base):
    """Database model for podcast episodes."""
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey("feeds.id"))
    title = Column(String)
    description = Column(String)
    url = Column(String)
    published_at = Column(DateTime)
    duration = Column(Integer)  # in seconds
    transcript = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    feed = relationship("Feed", back_populates="episodes")
    entities = relationship("Entity", back_populates="episode")
    sentiments = relationship("Sentiment", back_populates="episode")
    predictions = relationship("Prediction", back_populates="episode")

class Entity(Base):
    """Database model for entities mentioned in episodes."""
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    name = Column(String)
    type = Column(String)
    confidence = Column(Float)
    context = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    
    episode = relationship("Episode", back_populates="entities")

class Sentiment(Base):
    """Database model for sentiment analysis results."""
    __tablename__ = "sentiments"
    
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    entity_id = Column(Integer, ForeignKey("entities.id"))
    score = Column(Float)
    magnitude = Column(Float)
    evidence = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    episode = relationship("Episode", back_populates="sentiments")

class Prediction(Base):
    """Database model for predictions made in episodes."""
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey("episodes.id"))
    description = Column(String)
    timeframe = Column(String)
    confidence = Column(Float)
    supporting_evidence = Column(JSON)
    counter_evidence = Column(JSON)
    outcome = Column(Boolean)
    outcome_observed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    episode = relationship("Episode", back_populates="predictions")

class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config_manager: ConfigManager):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager.get_config()
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
    
    def _create_engine(self):
        """Create a SQLAlchemy engine with the configured settings."""
        db_config = self.config.database
        return create_engine(
            db_config.url,
            poolclass=QueuePool,
            pool_size=db_config.pool_size,
            max_overflow=db_config.max_overflow,
            echo=db_config.echo,
            connect_args=db_config.connect_args
        )
    
    def init_db(self) -> None:
        """Initialize the database by creating all tables."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()
    
    def add_feed(self, feed_data: Dict[str, Any]) -> Feed:
        """Add a new feed to the database."""
        with self.get_session() as session:
            feed = Feed(**feed_data)
            session.add(feed)
            session.commit()
            return feed
    
    def get_feed(self, feed_id: int) -> Optional[Feed]:
        """Get a feed by its ID."""
        with self.get_session() as session:
            return session.query(Feed).get(feed_id)
    
    def get_active_feeds(self) -> List[Feed]:
        """Get all active feeds."""
        with self.get_session() as session:
            return session.query(Feed).filter(Feed.is_active == True).all()
    
    def add_episode(self, episode_data: Dict[str, Any]) -> Episode:
        """Add a new episode to the database."""
        with self.get_session() as session:
            episode = Episode(**episode_data)
            session.add(episode)
            session.commit()
            return episode
    
    def get_episode(self, episode_id: int) -> Optional[Episode]:
        """Get an episode by its ID."""
        with self.get_session() as session:
            return session.query(Episode).get(episode_id)
    
    def add_entity(self, entity_data: Dict[str, Any]) -> Entity:
        """Add a new entity to the database."""
        with self.get_session() as session:
            entity = Entity(**entity_data)
            session.add(entity)
            session.commit()
            return entity
    
    def add_sentiment(self, sentiment_data: Dict[str, Any]) -> Sentiment:
        """Add a new sentiment analysis to the database."""
        with self.get_session() as session:
            sentiment = Sentiment(**sentiment_data)
            session.add(sentiment)
            session.commit()
            return sentiment
    
    def add_prediction(self, prediction_data: Dict[str, Any]) -> Prediction:
        """Add a new prediction to the database."""
        with self.get_session() as session:
            prediction = Prediction(**prediction_data)
            session.add(prediction)
            session.commit()
            return prediction
    
    def update_prediction_outcome(
        self,
        prediction_id: int,
        outcome: bool,
        observed_at: datetime
    ) -> Optional[Prediction]:
        """Update the outcome of a prediction."""
        with self.get_session() as session:
            prediction = session.query(Prediction).get(prediction_id)
            if prediction:
                prediction.outcome = outcome
                prediction.outcome_observed_at = observed_at
                session.commit()
            return prediction 