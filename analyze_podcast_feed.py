#!/usr/bin/env python3
import os
import argparse
from podcast_analyzer import PodcastFeedAnalyzer
from feeds.feed_manager import FeedManager
from typing import Optional

def analyze_podcast_feed(
    name: str,
    rss_url: str,
    description: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    base_dir: str = "podcast_analysis"
):
    """
    Analyze a podcast feed and process new episodes.
    
    Args:
        name (str): Name of the podcast
        rss_url (str): URL of the podcast RSS feed
        description (str): Description of the podcast
        start_date (Optional[str]): Start date in YYYY-MM-DD format
        end_date (Optional[str]): End date in YYYY-MM-DD format
        base_dir (str): Base directory for storing analysis results
    """
    try:
        # Initialize feed manager
        feed_manager = FeedManager()
        
        # Add or update feed
        feed_manager.add_feed(name, rss_url, description)
        
        # Get unprocessed episodes
        unprocessed_episodes = feed_manager.get_unprocessed_episodes(name, start_date, end_date)
        
        if not unprocessed_episodes:
            print(f"No new episodes found for {name}")
            return
        
        print(f"Found {len(unprocessed_episodes)} unprocessed episodes for {name}")
        
        # Initialize podcast analyzer
        analyzer = PodcastFeedAnalyzer(podcast_name=name, base_dir=base_dir)
        
        # Process each unprocessed episode
        for episode in unprocessed_episodes:
            try:
                print(f"\nProcessing episode: {episode['title']}")
                print(f"Published: {episode['published_date']}")
                
                # Download and analyze episode
                result = analyzer.analyze_episode_from_url(
                    audio_url=episode['audio_url'],
                    episode_title=episode['title'],
                    published_date=episode['published_date']
                )
                
                if result:
                    # Mark episode as processed
                    feed_manager.mark_episode_processed(
                        name=name,
                        episode_title=episode['title'],
                        published_date=episode['published_date'],
                        audio_url=episode['audio_url']
                    )
                    print(f"Successfully processed episode: {episode['title']}")
                else:
                    print(f"Failed to process episode: {episode['title']}")
                
            except Exception as e:
                print(f"Error processing episode {episode['title']}: {e}")
                continue
        
    except Exception as e:
        print(f"Error analyzing podcast feed: {e}")

def list_unprocessed_episodes(podcast_name: str, rss_url: str, description: str, start_date: Optional[str] = None, end_date: Optional[str] = None, base_dir: str = "podcast_analysis"):
    """
    List unprocessed episodes for a podcast without processing them.
    
    Args:
        podcast_name (str): Name of the podcast
        rss_url (str): RSS feed URL
        description (str): Podcast description
        start_date (Optional[str]): Start date in YYYY-MM-DD format
        end_date (Optional[str]): End date in YYYY-MM-DD format
        base_dir (str): Base directory for storing analysis results
    """
    try:
        # Initialize feed manager
        feed_manager = FeedManager()
        
        # Add feed if not already added
        if not feed_manager.get_feed(podcast_name):
            feed_manager.add_feed(podcast_name, rss_url, description)
        
        # Get unprocessed episodes
        unprocessed_episodes = feed_manager.get_unprocessed_episodes(podcast_name, rss_url, start_date, end_date)
        
        print(f"\nFound {len(unprocessed_episodes)} unprocessed episodes for {podcast_name}:")
        print("-" * 80)
        
        for episode in unprocessed_episodes:
            print(f"Title: {episode['title']}")
            if episode.get('published_date'):
                print(f"Published: {episode['published_date']}")
            if episode.get('description'):
                print(f"Description: {episode['description'][:200]}...")
            print("-" * 80)
            
    except Exception as e:
        print(f"Error listing unprocessed episodes: {e}")

def main():
    parser = argparse.ArgumentParser(description="Analyze podcast feed")
    parser.add_argument("--name", required=True, help="Name of the podcast")
    parser.add_argument("--rss-url", required=True, help="URL of the podcast RSS feed")
    parser.add_argument("--description", required=True, help="Description of the podcast")
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end-date", help="End date in YYYY-MM-DD format")
    parser.add_argument("--base-dir", default="podcast_analysis", help="Base directory for storing analysis results")
    parser.add_argument("--list-only", action="store_true", help="Only list unprocessed episodes without processing them")
    
    args = parser.parse_args()
    
    if args.list_only:
        list_unprocessed_episodes(
            podcast_name=args.name,
            rss_url=args.rss_url,
            description=args.description,
            start_date=args.start_date,
            end_date=args.end_date,
            base_dir=args.base_dir
        )
        return
    else:
        analyze_podcast_feed(
            name=args.name,
            rss_url=args.rss_url,
            description=args.description,
            start_date=args.start_date,
            end_date=args.end_date,
            base_dir=args.base_dir
        )

if __name__ == "__main__":
    main() 