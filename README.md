# PAWG Audio Analysis

A sophisticated podcast analysis tool that transcribes and analyzes financial and geopolitical podcasts using advanced AI models. The system provides structured insights, market implications, and actionable predictions across multiple timeframes.

## Features

- **Multi-Model Analysis**: Utilizes Claude 3 Sonnet, DeepSeek V3, and GPT-3.5-turbo for comprehensive analysis
- **Structured Analysis Framework**: Provides detailed insights across multiple dimensions:
  - Domain Classification
  - Hierarchical Theme Extraction
  - Sentiment Analysis
  - Actionable Predictions (Short, Medium, and Long-term)
  - Investment Implications
  - Confidence Assessment
- **Speaker Identification**: Automatically identifies and tracks different speakers in conversations
- **Cost Optimization**: Implements efficient token usage and fallback mechanisms
- **Local Storage**: Keeps all analysis results and audio files locally

## Installation

1. Clone the repository:
```bash
git clone https://github.com/darcy5d/pawg-audio.git
cd pawg-audio
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
Create a `.env` file with your API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DEEPSEEK_API_KEY=your_deepseek_key
```

## Usage

### Analyzing a Single Episode

```python
from podcast_analyzer import PodcastAnalyzer

analyzer = PodcastAnalyzer()
results = analyzer.analyze_episode("path/to/your/podcast.mp3")
```

### Analyzing Multiple Episodes

```python
from analyze_podcast_feed import analyze_feed

analyze_feed("path/to/your/feed.xml")
```

## Analysis Framework

The system provides a comprehensive analysis following this structure:

1. **Domain Classification**
   - Finance/Economics
   - Geopolitics/International Relations
   - Technology/Innovation
   - Philosophy/Ethics
   - Energy/Resources
   - Social/Cultural

2. **Hierarchical Theme Extraction**
   - Core concepts and arguments
   - Supporting assertions
   - Specific examples and data points
   - Counterarguments

3. **Sentiment Analysis**
   - Overall sentiment assessment
   - Emotional undertones
   - Speaker conviction levels
   - Sentiment shifts

4. **Actionable Predictions**
   - Short-term (0-6 months)
   - Medium-term (6-18 months)
   - Long-term (18+ months)

5. **Investment Implications**
   - Asset class performance
   - Sector opportunities
   - Geographic considerations
   - Risk factors

6. **Confidence Assessment**
   - Information quality
   - Speaker consensus
   - Historical precedent
   - Unknown variables

## Project Structure

```
pawg-audio/
├── podcast_analyzer/         # Core analysis module
├── feeds/                    # RSS feed management
├── requirements.txt          # Python dependencies
├── analyze_podcast.py        # Single episode analysis
├── analyze_podcast_feed.py   # Feed analysis
└── test_apis.py             # API testing utility
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 