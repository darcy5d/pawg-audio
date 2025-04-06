from podcast_analyzer import PodcastAnalyzer
import json
from pathlib import Path

def main():
    # Define speaker context for this specific podcast
    speaker_context = {
        "Host 1": "Grant Williams - Main host of The End Game podcast, known for his expertise in macroeconomics and markets",
        "Host 2": "Bill Fleckenstein - Co-host of The End Game podcast, veteran investor and market commentator",
        "Guest": "Fred Hickey - Technology analyst and editor of the High-Tech Strategist newsletter, known for his expertise in technology stocks and market analysis"
    }
    
    # Initialize the analyzer with speaker context
    analyzer = PodcastAnalyzer(speaker_context=speaker_context)
    
    # Path to the podcast file
    podcast_path = "the_grant_williams_p_the_end_game_ep_55_f.mp3"
    
    # Verify the file exists
    if not Path(podcast_path).exists():
        print(f"❌ Error: File not found at {podcast_path}")
        return
    
    print(f"✅ Found podcast file: {podcast_path}")
    print("Starting analysis... This may take a few minutes...")
    
    try:
        # Analyze the episode
        results = analyzer.analyze_episode(podcast_path)
        
        # Save results to a JSON file
        output_file = "podcast_analysis_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Analysis complete!")
        print(f"Results saved to: {output_file}")
        
        # Print a summary of the results
        print("\n=== Analysis Summary ===")
        print("\nTranscript Preview:")
        print(results["transcription"]["transcript"][:500] + "...")
        
        print("\nSpeaker Identification Preview:")
        print(results["transcription"]["speaker_identification"][:500] + "...")
        
        print("\nContent Analysis Preview:")
        print(results["analysis"]["content_analysis"][:500] + "...")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")

if __name__ == "__main__":
    main() 