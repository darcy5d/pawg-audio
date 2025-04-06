from podcast_analyzer import PodcastAnalyzer
import json

def main():
    # Initialize the analyzer
    analyzer = PodcastAnalyzer()
    
    # Path to your podcast audio file
    audio_path = "path/to/your/podcast.mp3"
    
    # Analyze the episode
    results = analyzer.analyze_episode(audio_path)
    
    # Print the results in a formatted way
    print("\n=== Podcast Analysis Results ===\n")
    
    print("=== Transcription ===")
    print(results["transcription"]["transcript"])
    print("\n=== Speaker Identification ===")
    print(results["transcription"]["speaker_identification"])
    print("\n=== Content Analysis ===")
    print(results["analysis"]["content_analysis"])
    
    # Optionally save results to a file
    with open("analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main() 