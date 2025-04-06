import os
import json
from typing import Dict, List, Optional
import openai
from dotenv import load_dotenv
import whisper
from pydub import AudioSegment
import numpy as np
import time

class PodcastAnalyzer:
    def __init__(self, speaker_context: Optional[Dict] = None):
        load_dotenv()
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.whisper_model = whisper.load_model("base", device="cpu")
        self.speaker_context = speaker_context or {}
        
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
    
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Transcribe the podcast audio and identify speakers."""
        print("Starting transcription...")
        
        # Transcribe using Whisper
        result = self.whisper_model.transcribe(audio_path)
        print("Transcription complete. Analyzing speakers...")
        
        # Split transcript into smaller chunks
        transcript_chunks = self.split_text(result['text'], chunk_size=2000)
        print(f"Split transcript into {len(transcript_chunks)} chunks for processing")
        
        # Prepare speaker context for diarization
        context_str = ""
        if self.speaker_context:
            context_str = "\nSpeaker Context:\n"
            for role, info in self.speaker_context.items():
                context_str += f"- {role}: {info}\n"
        
        # Process each chunk
        all_speaker_identifications = []
        for i, chunk in enumerate(transcript_chunks, 1):
            print(f"Processing chunk {i}/{len(transcript_chunks)}...")
            
            diarization_prompt = f"""
            Identify speakers in this podcast segment. Format as "Speaker: Text".
            {context_str}
            Segment: {chunk}
            """
            
            try:
                diarization_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use faster, cheaper model for initial processing
                    messages=[
                        {"role": "system", "content": "Identify speakers in podcast segments."},
                        {"role": "user", "content": diarization_prompt}
                    ],
                    max_tokens=1000
                )
                all_speaker_identifications.append(diarization_response.choices[0].message.content)
                time.sleep(2)  # Increased delay between requests
            except Exception as e:
                print(f"Error processing chunk {i}: {str(e)}")
                all_speaker_identifications.append(f"Error processing chunk {i}")
        
        return {
            "transcript": result['text'],
            "speaker_identification": "\n\n".join(all_speaker_identifications)
        }
    
    def analyze_content(self, transcript: str, speaker_identification: str) -> Dict:
        """Analyze the content for main points, worldview, and expertise."""
        print("Analyzing content...")
        
        # Split analysis into smaller chunks
        transcript_chunks = self.split_text(transcript, chunk_size=2000)
        print(f"Split analysis into {len(transcript_chunks)} chunks")
        
        all_analyses = []
        for i, chunk in enumerate(transcript_chunks, 1):
            print(f"Analyzing chunk {i}/{len(transcript_chunks)}...")
            
            analysis_prompt = f"""
            Analyze Fred Hickey's views in this segment:
            1. Main points
            2. Expertise shown
            3. Confidence level
            4. Market implications

            Segment: {chunk}
            """
            
            try:
                analysis_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Use faster, cheaper model for initial processing
                    messages=[
                        {"role": "system", "content": "Analyze podcast content."},
                        {"role": "user", "content": analysis_prompt}
                    ],
                    max_tokens=1000
                )
                all_analyses.append(analysis_response.choices[0].message.content)
                time.sleep(2)  # Increased delay between requests
            except Exception as e:
                print(f"Error analyzing chunk {i}: {str(e)}")
                all_analyses.append(f"Error analyzing chunk {i}")
        
        return {
            "content_analysis": "\n\n".join(all_analyses)
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