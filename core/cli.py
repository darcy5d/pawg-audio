"""
Command Line Interface

This module provides a CLI for system management and analysis.
"""

import argparse
import logging
from typing import Optional
from datetime import datetime, timedelta
from .config import ConfigManager
from .database import DatabaseManager
from .services import FeedManager, ProcessingPipeline, AnalysisService

class CLI:
    """Command Line Interface for the system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.db_manager = DatabaseManager(self.config_manager)
        self.feed_manager = FeedManager(self.db_manager)
        self.processing_pipeline = ProcessingPipeline(
            self.config_manager,
            self.db_manager
        )
        self.analysis_service = AnalysisService(
            self.config_manager,
            self.db_manager
        )
    
    def setup_logging(self, verbose: bool = False) -> None:
        """Setup logging configuration."""
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description="Podcast Analysis System CLI"
        )
        
        # Global options
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest="command",
            help="Available commands"
        )
        
        # Feed management
        feed_parser = subparsers.add_parser(
            "feeds",
            help="Manage podcast feeds"
        )
        feed_subparsers = feed_parser.add_subparsers(dest="feed_command")
        
        feed_subparsers.add_parser(
            "list",
            help="List all feeds"
        )
        feed_subparsers.add_parser(
            "update",
            help="Update all feeds"
        )
        add_feed_parser = feed_subparsers.add_parser(
            "add",
            help="Add a new feed"
        )
        add_feed_parser.add_argument(
            "url",
            help="Feed URL"
        )
        add_feed_parser.add_argument(
            "--name",
            help="Feed name"
        )
        
        # Processing
        process_parser = subparsers.add_parser(
            "process",
            help="Process episodes"
        )
        process_parser.add_argument(
            "--episode-id",
            type=int,
            help="Process specific episode"
        )
        process_parser.add_argument(
            "--feed-id",
            type=int,
            help="Process all episodes from feed"
        )
        
        # Analysis
        analysis_parser = subparsers.add_parser(
            "analyze",
            help="Run analysis"
        )
        analysis_subparsers = analysis_parser.add_subparsers(dest="analysis_command")
        
        entity_parser = analysis_subparsers.add_parser(
            "entity",
            help="Analyze entity"
        )
        entity_parser.add_argument(
            "entity_id",
            type=int,
            help="Entity ID"
        )
        
        trend_parser = analysis_subparsers.add_parser(
            "trends",
            help="Analyze trends"
        )
        trend_parser.add_argument(
            "--window-days",
            type=int,
            help="Analysis window in days"
        )
        
        prediction_parser = analysis_subparsers.add_parser(
            "predictions",
            help="Analyze predictions"
        )
        prediction_parser.add_argument(
            "--window-days",
            type=int,
            help="Analysis window in days"
        )
        
        # System management
        system_parser = subparsers.add_parser(
            "system",
            help="System management"
        )
        system_subparsers = system_parser.add_subparsers(dest="system_command")
        
        system_subparsers.add_parser(
            "init",
            help="Initialize system"
        )
        system_subparsers.add_parser(
            "status",
            help="Show system status"
        )
        
        return parser.parse_args()
    
    async def run(self) -> None:
        """Run the CLI."""
        args = self.parse_args()
        self.setup_logging(args.verbose)
        
        if not args.command:
            self.logger.error("No command specified")
            return
        
        try:
            if args.command == "feeds":
                await self.handle_feeds(args)
            elif args.command == "process":
                await self.handle_process(args)
            elif args.command == "analyze":
                await self.handle_analysis(args)
            elif args.command == "system":
                await self.handle_system(args)
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
    
    async def handle_feeds(self, args: argparse.Namespace) -> None:
        """Handle feed management commands."""
        if args.feed_command == "list":
            feeds = self.db_manager.get_active_feeds()
            for feed in feeds:
                print(f"{feed.id}: {feed.name} ({feed.url})")
        elif args.feed_command == "update":
            await self.feed_manager.update_feeds()
        elif args.feed_command == "add":
            feed_data = {
                "url": args.url,
                "name": args.name or args.url,
                "is_active": True
            }
            feed = self.db_manager.add_feed(feed_data)
            print(f"Added feed: {feed.name} ({feed.url})")
    
    async def handle_process(self, args: argparse.Namespace) -> None:
        """Handle processing commands."""
        if args.episode_id:
            await self.processing_pipeline.process_episode(args.episode_id)
        elif args.feed_id:
            feed = self.db_manager.get_feed(args.feed_id)
            if feed:
                episode_ids = [e.id for e in feed.episodes]
                await self.processing_pipeline.process_episodes(episode_ids)
            else:
                self.logger.error(f"Feed {args.feed_id} not found")
    
    async def handle_analysis(self, args: argparse.Namespace) -> None:
        """Handle analysis commands."""
        if args.analysis_command == "entity":
            analysis = self.analysis_service.get_entity_analysis(args.entity_id)
            print(f"Entity Analysis for ID {args.entity_id}:")
            print(f"Name: {analysis['entity']['name']}")
            print(f"Type: {analysis['entity']['type']}")
            print(f"Total Mentions: {analysis['mentions']['total']}")
            print(f"Recent Frequency: {analysis['mentions']['recent_frequency']:.2f}")
            print("\nSentiment Summary:")
            print(f"Average Score: {analysis['sentiment']['overall_metrics']['average_score']:.2f}")
            print(f"Trend: {analysis['sentiment']['overall_metrics']['trend']:.2f}")
        elif args.analysis_command == "trends":
            analysis = self.analysis_service.get_trend_analysis(args.window_days)
            print(f"Trend Analysis (Last {analysis['time_window']['days']} days):")
            for trend in analysis["trends"]:
                print(f"\nTrend: {trend['name']}")
                print(f"Confidence: {trend['confidence']:.2f}")
                print(f"Description: {trend['description']}")
        elif args.analysis_command == "predictions":
            analysis = self.analysis_service.get_prediction_analysis(args.window_days)
            print(f"Prediction Analysis (Last {analysis['time_window']['days']} days):")
            for entity_id, patterns in analysis["prediction_patterns"].items():
                print(f"\nEntity ID: {entity_id}")
                for pattern in patterns:
                    print(f"Timeframe: {pattern['timeframe']}")
                    print(f"Total Predictions: {pattern['total_predictions']}")
                    print(f"Consensus Score: {pattern['consensus_score']:.2f}")
    
    async def handle_system(self, args: argparse.Namespace) -> None:
        """Handle system management commands."""
        if args.system_command == "init":
            self.db_manager.init_db()
            print("System initialized successfully")
        elif args.system_command == "status":
            config = self.config_manager.get_config()
            print("System Status:")
            print(f"Environment: {config.environment.value}")
            print(f"Debug Mode: {config.debug}")
            print("\nDatabase:")
            print(f"URL: {config.database.url}")
            print(f"Pool Size: {config.database.pool_size}")
            print("\nProcessing:")
            print(f"Max Workers: {config.processing.max_workers}")
            print(f"Batch Size: {config.processing.batch_size}")
            print("\nAnalysis:")
            print(f"Min Confidence: {config.analysis.min_confidence}")
            print(f"Trend Window: {config.analysis.trend_window_days} days")

def main():
    """Main entry point for the CLI."""
    cli = CLI()
    asyncio.run(cli.run())

if __name__ == "__main__":
    main() 