# PawgAudio - Podcast Analysis System

A comprehensive system for analyzing podcast content, tracking trends, and extracting insights from audio content.

## Features

- **Content Analysis**
  - Automatic transcription of podcast episodes
  - Speaker identification and diarization
  - Topic extraction and categorization
  - Key phrase and concept detection

- **Trend Detection**
  - Entity tracking and relationship mapping
  - Sentiment analysis over time
  - Prediction tracking and outcome analysis
  - Emerging narrative detection
  - Consensus and divergence analysis

- **System Architecture**
  - Modular, layered architecture
  - Environment-based configuration
  - Secure API key management
  - Plugin system for extensibility
  - Comprehensive CLI interface

## Project Structure

```
pawgaudio/
├── core/                    # Core system components
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── database.py         # Data access layer
│   ├── services.py         # Core services
│   └── cli.py              # Command line interface
├── content_analysis/        # Content analysis modules
├── speaker_identification/  # Speaker identification
├── trend_detection/         # Trend analysis modules
├── processing/             # Processing pipeline
├── database/               # Database migrations
├── feeds/                  # Feed management
├── podcast_analysis/       # Podcast analysis tools
└── podcast_analyzer/       # Main application
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pawgaudio.git
cd pawgaudio
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

The system uses a layered configuration approach:

1. Environment variables (`.env`)
2. Environment-specific config files (`config/development.json`, `config/production.json`)
3. Default settings in `core/config.py`

Key configuration areas:
- Database settings
- API keys and endpoints
- Processing parameters
- Analysis thresholds
- Plugin configurations

## Usage

### Command Line Interface

The system provides a comprehensive CLI for all operations:

```bash
# System Management
python -m podcast_analyzer system init    # Initialize system
python -m podcast_analyzer system status  # Show system status

# Feed Management
python -m podcast_analyzer feeds list     # List all feeds
python -m podcast_analyzer feeds add <url> [--name <name>]  # Add new feed
python -m podcast_analyzer feeds update   # Update all feeds

# Processing
python -m podcast_analyzer process --episode-id <id>  # Process specific episode
python -m podcast_analyzer process --feed-id <id>     # Process all episodes from feed

# Analysis
python -m podcast_analyzer analyze entity <entity_id>     # Analyze specific entity
python -m podcast_analyzer analyze trends [--window-days <days>]  # Analyze trends
python -m podcast_analyzer analyze predictions [--window-days <days>]  # Analyze predictions
```

### API Usage

The system can also be used programmatically:

```python
from core.config import ConfigManager
from core.database import DatabaseManager
from core.services import FeedManager, ProcessingPipeline, AnalysisService

# Initialize components
config_manager = ConfigManager()
db_manager = DatabaseManager(config_manager)
feed_manager = FeedManager(db_manager)
processing_pipeline = ProcessingPipeline(config_manager, db_manager)
analysis_service = AnalysisService(config_manager, db_manager)

# Example: Process a feed
async def process_feed(feed_id: int):
    feed = db_manager.get_feed(feed_id)
    if feed:
        episode_ids = [e.id for e in feed.episodes]
        await processing_pipeline.process_episodes(episode_ids)

# Example: Analyze trends
def analyze_trends(window_days: int = 30):
    analysis = analysis_service.get_trend_analysis(window_days)
    return analysis
```

## Development

### Adding New Features

1. **New Analysis Module**
   - Create module in appropriate directory
   - Implement required interfaces
   - Add configuration options
   - Register with core services

2. **New Plugin**
   - Create plugin directory
   - Implement plugin interface
   - Add plugin configuration
   - Register in config

### Testing

```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest tests/specific_test.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for transcription capabilities
- Various open-source libraries for audio processing
- Podcast creators for content analysis 