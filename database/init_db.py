#!/usr/bin/env python3
import os
import argparse
from models import init_db, Base
from sqlalchemy import create_engine

def create_directory_structure(base_dir="podcast_analysis"):
    """
    Create the base directory structure for the podcast analysis system.
    
    Args:
        base_dir (str): Base directory for all podcast data
    """
    # Create base directory
    os.makedirs(base_dir, exist_ok=True)
    
    # Create subdirectories
    os.makedirs(os.path.join(base_dir, "downloads"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "transcripts"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "summaries"), exist_ok=True)
    
    print(f"Directory structure created at: {os.path.abspath(base_dir)}")

def initialize_database(db_url=None):
    """
    Initialize the SQLite database.
    
    Args:
        db_url (str): Database URL. If None, uses the environment variable DATABASE_URL
                     or defaults to sqlite:///podcast_analysis.db
    
    Returns:
        The database session
    """
    if db_url is None:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///podcast_analysis.db")
    
    # Create engine and tables
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    # Return initialized session
    session = init_db(db_url)
    
    print(f"Database initialized at: {db_url}")
    return session

def main():
    parser = argparse.ArgumentParser(description="Initialize the podcast analysis database and directory structure")
    parser.add_argument("--db-url", help="Database URL. Defaults to environment variable DATABASE_URL or sqlite:///podcast_analysis.db")
    parser.add_argument("--base-dir", default="podcast_analysis", help="Base directory for storing podcast data")
    args = parser.parse_args()
    
    # Create directory structure
    create_directory_structure(args.base_dir)
    
    # Initialize database
    initialize_database(args.db_url)
    
    print("Initialization complete!")

if __name__ == "__main__":
    main() 