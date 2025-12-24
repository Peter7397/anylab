"""
Video Transcript Extractor

This module provides comprehensive video transcript extraction capabilities
including audio extraction, speech recognition, and transcript processing.
"""

import logging
import os
import tempfile
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import re
import subprocess
import wave
import librosa
import numpy as np
from pydub import AudioSegment
import speech_recognition as sr
from moviepy.editor import VideoFileClip
import whisper
import torch

logger = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    """Video metadata structure"""
    title: str
    duration: float
    file_size: int
    file_hash: str
    format: str
    resolution: Tuple[int, int]
    fps: float
    bitrate: int
    audio_codec: str
    video_codec: str
    has_audio: bool
    has_video: bool
    language: Optional[str]
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]


@dataclass
class TranscriptSegment:
    """Transcript segment structure"""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker: Optional[str]
    language: Optional[str]
    words: List[Dict[str, Any]]


@dataclass
class Transcript:
    """Transcript structure"""
    metadata: VideoMetadata
    segments: List[TranscriptSegment]
    full_text: str
    language: str
    confidence: float
    processing_time: float
    word_count: int
    speaker_count: int
    quality_score: float


class VideoTranscriptExtractor:
    """Comprehensive video transcript extractor"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize video transcript extractor with configuration"""
        self.config = config or {}
        self.whisper_enabled = self.config.get('whisper_enabled', True)
        self.speech_recognition_enabled = self.config.get('speech_recognition_enabled', True)
        self.speaker_diarization_enabled = self.config.get('speaker_diarization_enabled', False)
        self.language_detection_enabled = self.config.get('language_detection_enabled', True)
        self.audio_preprocessing_enabled = self.config.get('audio_preprocessing_enabled', True)
        
        # Whisper configuration
        self.whisper_model = self.config.get('whisper_model', 'base')
        self.whisper_language = self.config.get('whisper_language', None)
        self.whisper_task = self.config.get('whisper_task', 'transcribe')
        
        # Speech recognition configuration
        self.sr_engine = self.config.get('sr_engine', 'google')
        self.sr_language = self.config.get('sr_language', 'en-US')
        
        # Audio processing configuration
        self.audio_sample_rate = self.config.get('audio_sample_rate', 16000)
        self.audio_channels = self.config.get('audio_channels', 1)
        self.audio_format = self.config.get('audio_format', 'wav')
        
        # Processing configuration
        self.max_duration = self.config.get('max_duration', 3600)  # 1 hour
        self.chunk_duration = self.config.get('chunk_duration', 30)  # 30 seconds
        self.min_confidence = self.config.get('min_confidence', 0.5)
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Video Transcript Extractor initialized with configuration")
    
    def _initialize_components(self):
        """Initialize processing components"""
        try:
            # Initialize Whisper model
            if self.whisper_enabled:
                self.whisper_model_instance = whisper.load_model(self.whisper_model)
                logger.info(f"Whisper model '{self.whisper_model}' loaded")
            
            # Initialize speech recognition
            if self.speech_recognition_enabled:
                self.sr_recognizer = sr.Recognizer()
                logger.info("Speech recognition initialized")
            
            # Initialize speaker diarization
            if self.speaker_diarization_enabled:
                # This would require additional libraries like pyannote.audio
                logger.info("Speaker diarization enabled (requires pyannote.audio)")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def extract_transcript(self, video_path: str) -> Transcript:
        """Extract transcript from video file"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting transcript extraction for: {video_path}")
            
            # Extract video metadata
            metadata = self._extract_video_metadata(video_path)
            
            # Extract audio from video
            audio_path = self._extract_audio(video_path)
            
            # Detect language if enabled
            language = self._detect_language(audio_path) if self.language_detection_enabled else None
            
            # Extract transcript using multiple methods
            segments = self._extract_transcript_segments(audio_path, language)
            
            # Process segments
            processed_segments = self._process_segments(segments)
            
            # Generate full text
            full_text = self._generate_full_text(processed_segments)
            
            # Calculate statistics
            word_count = len(full_text.split())
            speaker_count = len(set(seg.speaker for seg in processed_segments if seg.speaker))
            confidence = self._calculate_average_confidence(processed_segments)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(metadata, processed_segments, full_text)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create transcript object
            transcript = Transcript(
                metadata=metadata,
                segments=processed_segments,
                full_text=full_text,
                language=language or 'unknown',
                confidence=confidence,
                processing_time=processing_time,
                word_count=word_count,
                speaker_count=speaker_count,
                quality_score=quality_score
            )
            
            logger.info(f"Transcript extraction completed in {processing_time:.2f} seconds")
            return transcript
            
        except Exception as e:
            logger.error(f"Error extracting transcript: {e}")
            raise
        finally:
            # Clean up temporary files
            if 'audio_path' in locals() and os.path.exists(audio_path):
                os.remove(audio_path)
    
    def _extract_video_metadata(self, video_path: str) -> VideoMetadata:
        """Extract video metadata"""
        try:
            # Get file information
            file_size = os.path.getsize(video_path)
            file_hash = self._calculate_file_hash(video_path)
            
            # Use moviepy to get video information
            with VideoFileClip(video_path) as clip:
                duration = clip.duration
                fps = clip.fps
                size = clip.size
                
                # Get audio information
                has_audio = clip.audio is not None
                audio_codec = clip.audio.codec if has_audio else None
                
                # Get video information
                has_video = True
                video_codec = clip.codec
                
                # Get bitrate (approximate)
                bitrate = int(file_size * 8 / duration) if duration > 0 else 0
            
            # Get file format
            file_format = Path(video_path).suffix.lower()
            
            # Get file dates
            stat = os.stat(video_path)
            creation_date = datetime.fromtimestamp(stat.st_ctime)
            modification_date = datetime.fromtimestamp(stat.st_mtime)
            
            return VideoMetadata(
                title=Path(video_path).stem,
                duration=duration,
                file_size=file_size,
                file_hash=file_hash,
                format=file_format,
                resolution=size,
                fps=fps,
                bitrate=bitrate,
                audio_codec=audio_codec,
                video_codec=video_codec,
                has_audio=has_audio,
                has_video=has_video,
                language=None,  # Will be detected later
                creation_date=creation_date,
                modification_date=modification_date
            )
            
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
            raise
    
    def _extract_audio(self, video_path: str) -> str:
        """Extract audio from video file"""
        try:
            # Create temporary audio file
            temp_dir = tempfile.gettempdir()
            audio_filename = f"audio_{hashlib.md5(video_path.encode()).hexdigest()[:8]}.{self.audio_format}"
            audio_path = os.path.join(temp_dir, audio_filename)
            
            # Extract audio using moviepy
            with VideoFileClip(video_path) as clip:
                if clip.audio is None:
                    raise ValueError("Video file has no audio track")
                
                # Extract audio
                audio_clip = clip.audio
                
                # Convert to desired format
                if self.audio_preprocessing_enabled:
                    # Resample and convert to mono
                    audio_clip = audio_clip.set_fps(self.audio_sample_rate)
                    if self.audio_channels == 1:
                        audio_clip = audio_clip.set_channels(1)
                
                # Write audio file
                audio_clip.write_audiofile(
                    audio_path,
                    fps=self.audio_sample_rate,
                    nbytes=2,  # 16-bit
                    codec='pcm_s16le' if self.audio_format == 'wav' else 'mp3'
                )
                
                audio_clip.close()
            
            logger.info(f"Audio extracted to: {audio_path}")
            return audio_path
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    def _detect_language(self, audio_path: str) -> Optional[str]:
        """Detect language of audio"""
        try:
            if not self.whisper_enabled:
                return None
            
            # Use Whisper to detect language
            result = self.whisper_model_instance.transcribe(
                audio_path,
                language=None,  # Auto-detect
                task='transcribe',
                verbose=False
            )
            
            detected_language = result.get('language', None)
            logger.info(f"Detected language: {detected_language}")
            
            return detected_language
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return None
    
    def _extract_transcript_segments(self, audio_path: str, language: Optional[str]) -> List[TranscriptSegment]:
        """Extract transcript segments using multiple methods"""
        segments = []
        
        # Try Whisper first (most accurate)
        if self.whisper_enabled:
            try:
                whisper_segments = self._extract_with_whisper(audio_path, language)
                segments.extend(whisper_segments)
                logger.info(f"Extracted {len(whisper_segments)} segments with Whisper")
            except Exception as e:
                logger.error(f"Error with Whisper extraction: {e}")
        
        # Fallback to speech recognition
        if not segments and self.speech_recognition_enabled:
            try:
                sr_segments = self._extract_with_speech_recognition(audio_path)
                segments.extend(sr_segments)
                logger.info(f"Extracted {len(sr_segments)} segments with Speech Recognition")
            except Exception as e:
                logger.error(f"Error with Speech Recognition extraction: {e}")
        
        # Sort segments by start time
        segments.sort(key=lambda x: x.start_time)
        
        return segments
    
    def _extract_with_whisper(self, audio_path: str, language: Optional[str]) -> List[TranscriptSegment]:
        """Extract transcript using Whisper"""
        try:
            # Transcribe with Whisper
            result = self.whisper_model_instance.transcribe(
                audio_path,
                language=language,
                task=self.whisper_task,
                verbose=False
            )
            
            segments = []
            for segment in result['segments']:
                # Extract words if available
                words = []
                if 'words' in segment:
                    for word in segment['words']:
                        words.append({
                            'word': word['word'],
                            'start': word['start'],
                            'end': word['end'],
                            'probability': word.get('probability', 1.0)
                        })
                
                transcript_segment = TranscriptSegment(
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'].strip(),
                    confidence=segment.get('avg_logprob', 0.0),
                    speaker=None,  # Whisper doesn't provide speaker info
                    language=result.get('language', language),
                    words=words
                )
                
                segments.append(transcript_segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"Error with Whisper extraction: {e}")
            raise
    
    def _extract_with_speech_recognition(self, audio_path: str) -> List[TranscriptSegment]:
        """Extract transcript using speech recognition"""
        try:
            segments = []
            
            # Load audio file
            audio = AudioSegment.from_file(audio_path)
            
            # Split audio into chunks
            chunk_length = self.chunk_duration * 1000  # Convert to milliseconds
            chunks = [audio[i:i + chunk_length] for i in range(0, len(audio), chunk_length)]
            
            for i, chunk in enumerate(chunks):
                try:
                    # Convert chunk to WAV format
                    chunk_path = tempfile.mktemp(suffix='.wav')
                    chunk.export(chunk_path, format='wav')
                    
                    # Recognize speech
                    with sr.AudioFile(chunk_path) as source:
                        audio_data = self.sr_recognizer.record(source)
                    
                    # Use Google Speech Recognition
                    text = self.sr_recognizer.recognize_google(
                        audio_data,
                        language=self.sr_language
                    )
                    
                    if text.strip():
                        start_time = i * self.chunk_duration
                        end_time = min((i + 1) * self.chunk_duration, len(audio) / 1000)
                        
                        segment = TranscriptSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=text.strip(),
                            confidence=0.8,  # Default confidence for Google SR
                            speaker=None,
                            language=self.sr_language,
                            words=[]
                        )
                        
                        segments.append(segment)
                    
                    # Clean up chunk file
                    os.remove(chunk_path)
                    
                except sr.UnknownValueError:
                    # Speech not recognized
                    continue
                except sr.RequestError as e:
                    logger.error(f"Speech recognition error: {e}")
                    continue
            
            return segments
            
        except Exception as e:
            logger.error(f"Error with speech recognition extraction: {e}")
            raise
    
    def _process_segments(self, segments: List[TranscriptSegment]) -> List[TranscriptSegment]:
        """Process and clean transcript segments"""
        processed_segments = []
        
        for segment in segments:
            # Clean text
            cleaned_text = self._clean_text(segment.text)
            
            if not cleaned_text:
                continue
            
            # Filter by confidence
            if segment.confidence < self.min_confidence:
                continue
            
            # Update segment with cleaned text
            segment.text = cleaned_text
            
            # Perform speaker diarization if enabled
            if self.speaker_diarization_enabled:
                segment.speaker = self._identify_speaker(segment)
            
            processed_segments.append(segment)
        
        return processed_segments
    
    def _clean_text(self, text: str) -> str:
        """Clean transcript text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:]', '', text)
        
        # Remove repeated words (common in speech recognition)
        words = text.split()
        cleaned_words = []
        prev_word = None
        
        for word in words:
            if word.lower() != prev_word:
                cleaned_words.append(word)
                prev_word = word.lower()
        
        return ' '.join(cleaned_words)
    
    def _identify_speaker(self, segment: TranscriptSegment) -> Optional[str]:
        """Identify speaker for segment"""
        # This is a placeholder for speaker diarization
        # In a real implementation, you would use libraries like pyannote.audio
        return f"Speaker_{hash(segment.text) % 3}"  # Simple hash-based speaker ID
    
    def _generate_full_text(self, segments: List[TranscriptSegment]) -> str:
        """Generate full text from segments"""
        full_text = ""
        
        for segment in segments:
            if segment.text:
                full_text += segment.text + " "
        
        return full_text.strip()
    
    def _calculate_average_confidence(self, segments: List[TranscriptSegment]) -> float:
        """Calculate average confidence score"""
        if not segments:
            return 0.0
        
        total_confidence = sum(seg.confidence for seg in segments)
        return total_confidence / len(segments)
    
    def _calculate_quality_score(self, metadata: VideoMetadata, segments: List[TranscriptSegment], text: str) -> float:
        """Calculate quality score for the transcript"""
        score = 0.0
        
        # Base score
        score += 0.1
        
        # Audio quality score
        if metadata.has_audio:
            score += 0.2
        
        # Duration score
        if metadata.duration > 0:
            score += 0.1
        
        # Text content score
        if text and len(text) > 100:
            score += 0.2
        
        # Segment count score
        if len(segments) > 0:
            score += 0.1
        
        # Confidence score
        avg_confidence = self._calculate_average_confidence(segments)
        score += avg_confidence * 0.3
        
        return min(score, 1.0)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def export_transcript(self, transcript: Transcript, format: str = 'json') -> str:
        """Export transcript in specified format"""
        if format.lower() == 'json':
            return self._export_json(transcript)
        elif format.lower() == 'srt':
            return self._export_srt(transcript)
        elif format.lower() == 'vtt':
            return self._export_vtt(transcript)
        elif format.lower() == 'txt':
            return self._export_txt(transcript)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, transcript: Transcript) -> str:
        """Export transcript as JSON"""
        data = {
            'metadata': {
                'title': transcript.metadata.title,
                'duration': transcript.metadata.duration,
                'language': transcript.language,
                'confidence': transcript.confidence,
                'word_count': transcript.word_count,
                'speaker_count': transcript.speaker_count,
                'quality_score': transcript.quality_score,
                'processing_time': transcript.processing_time
            },
            'segments': [
                {
                    'start_time': seg.start_time,
                    'end_time': seg.end_time,
                    'text': seg.text,
                    'confidence': seg.confidence,
                    'speaker': seg.speaker,
                    'language': seg.language,
                    'words': seg.words
                }
                for seg in transcript.segments
            ],
            'full_text': transcript.full_text
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_srt(self, transcript: Transcript) -> str:
        """Export transcript as SRT subtitle format"""
        srt_content = ""
        
        for i, segment in enumerate(transcript.segments, 1):
            start_time = self._format_srt_time(segment.start_time)
            end_time = self._format_srt_time(segment.end_time)
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{segment.text}\n\n"
        
        return srt_content
    
    def _export_vtt(self, transcript: Transcript) -> str:
        """Export transcript as WebVTT format"""
        vtt_content = "WEBVTT\n\n"
        
        for segment in transcript.segments:
            start_time = self._format_vtt_time(segment.start_time)
            end_time = self._format_vtt_time(segment.end_time)
            
            vtt_content += f"{start_time} --> {end_time}\n"
            vtt_content += f"{segment.text}\n\n"
        
        return vtt_content
    
    def _export_txt(self, transcript: Transcript) -> str:
        """Export transcript as plain text"""
        return transcript.full_text
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format time for WebVTT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
