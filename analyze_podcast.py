import os
from datetime import datetime
from podcast_analyzer import PodcastAnalyzer
import json

def analyze_february_episodes():
    base_dir = "podcast_analysis/podcasts/grant_williams/episodes"
    
    # Get all February 2025 episodes
    february_episodes = [
        d for d in os.listdir(base_dir)
        if d.startswith("2025-02-") and os.path.isdir(os.path.join(base_dir, d))
    ]
    
    analyzer = PodcastAnalyzer()
    
    for episode_dir in february_episodes:
        print(f"\nAnalyzing episode: {episode_dir}")
        
        # Find the audio file in the episode directory
        episode_path = os.path.join(base_dir, episode_dir)
        audio_files = [f for f in os.listdir(episode_path) if f.endswith('.mp3')]
        
        if not audio_files:
            print(f"No audio file found in {episode_dir}")
            continue
            
        audio_path = os.path.join(episode_path, audio_files[0])
        
        try:
            # Analyze the episode
            analysis_result = analyzer.analyze_episode(audio_path)
            
            # Save the analysis results
            output_dir = os.path.join("podcast_analysis/podcasts/grant_williams/summaries", episode_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            with open(os.path.join(output_dir, "analysis.json"), "w") as f:
                json.dump(analysis_result, f, indent=2)
                
            print(f"Successfully analyzed and saved results for {episode_dir}")
            
        except Exception as e:
            print(f"Error analyzing {episode_dir}: {str(e)}")

if __name__ == "__main__":
    analyze_february_episodes() 