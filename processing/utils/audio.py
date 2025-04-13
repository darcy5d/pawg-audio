#!/usr/bin/env python3
import os
import asyncio
import logging
from typing import List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

async def get_audio_format(url: str) -> str:
    """
    Get audio format from URL or content type.
    
    Args:
        url: Audio URL
        
    Returns:
        str: Audio format extension
    """
    # Try to get format from URL
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    
    if ext in ['.mp3', '.m4a', '.wav', '.ogg', '.opus']:
        return ext[1:]  # Remove leading dot
    
    # Default to mp3
    return 'mp3'

async def convert_to_mp3(input_path: str) -> str:
    """
    Convert audio file to MP3 format.
    
    Args:
        input_path: Path to input audio file
        
    Returns:
        str: Path to converted MP3 file
    """
    output_path = os.path.splitext(input_path)[0] + '.mp3'
    
    if input_path == output_path:
        return input_path
    
    try:
        # Use ffmpeg for conversion
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-codec:a', 'libmp3lame',
            '-qscale:a', '2',  # High quality (0-9, lower is better)
            '-y',  # Overwrite output file
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error converting audio: {stderr.decode()}")
            raise Exception("Audio conversion failed")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error converting audio: {str(e)}")
        raise

async def optimize_audio(input_path: str) -> str:
    """
    Optimize audio file for processing.
    
    Args:
        input_path: Path to input audio file
        
    Returns:
        str: Path to optimized audio file
    """
    output_path = os.path.splitext(input_path)[0] + '_optimized' + os.path.splitext(input_path)[1]
    
    try:
        # Use ffmpeg to optimize audio
        # - Convert to mono
        # - Resample to 16kHz
        # - Normalize audio levels
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ac', '1',  # Mono
            '-ar', '16000',  # 16kHz
            '-filter:a', 'loudnorm',  # Normalize audio levels
            '-y',  # Overwrite output file
            output_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error optimizing audio: {stderr.decode()}")
            raise Exception("Audio optimization failed")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error optimizing audio: {str(e)}")
        raise

async def split_audio(input_path: str, max_size_mb: int = 25) -> List[str]:
    """
    Split audio file into smaller segments.
    
    Args:
        input_path: Path to input audio file
        max_size_mb: Maximum size of each segment in MB
        
    Returns:
        List[str]: List of paths to audio segments
    """
    # Check if file needs splitting
    file_size = os.path.getsize(input_path)
    if file_size <= max_size_mb * 1024 * 1024:
        return [input_path]
    
    # Get audio duration
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        logger.error(f"Error getting audio duration: {stderr.decode()}")
        raise Exception("Failed to get audio duration")
    
    duration = float(stdout.decode().strip())
    
    # Calculate segment duration based on file size and max segment size
    segment_duration = (max_size_mb * 1024 * 1024 * duration) / file_size
    
    # Split audio into segments
    segments = []
    base_path = os.path.splitext(input_path)[0]
    ext = os.path.splitext(input_path)[1]
    
    for i in range(0, int(duration), int(segment_duration)):
        segment_path = f"{base_path}_part{i}{ext}"
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', str(i),
            '-t', str(segment_duration),
            '-c', 'copy',  # Copy without re-encoding
            '-y',
            segment_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error splitting audio: {stderr.decode()}")
            # Clean up any created segments
            for segment in segments:
                os.remove(segment)
            raise Exception("Audio splitting failed")
        
        segments.append(segment_path)
    
    return segments 