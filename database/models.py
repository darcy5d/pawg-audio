#!/usr/bin/env python3
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Table, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import datetime
import os

Base = declarative_base()

# Many-to-many relationship between episodes and speakers
episode_speakers = Table(
    'episode_speakers',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('episode_id', Integer, ForeignKey('episodes.id'), nullable=False),
    Column('speaker_id', Integer, ForeignKey('speakers.id'), nullable=False),
    Column('speaking_time', Float, nullable=True, comment='Speaking time in seconds'),
    Column('speaking_percentage', Float, nullable=True),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow),
    Index('idx_episode_speaker', 'episode_id', 'speaker_id')
)

# Many-to-many relationship between entities and insights
entity_mentions = Table(
    'entity_mentions',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('entity_id', Integer, ForeignKey('entities.id'), nullable=False),
    Column('insight_id', Integer, ForeignKey('insights.id'), nullable=False),
    Column('sentiment_score', Float, nullable=True, comment='Sentiment score from -1.0 to 1.0'),
    Column('importance_score', Float, nullable=True, comment='Importance score from 0.0 to 1.0'),
    Column('created_at', DateTime, default=datetime.datetime.utcnow),
    Column('updated_at', DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow),
    Index('idx_entity_insight', 'entity_id', 'insight_id')
)

class Feed(Base):
    __tablename__ = 'feeds'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    url = Column(String(512), nullable=False)
    category = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    update_frequency = Column(String(50), nullable=True, comment='Daily, Weekly, Monthly, etc.')
    author = Column(String(255), nullable=True)
    language = Column(String(50), nullable=True)
    image_url = Column(String(512), nullable=True)
    website_url = Column(String(512), nullable=True)
    last_checked = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    episodes = relationship("Episode", back_populates="feed", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Feed(name='{self.name}', url='{self.url}')>"


class Episode(Base):
    __tablename__ = 'episodes'
    
    id = Column(Integer, primary_key=True)
    feed_id = Column(Integer, ForeignKey('feeds.id'), nullable=False)
    guid = Column(String(512), nullable=True, unique=True, comment='Unique identifier from RSS feed')
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    publish_date = Column(DateTime, nullable=False, index=True)
    duration = Column(Integer, nullable=True, comment='Duration in seconds')
    audio_url = Column(String(512), nullable=False)
    audio_format = Column(String(50), nullable=True)
    audio_size = Column(Integer, nullable=True, comment='Size in bytes')
    image_url = Column(String(512), nullable=True)
    website_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    feed = relationship("Feed", back_populates="episodes")
    processing_status = relationship("ProcessingStatus", back_populates="episode", uselist=False, cascade="all, delete-orphan")
    insights = relationship("Insight", back_populates="episode", cascade="all, delete-orphan")
    speakers = relationship("Speaker", secondary=episode_speakers, back_populates="episodes")
    
    __table_args__ = (
        Index('idx_feed_publish_date', 'feed_id', 'publish_date'),
    )
    
    def __repr__(self):
        return f"<Episode(title='{self.title}', feed_id={self.feed_id})>"


class ProcessingStatus(Base):
    __tablename__ = 'processing_status'
    
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey('episodes.id'), nullable=False, unique=True)
    
    # Status flags
    is_downloaded = Column(Boolean, default=False)
    is_transcribed = Column(Boolean, default=False)
    is_analyzed = Column(Boolean, default=False)
    
    # Processing data
    download_path = Column(String(512), nullable=True)
    transcript_path = Column(String(512), nullable=True)
    
    # Timestamps for tracking and analytics
    queued_at = Column(DateTime, nullable=True)
    download_started_at = Column(DateTime, nullable=True)
    download_completed_at = Column(DateTime, nullable=True)
    transcription_started_at = Column(DateTime, nullable=True)
    transcription_completed_at = Column(DateTime, nullable=True)
    analysis_started_at = Column(DateTime, nullable=True)
    analysis_completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    episode = relationship("Episode", back_populates="processing_status")
    
    __table_args__ = (
        Index('idx_unprocessed_episodes', 'is_downloaded', 'is_transcribed', 'is_analyzed'),
    )
    
    def __repr__(self):
        return f"<ProcessingStatus(episode_id={self.episode_id}, downloaded={self.is_downloaded}, transcribed={self.is_transcribed}, analyzed={self.is_analyzed})>"


class Speaker(Base):
    __tablename__ = 'speakers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True, comment='Host, Guest, Panelist, etc.')
    expertise = Column(Text, nullable=True)
    organization = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    image_url = Column(String(512), nullable=True)
    website_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    episodes = relationship("Episode", secondary=episode_speakers, back_populates="speakers")
    insights = relationship("Insight", back_populates="speaker")
    
    __table_args__ = (
        Index('idx_speaker_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Speaker(name='{self.name}', role='{self.role}')>"


class Insight(Base):
    __tablename__ = 'insights'
    
    id = Column(Integer, primary_key=True)
    episode_id = Column(Integer, ForeignKey('episodes.id'), nullable=False)
    speaker_id = Column(Integer, ForeignKey('speakers.id'), nullable=True)
    
    insight_type = Column(String(100), nullable=False, comment='Theme, Prediction, Opinion, Fact, etc.')
    content = Column(Text, nullable=False)
    confidence = Column(Float, nullable=True, comment='Confidence score from 0.0 to 1.0')
    
    # For predictions and time-sensitive insights
    timeframe = Column(String(50), nullable=True, comment='Short-term, Medium-term, Long-term')
    reference_date = Column(DateTime, nullable=True, comment='Date referenced in the insight')
    start_timestamp = Column(Float, nullable=True, comment='Start time in seconds from beginning of episode')
    end_timestamp = Column(Float, nullable=True, comment='End time in seconds from beginning of episode')
    
    # For sentiment analysis
    sentiment_score = Column(Float, nullable=True, comment='Overall sentiment from -1.0 to 1.0')
    conviction_level = Column(Float, nullable=True, comment='Conviction level from 0.0 to 1.0')
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    episode = relationship("Episode", back_populates="insights")
    speaker = relationship("Speaker", back_populates="insights")
    entities = relationship("Entity", secondary=entity_mentions, back_populates="insights")
    
    __table_args__ = (
        Index('idx_episode_insight_type', 'episode_id', 'insight_type'),
        Index('idx_insight_timeframe', 'timeframe', 'reference_date'),
        Index('idx_insight_sentiment', 'sentiment_score'),
    )
    
    def __repr__(self):
        return f"<Insight(type='{self.insight_type}', episode_id={self.episode_id})>"


class Entity(Base):
    __tablename__ = 'entities'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(String(100), nullable=False, comment='Person, Organization, Location, Asset, Concept, etc.')
    description = Column(Text, nullable=True)
    aliases = Column(Text, nullable=True, comment='Comma-separated list of alternative names')
    canonical_url = Column(String(512), nullable=True)
    image_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    insights = relationship("Insight", secondary=entity_mentions, back_populates="entities")
    
    __table_args__ = (
        Index('idx_entity_type', 'type'),
        Index('idx_entity_name', 'name'),
    )
    
    def __repr__(self):
        return f"<Entity(name='{self.name}', type='{self.type}')>"


# Database initialization function
def init_db(db_path='sqlite:///podcast_analysis.db'):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Create database if this file is run directly
    db_path = os.environ.get("DATABASE_URL", "sqlite:///podcast_analysis.db")
    session = init_db(db_path)
    print(f"Database initialized at: {db_path}") 