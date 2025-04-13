"""
Transcript Segmenter Module

This module handles the segmentation of transcripts into logical chunks,
maintaining appropriate context and managing segment sizes for LLM processing.
"""

from typing import List, Dict, Optional, Tuple
import re
from dataclasses import dataclass
import math

@dataclass
class TranscriptSegment:
    """Represents a segment of transcript with associated metadata."""
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str] = None
    confidence: float = 0.0
    context: Dict = None
    metadata: Dict = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.metadata is None:
            self.metadata = {}

class TranscriptSegmenter:
    """Manages the segmentation of transcripts into logical chunks."""
    
    def __init__(
        self,
        max_tokens: int = 2000,
        overlap_tokens: int = 200,
        min_segment_tokens: int = 100
    ):
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.min_segment_tokens = min_segment_tokens
        self.speaker_pattern = re.compile(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*):\s*(.*)$')
        self.topic_change_patterns = [
            re.compile(r'\b(now|next|moving on|let\'s talk about|turning to)\b', re.IGNORECASE),
            re.compile(r'\b(question|answer|discussion|point)\b', re.IGNORECASE),
            re.compile(r'[.!?]\s*$')
        ]

    def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text string."""
        # Rough estimation: 1 token ≈ 4 characters
        return math.ceil(len(text) / 4)

    def find_topic_changes(self, text: str) -> List[int]:
        """Find potential topic change points in the text."""
        changes = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            for pattern in self.topic_change_patterns:
                if pattern.search(line):
                    changes.append(i)
                    break
        
        return changes

    def find_speaker_changes(self, text: str) -> List[int]:
        """Find speaker change points in the text."""
        changes = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            if self.speaker_pattern.match(line):
                changes.append(i)
        
        return changes

    def create_segments(
        self,
        transcript: str,
        timestamps: Optional[List[Tuple[float, float]]] = None
    ) -> List[TranscriptSegment]:
        """Create logical segments from a transcript."""
        segments = []
        lines = transcript.split('\n')
        current_segment = []
        current_start = 0.0
        current_end = 0.0
        
        # Find all potential break points
        topic_changes = self.find_topic_changes(transcript)
        speaker_changes = self.find_speaker_changes(transcript)
        break_points = sorted(set(topic_changes + speaker_changes))
        
        for i, line in enumerate(lines):
            current_segment.append(line)
            
            # Update timestamps if available
            if timestamps and i < len(timestamps):
                current_end = timestamps[i][1]
            
            # Check if we should create a new segment
            should_break = (
                i in break_points or
                self.estimate_tokens('\n'.join(current_segment)) >= self.max_tokens
            )
            
            if should_break and len(current_segment) >= self.min_segment_tokens:
                # Create new segment
                segment_text = '\n'.join(current_segment)
                segments.append(TranscriptSegment(
                    text=segment_text,
                    start_time=current_start,
                    end_time=current_end,
                    metadata={
                        'line_start': i - len(current_segment) + 1,
                        'line_end': i
                    }
                ))
                
                # Start new segment with overlap
                overlap_lines = max(1, self.overlap_tokens // self.estimate_tokens(line))
                current_segment = current_segment[-overlap_lines:]
                current_start = current_end
        
        # Add final segment if there's remaining text
        if current_segment:
            segment_text = '\n'.join(current_segment)
            segments.append(TranscriptSegment(
                text=segment_text,
                start_time=current_start,
                end_time=current_end,
                metadata={
                    'line_start': len(lines) - len(current_segment),
                    'line_end': len(lines) - 1
                }
            ))
        
        return segments

    def add_context_to_segments(
        self,
        segments: List[TranscriptSegment],
        context_window: int = 2
    ) -> List[TranscriptSegment]:
        """Add context from surrounding segments to each segment."""
        for i, segment in enumerate(segments):
            # Get context from previous segments
            prev_context = []
            for j in range(max(0, i - context_window), i):
                prev_context.append(segments[j].text)
            
            # Get context from next segments
            next_context = []
            for j in range(i + 1, min(len(segments), i + context_window + 1)):
                next_context.append(segments[j].text)
            
            # Add context to segment
            segment.context = {
                'previous': prev_context,
                'next': next_context
            }
        
        return segments

    def optimize_segments(
        self,
        segments: List[TranscriptSegment],
        target_tokens: int = 1500
    ) -> List[TranscriptSegment]:
        """Optimize segment sizes to be closer to target token count."""
        optimized = []
        current_segment = []
        current_tokens = 0
        
        for segment in segments:
            segment_tokens = self.estimate_tokens(segment.text)
            
            if current_tokens + segment_tokens <= target_tokens:
                current_segment.append(segment)
                current_tokens += segment_tokens
            else:
                if current_segment:
                    # Merge current segments
                    merged_text = '\n'.join(s.text for s in current_segment)
                    merged_segment = TranscriptSegment(
                        text=merged_text,
                        start_time=current_segment[0].start_time,
                        end_time=current_segment[-1].end_time,
                        metadata={'merged_from': len(current_segment)}
                    )
                    optimized.append(merged_segment)
                
                current_segment = [segment]
                current_tokens = segment_tokens
        
        # Add final merged segment
        if current_segment:
            merged_text = '\n'.join(s.text for s in current_segment)
            merged_segment = TranscriptSegment(
                text=merged_text,
                start_time=current_segment[0].start_time,
                end_time=current_segment[-1].end_time,
                metadata={'merged_from': len(current_segment)}
            )
            optimized.append(merged_segment)
        
        return optimized 