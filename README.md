# Podcast Analysis System

A comprehensive system for analyzing podcast episodes, providing deep insights into content, speakers, and implications.

## Features

- **Audio Processing**: Transcribes podcast episodes with high accuracy
- **Speaker Diarization**: Distinguishes between host and guests
- **Content Analysis**: Summarizes main points and key takeaways
- **Worldview Analysis**: Estimates the guest's worldview and perspective
- **Expertise Assessment**: Determines areas of expertise and specialization
- **Confidence Analysis**: Evaluates confidence levels in discussed theories
- **Impact Analysis**: Assesses implications for world events, geopolitics, and markets

## Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up your OpenAI API key in a `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

## Usage

```python
from podcast_analyzer import PodcastAnalyzer

analyzer = PodcastAnalyzer()
results = analyzer.analyze_episode("path/to/podcast.mp3")
```

## Output

The system provides a comprehensive analysis including:
- Full transcript with speaker identification
- Summary of main points
- Guest worldview assessment
- Expertise profile
- Confidence levels in discussed topics
- Geopolitical and market implications

## Requirements

- Python 3.8+
- FFmpeg (for audio processing)
- OpenAI API key 