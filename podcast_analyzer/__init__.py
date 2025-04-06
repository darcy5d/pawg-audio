import os
import json
from typing import Dict, List, Optional
import openai
from dotenv import load_dotenv
import whisper
from pydub import AudioSegment
import numpy as np
import time
import feedparser
import requests
from openai import OpenAI
import anthropic
from datetime import datetime, timezone
from feeds.feed_manager import FeedManager

class PodcastAnalyzer:
    def __init__(self, speaker_context: Optional[Dict] = None):
        load_dotenv()
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        self.whisper_model = whisper.load_model("base", device="cpu")
        self.speaker_context = speaker_context or {}
        
    def is_discount_hours(self):
        """Check if current time is within DeepSeek discount hours (02:30-10:30 AEST)"""
        current_time = datetime.now(timezone.utc)
        # Convert to AEST (UTC+10)
        aest_time = current_time.astimezone(timezone.utc).replace(hour=(current_time.hour + 10) % 24)
        return 2 <= aest_time.hour < 10
        
    def split_text(self, text: str, chunk_size: int = 2000) -> List[str]:
        """Split text into smaller chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1  # +1 for space
            
            if current_size >= chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
    
    def transcribe_audio(self, audio_path: str, episode_title: str = "", use_deepseek: bool = True) -> Dict:
        """Transcribe the podcast audio and identify speakers."""
        print("Starting transcription...")
        
        # Transcribe using Whisper
        result = self.whisper_model.transcribe(audio_path)
        print("Transcription complete. Analyzing speakers...")
        
        # Split transcript into larger chunks to reduce API calls
        transcript_chunks = self.split_text(result['text'], chunk_size=4000)
        print(f"Split transcript into {len(transcript_chunks)} chunks for processing")
        
        # Extract guest name from episode title if possible
        guest_name = ""
        if ":" in episode_title:
            guest_name = episode_title.split(":")[-1].strip()
        
        # Process each chunk
        all_speaker_identifications = []
        for i, chunk in enumerate(transcript_chunks, 1):
            print(f"Processing chunk {i}/{len(transcript_chunks)}...")
            
            diarization_prompt = f"""
            You are analyzing a segment from The Grant Williams Podcast. 
            The host is Grant Williams.
            {f"The guest is {guest_name}." if guest_name else "There is one guest whose name you should identify from context."}
            
            Identify the speakers in this segment. Format each line as "Speaker: Text".
            Look for:
            - Grant Williams (host) asking questions or introducing topics
            - Guest name from introductions or self-references
            - Maintain consistent speaker names across segments
            
            Segment: {chunk}
            """
            
            try:
                # Always use DeepSeek V3 since it's cheaper than GPT-3.5-turbo
                diarization_response = self.deepseek_client.chat.completions.create(
                    model="deepseek-chat",  # This will use DeepSeek V3
                    messages=[
                        {"role": "system", "content": "You are an expert at identifying speakers in podcast transcripts."},
                        {"role": "user", "content": diarization_prompt}
                    ],
                    max_tokens=1000
                )
                
                all_speaker_identifications.append(diarization_response.choices[0].message.content)
                time.sleep(1)  # Reduced delay between requests
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                # Fallback to GPT-3.5-turbo if DeepSeek fails
                try:
                    diarization_response = self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert at identifying speakers in podcast transcripts."},
                            {"role": "user", "content": diarization_prompt}
                        ],
                        max_tokens=1000
                    )
                    all_speaker_identifications.append(diarization_response.choices[0].message.content)
                except Exception as e2:
                    print(f"Fallback also failed for chunk {i}: {str(e2)}")
                    all_speaker_identifications.append(f"Error processing chunk {i}")
        
        return {
            "transcript": result['text'],
            "speaker_identification": "\n\n".join(all_speaker_identifications)
        }
    
    def analyze_content(self, transcript: str, speaker_identification: str, episode_title: str = "", use_claude: bool = True) -> Dict:
        """Analyze the content for main points, worldview, and expertise."""
        print("Analyzing content...")
        
        # Extract guest name from episode title
        guest_name = ""
        if ":" in episode_title:
            guest_name = episode_title.split(":")[-1].strip()
        
        # Use Claude for content analysis
        try:
            claude_response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"""You are an expert financial and geopolitical analyst tasked with extracting structured insights from podcast transcripts. 
                    Analyze the following podcast transcript featuring {guest_name if guest_name else "a guest"} and provide a detailed analysis following this framework:

                    1. DOMAIN CLASSIFICATION
                    Classify the podcast into one or more primary domains:
                    - Finance/Economics
                    - Geopolitics/International Relations
                    - Technology/Innovation
                    - Philosophy/Ethics
                    - Energy/Resources
                    - Social/Cultural
                    - Other (please specify)

                    2. HIERARCHICAL THEME EXTRACTION
                    Extract 1-5 major themes discussed in the podcast. For each theme:
                       a. Identify the core concept/argument
                       b. List key supporting assertions made by speakers
                       c. Document specific examples, data points, or claims that reinforce these assertions
                       d. Note any significant counterarguments or alternative perspectives presented

                    3. SENTIMENT ANALYSIS
                    For each major theme:
                       a. Assess the overall sentiment (strongly negative, moderately negative, neutral, moderately positive, strongly positive)
                       b. Identify emotional undertones in the discussion (fear, optimism, uncertainty, confidence, etc.)
                       c. Evaluate the speakers' conviction levels regarding their assertions
                       d. Note any significant shifts in sentiment throughout the discussion

                    4. ACTIONABLE PREDICTIONS
                    Based on the analysis, identify potential market implications across three timeframes:

                    SHORT-TERM (0-6 months):
                    - Specific assets, sectors, or regions likely to be impacted
                    - Potential market movements or reactions to discussed events
                    - Immediate trading or positioning opportunities

                    MEDIUM-TERM (6-18 months):
                    - Emerging trends that could reshape market dynamics
                    - Structural changes that may affect asset classes
                    - Strategic positioning recommendations

                    LONG-TERM (18+ months):
                    - Fundamental shifts in economic, political, or social paradigms
                    - Secular trends that could create new investment categories
                    - Transformative scenarios that require strategic preparation

                    5. INVESTMENT IMPLICATIONS
                    Provide specific, actionable insights:
                    - Asset classes positioned for outperformance/underperformance
                    - Specific sectors or industries likely to benefit/suffer
                    - Geographic regions of opportunity or concern
                    - Risk factors that may invalidate the analysis

                    6. CONFIDENCE ASSESSMENT
                    Rate your confidence in the predictions (low, medium, high) based on:
                    - Quality and credibility of information presented
                    - Consensus among multiple speakers (if applicable)
                    - Historical precedent for similar scenarios
                    - Potential unknown variables or black swan events

                    Transcript:
                    {transcript}
                    
                    Please provide a comprehensive analysis following this structured framework."""
                }]
            )
            content_analysis = claude_response.content[0].text
        except Exception as e:
            content_analysis = f"Error analyzing content: {str(e)}"
        
        return {
            "content_analysis": content_analysis
        }
    
    def analyze_episode(self, audio_path: str) -> Dict:
        """Main function to analyze a podcast episode."""
        print(f"\nAnalyzing podcast episode: {audio_path}")
        
        # Step 1: Transcribe and identify speakers
        transcription_results = self.transcribe_audio(audio_path)
        
        # Step 2: Analyze content
        content_analysis = self.analyze_content(
            transcription_results["transcript"],
            transcription_results["speaker_identification"]
        )
        
        print("Analysis complete!")
        
        # Combine results
        return {
            "transcription": transcription_results,
            "analysis": content_analysis
        }

class PodcastFeedAnalyzer:
    def __init__(self, podcast_name: str, base_dir: str = "podcast_analysis"):
        """
        Initialize the podcast feed analyzer.
        
        Args:
            podcast_name (str): Name of the podcast (used for directory structure)
            base_dir (str): Base directory for all podcast analysis
        """
        self.podcast_name = podcast_name
        self.base_dir = base_dir
        self.episode_analyzer = PodcastAnalyzer()
        self.client = OpenAI()
        self.feed_manager = FeedManager()
        
        # Get feed information first
        self.feed_info = self.feed_manager.get_feed(podcast_name)
        if not self.feed_info:
            raise ValueError(f"Feed not found for podcast: {podcast_name}")
            
        # Then create directory structure
        self._create_directory_structure()

    def _create_directory_structure(self):
        """Create the organized directory structure for storing analysis results."""
        # Main directories
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Databases directory (shared across all podcasts)
        self.databases_dir = os.path.join(self.base_dir, "databases")
        os.makedirs(self.databases_dir, exist_ok=True)
        
        # Podcast-specific directories
        self.podcast_dir = os.path.join(self.base_dir, "podcasts", self.podcast_name)
        self.episodes_dir = os.path.join(self.podcast_dir, "episodes")
        self.summaries_dir = os.path.join(self.podcast_dir, "summaries")
        
        # Create all required directories
        os.makedirs(self.episodes_dir, exist_ok=True)
        os.makedirs(os.path.join(self.summaries_dir, "monthly"), exist_ok=True)
        os.makedirs(os.path.join(self.summaries_dir, "quarterly"), exist_ok=True)
        
        # Create podcast metadata file if it doesn't exist
        self.podcast_metadata_path = os.path.join(self.podcast_dir, "podcast_metadata.json")
        if not os.path.exists(self.podcast_metadata_path):
            with open(self.podcast_metadata_path, 'w') as f:
                json.dump({
                    'name': self.podcast_name,
                    'rss_url': self.feed_info['url'],
                    'first_analyzed': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'last_updated': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'total_episodes': 0
                }, f, indent=2)

    def _update_podcast_metadata(self, new_episodes: int = 0):
        """Update the podcast metadata file."""
        try:
            with open(self.podcast_metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['last_updated'] = time.strftime("%Y-%m-%d %H:%M:%S")
            metadata['total_episodes'] += new_episodes
            
            with open(self.podcast_metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            print(f"Error updating podcast metadata: {e}")

    def _get_episode_dir(self, episode: Dict) -> str:
        """Get the directory path for a specific episode."""
        date_str = time.strftime("%Y-%m-%d", episode['published_parsed'])
        safe_title = "".join(c for c in episode['title'] if c.isalnum() or c in (' ', '-', '_')).strip()
        episode_dir = os.path.join(self.episodes_dir, f"{date_str}_{safe_title}")
        os.makedirs(episode_dir, exist_ok=True)
        return episode_dir

    def fetch_feed(self) -> List[Dict]:
        """
        Fetch and parse the RSS feed.
        
        Returns:
            List[Dict]: List of episode metadata
        """
        try:
            feed = feedparser.parse(self.feed_info['url'])
            episodes = []
            
            for entry in feed.entries:
                episode = {
                    'title': entry.title,
                    'published': entry.published,
                    'published_parsed': entry.published_parsed,
                    'description': entry.description,
                    'audio_url': None,
                    'podcast_name': self.podcast_name
                }
                
                # Find the audio enclosure
                for link in entry.links:
                    if link.type.startswith('audio/'):
                        episode['audio_url'] = link.href
                        break
                
                if episode['audio_url']:
                    episodes.append(episode)
            
            return sorted(episodes, key=lambda x: x['published_parsed'])
            
        except Exception as e:
            print(f"Error fetching feed: {e}")
            return []

    def download_episode(self, episode: Dict) -> Optional[str]:
        """
        Download an episode's audio file.
        
        Args:
            episode (Dict): Episode metadata
            
        Returns:
            Optional[str]: Path to downloaded audio file
        """
        try:
            episode_dir = self._get_episode_dir(episode)
            audio_path = os.path.join(episode_dir, "audio.mp3")
            
            # Download if not already exists
            if not os.path.exists(audio_path):
                response = requests.get(episode['audio_url'], stream=True)
                response.raise_for_status()
                
                with open(audio_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            return audio_path
            
        except Exception as e:
            print(f"Error downloading episode {episode['title']}: {e}")
            return None

    def analyze_episode(self, episode: Dict, audio_path: str) -> Dict:
        """
        Analyze a single episode.
        
        Args:
            episode (Dict): Episode metadata
            audio_path (str): Path to audio file
            
        Returns:
            Dict: Analysis results
        """
        try:
            episode_dir = self._get_episode_dir(episode)
            
            # Get transcript and speaker identification
            transcription_results = self.episode_analyzer.transcribe_audio(audio_path, episode['title'])
            content_analysis = self.episode_analyzer.analyze_content(
                transcription_results["transcript"],
                transcription_results["speaker_identification"],
                episode['title']
            )
            
            # Save transcript
            transcript_path = os.path.join(episode_dir, "transcript.txt")
            with open(transcript_path, 'w') as f:
                f.write(transcription_results["transcript"])
            
            # Save analysis
            analysis_path = os.path.join(episode_dir, "analysis.json")
            analysis_data = {
                'title': episode['title'],
                'published_date': episode['published'],
                'speaker_identification': transcription_results["speaker_identification"],
                'content_analysis': content_analysis
            }
            
            with open(analysis_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            # Save metadata
            metadata_path = os.path.join(episode_dir, "metadata.json")
            metadata = {
                'title': episode['title'],
                'published_date': episode['published'],
                'description': episode['description'],
                'audio_url': episode['audio_url'],
                'duration': episode.get('duration', 'unknown'),
                'file_size': os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return analysis_data
            
        except Exception as e:
            print(f"Error analyzing episode {episode['title']}: {e}")
            return {}

    def _generate_summary(self, episodes: List[Dict], period: str):
        """Generate summary for a specific time period."""
        try:
            summary = {
                'period': period,
                'total_episodes': len(episodes),
                'episodes': []
            }
            
            for episode in episodes:
                episode_dir = self._get_episode_dir(episode)
                analysis_path = os.path.join(episode_dir, "analysis.json")
                
                if os.path.exists(analysis_path):
                    with open(analysis_path, 'r') as f:
                        analysis = json.load(f)
                        summary['episodes'].append({
                            'title': episode['title'],
                            'date': episode['published'],
                            'speakers': analysis['speakers'],
                            'main_points': analysis['content_analysis'].get('main_points', [])
                        })
            
            # Save summary
            summary_path = os.path.join(self.summaries_dir, f"{period}_summary.json")
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
                
        except Exception as e:
            print(f"Error generating summary for {period}: {e}")

    def analyze_feed(self, start_date: Optional[str] = None, end_date: Optional[str] = None):
        """
        Analyze all episodes in the feed within a date range.
        
        Args:
            start_date (Optional[str]): Start date in YYYY-MM-DD format
            end_date (Optional[str]): End date in YYYY-MM-DD format
        """
        # Check for episodes in date range
        episodes = self.feed_manager.check_for_updates(
            self.podcast_name,
            start_date=start_date,
            end_date=end_date
        )
        
        if not episodes:
            print(f"No episodes found in date range {start_date} to {end_date}")
            return
        
        print(f"Found {len(episodes)} episodes in date range")
        
        # Process episodes
        for episode in episodes:
            print(f"\nProcessing episode: {episode['title']} ({episode['published']})")
            
            # Download episode
            audio_path = self.download_episode(episode)
            if not audio_path:
                print(f"Skipping episode {episode['title']} - download failed")
                continue
            
            # Analyze episode
            analysis = self.analyze_episode(episode, audio_path)
            
            # Add delay to respect rate limits
            time.sleep(60)  # Wait 1 minute between episodes
        
        # Update feed statistics
        self.feed_manager.update_feed_stats(self.podcast_name, len(episodes))
        
        print("\nAnalysis complete! Results saved in:", self.podcast_dir) 