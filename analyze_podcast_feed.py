#!/usr/bin/env python3
import os
import argparse
from podcast_analyzer import PodcastFeedAnalyzer
from feeds.feed_manager import FeedManager

def main():
    parser = argparse.ArgumentParser(description='Analyze a podcast feed')
    parser.add_argument('podcast_name', help='Name of the podcast (used for directory structure)')
    parser.add_argument('--rss-url', help='URL of the podcast RSS feed (only for adding new feeds)')
    parser.add_argument('--description', help='Description of the podcast (only for adding new feeds)')
    parser.add_argument('--start-date', help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', help='End date in YYYY-MM-DD format')
    parser.add_argument('--base-dir', default='podcast_analysis', help='Base directory for all podcast analysis')
    
    args = parser.parse_args()
    
    # Initialize feed manager
    feed_manager = FeedManager()
    
    # If RSS URL is provided, add the feed
    if args.rss_url:
        print(f"Adding new feed: {args.podcast_name}")
        if feed_manager.add_feed(args.podcast_name, args.rss_url, args.description or ""):
            print("Feed added successfully")
        else:
            print("Failed to add feed")
            return
    
    # Create analyzer
    analyzer = PodcastFeedAnalyzer(
        podcast_name=args.podcast_name,
        base_dir=args.base_dir
    )
    
    # Analyze feed
    analyzer.analyze_feed(args.start_date, args.end_date)

if __name__ == "__main__":
    main() 