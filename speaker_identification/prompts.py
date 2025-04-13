"""
Prompts Module

This module contains specialized prompts for speaker identification and diarization
across different LLM providers (OpenAI, Anthropic, DeepSeek).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class SpeakerIdentificationPrompts:
    """Collection of prompts for speaker identification across different LLM providers."""
    
    @staticmethod
    def get_openai_prompt(transcript: str, context: Optional[Dict] = None) -> str:
        """Get the OpenAI-specific prompt for speaker identification."""
        return f"""Analyze the following podcast transcript segment and identify the speakers.
For each speaker, provide:
1. Their name (if mentioned or can be inferred)
2. Their role or title (if mentioned)
3. Their organization (if mentioned)
4. Their expertise areas (if mentioned)
5. A confidence score (0-1) for the identification
6. Any aliases or alternative names used

Transcript:
{transcript}

Previous context:
{context.get('previous', 'No previous context') if context else 'No context'}

Next context:
{context.get('next', 'No next context') if context else 'No context'}

Format your response as JSON with the following structure:
{{
    "speakers": [
        {{
            "name": "string",
            "role": "string",
            "organization": "string",
            "expertise": ["string"],
            "confidence": float,
            "aliases": ["string"],
            "evidence": "string"
        }}
    ],
    "speaker_changes": [
        {{
            "line": int,
            "from_speaker": "string",
            "to_speaker": "string",
            "confidence": float
        }}
    ]
}}"""

    @staticmethod
    def get_anthropic_prompt(transcript: str, context: Optional[Dict] = None) -> str:
        """Get the Anthropic-specific prompt for speaker identification."""
        return f"""<task>
Analyze this podcast transcript segment to identify speakers and their characteristics.
</task>

<transcript>
{transcript}
</transcript>

<context>
Previous: {context.get('previous', 'No previous context') if context else 'No context'}
Next: {context.get('next', 'No next context') if context else 'No context'}
</context>

<instructions>
1. Identify all speakers in the transcript
2. For each speaker, determine:
   - Full name and any aliases
   - Professional role or title
   - Organization affiliation
   - Areas of expertise
   - Confidence in identification (0-1)
3. Note speaker changes and transitions
4. Provide evidence for each identification
5. Format response as structured JSON
</instructions>

<format>
{{
    "analysis": {{
        "speakers": [
            {{
                "identity": {{
                    "primary_name": "string",
                    "aliases": ["string"],
                    "role": "string",
                    "organization": "string",
                    "expertise": ["string"]
                }},
                "confidence": float,
                "evidence": ["string"]
            }}
        ],
        "transitions": [
            {{
                "location": "string",
                "from_speaker": "string",
                "to_speaker": "string",
                "confidence": float
            }}
        ]
    }}
}}
</format>"""

    @staticmethod
    def get_deepseek_prompt(transcript: str, context: Optional[Dict] = None) -> str:
        """Get the DeepSeek-specific prompt for speaker identification."""
        return f"""# Speaker Identification Analysis

## Transcript Segment
{transcript}

## Context
Previous: {context.get('previous', 'No previous context') if context else 'No context'}
Next: {context.get('next', 'No next context') if context else 'No context'}

## Task
Perform a detailed speaker identification analysis of the provided transcript segment.
Focus on:
1. Speaker names and aliases
2. Professional roles and affiliations
3. Areas of expertise
4. Speaking patterns and characteristics
5. Confidence levels for each identification

## Required Output Format
```json
{{
    "speaker_analysis": {{
        "identified_speakers": [
            {{
                "name": "string",
                "aliases": ["string"],
                "role": "string",
                "organization": "string",
                "expertise": ["string"],
                "confidence": float,
                "speaking_style": "string",
                "evidence": ["string"]
            }}
        ],
        "speaker_transitions": [
            {{
                "position": "string",
                "previous_speaker": "string",
                "next_speaker": "string",
                "transition_confidence": float,
                "transition_evidence": "string"
            }}
        ],
        "analysis_confidence": float,
        "key_observations": ["string"]
    }}
}}
```"""

    @staticmethod
    def get_metadata_extraction_prompt(metadata: Dict) -> str:
        """Get a prompt for extracting speaker information from episode metadata."""
        return f"""Analyze the following podcast episode metadata to identify potential speakers
and their characteristics:

Title: {metadata.get('title', 'N/A')}
Description: {metadata.get('description', 'N/A')}
Host: {metadata.get('host', 'N/A')}
Guests: {metadata.get('guests', 'N/A')}

Extract all potential speaker information, including:
1. Names and aliases
2. Roles and titles
3. Organizations
4. Areas of expertise
5. Relationship to the episode (host, guest, etc.)

Format your response as JSON:
{{
    "speakers": [
        {{
            "name": "string",
            "aliases": ["string"],
            "role": "string",
            "organization": "string",
            "expertise": ["string"],
            "episode_role": "string",
            "confidence": float
        }}
    ],
    "relationships": [
        {{
            "speaker1": "string",
            "speaker2": "string",
            "relationship": "string",
            "confidence": float
        }}
    ]
}}"""

    @staticmethod
    def get_speaker_verification_prompt(
        speaker1: Dict,
        speaker2: Dict,
        context: Optional[Dict] = None
    ) -> str:
        """Get a prompt for verifying if two speaker identifications refer to the same person."""
        return f"""Analyze these two speaker identifications and determine if they refer to the same person.

Speaker 1:
{{
    "name": "{speaker1.get('name', 'Unknown')}",
    "aliases": {speaker1.get('aliases', [])},
    "role": "{speaker1.get('role', 'Unknown')}",
    "organization": "{speaker1.get('organization', 'Unknown')}",
    "expertise": {speaker1.get('expertise', [])}
}}

Speaker 2:
{{
    "name": "{speaker2.get('name', 'Unknown')}",
    "aliases": {speaker2.get('aliases', [])},
    "role": "{speaker2.get('role', 'Unknown')}",
    "organization": "{speaker2.get('organization', 'Unknown')}",
    "expertise": {speaker2.get('expertise', [])}
}}

Context:
{context if context else 'No additional context'}

Determine if these are the same person and provide:
1. A confidence score (0-1)
2. Evidence for your decision
3. Suggested merged profile if they are the same person

Format your response as JSON:
{{
    "same_person": boolean,
    "confidence": float,
    "evidence": ["string"],
    "merged_profile": {{
        "name": "string",
        "aliases": ["string"],
        "role": "string",
        "organization": "string",
        "expertise": ["string"]
    }}
}}""" 