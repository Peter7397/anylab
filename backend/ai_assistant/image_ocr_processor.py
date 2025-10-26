"""
Image OCR Processing System

This module provides comprehensive image OCR processing capabilities
including text extraction, image preprocessing, and OCR optimization.
"""

import logging
import os
import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import easyocr
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Image metadata structure"""
    filename: str
    file_size: int
    file_hash: str
    format: str
    dimensions: Tuple[int, int]
    color_mode: str
    dpi: Tuple[int, int]
    has_transparency: bool
    creation_date: Optional[datetime]
    modification_date: Optional[datetime]


@dataclass
class OCRResult:
    """OCR result structure"""
    text: str
    confidence: float
    bounding_boxes: List[Dict[str, Any]]
    words: List[Dict[str, Any]]
    lines: List[Dict[str, Any]]
    paragraphs: List[Dict[str, Any]]
    language: str
    processing_time: float
    quality_score: float


@dataclass
class ProcessedImage:
    """Processed image structure"""
    metadata: ImageMetadata
    ocr_result: OCRResult
    preprocessed_image: Optional[np.ndarray]
    processing_steps: List[str]
    quality_metrics: Dict[str, float]


class ImageOCRProcessor:
    """Comprehensive image OCR processor"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize image OCR processor with configuration"""
        self.config = config or {}
        self.tesseract_enabled = self.config.get('tesseract_enabled', True)
        self.easyocr_enabled = self.config.get('easyocr_enabled', True)
        self.trocr_enabled = self.config.get('trocr_enabled', False)
        self.preprocessing_enabled = self.config.get('preprocessing_enabled', True)
        self.language_detection_enabled = self.config.get('language_detection_enabled', True)
        
        # Tesseract configuration
        self.tesseract_language = self.config.get('tesseract_language', 'eng')
        self.tesseract_config = self.config.get('tesseract_config', '--psm 6')
        self.tesseract_oem = self.config.get('tesseract_oem', 3)
        
        # EasyOCR configuration
        self.easyocr_languages = self.config.get('easyocr_languages', ['en'])
        self.easyocr_gpu = self.config.get('easyocr_gpu', False)
        
        # TrOCR configuration
        self.trocr_model = self.config.get('trocr_model', 'microsoft/trocr-base-printed')
        
        # Preprocessing configuration
        self.resize_enabled = self.config.get('resize_enabled', True)
        self.resize_factor = self.config.get('resize_factor', 2.0)
        self.denoise_enabled = self.config.get('denoise_enabled', True)
        self.contrast_enhancement_enabled = self.config.get('contrast_enhancement_enabled', True)
        self.binarization_enabled = self.config.get('binarization_enabled', True)
        self.deskew_enabled = self.config.get('deskew_enabled', True)
        
        # Quality thresholds
        self.min_confidence = self.config.get('min_confidence', 0.5)
        self.min_text_length = self.config.get('min_text_length', 3)
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Image OCR Processor initialized with configuration")
    
    def _initialize_components(self):
        """Initialize processing components"""
        try:
            # Initialize EasyOCR
            if self.easyocr_enabled:
                self.easyocr_reader = easyocr.Reader(
                    self.easyocr_languages,
                    gpu=self.easyocr_gpu
                )
                logger.info(f"EasyOCR initialized with languages: {self.easyocr_languages}")
            
            # Initialize TrOCR
            if self.trocr_enabled:
                self.trocr_processor = TrOCRProcessor.from_pretrained(self.trocr_model)
                self.trocr_model_instance = VisionEncoderDecoderModel.from_pretrained(self.trocr_model)
                logger.info(f"TrOCR model '{self.trocr_model}' loaded")
            
            # Initialize Tesseract
            if self.tesseract_enabled:
                # Test Tesseract installation
                pytesseract.get_tesseract_version()
                logger.info("Tesseract initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def process_image(self, image_path: str) -> ProcessedImage:
        """Process image and extract text using OCR"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting OCR processing for: {image_path}")
            
            # Extract image metadata
            metadata = self._extract_image_metadata(image_path)
            
            # Load image
            image = self._load_image(image_path)
            
            # Preprocess image if enabled
            preprocessed_image = None
            processing_steps = []
            if self.preprocessing_enabled:
                preprocessed_image, steps = self._preprocess_image(image)
                processing_steps = steps
                image = preprocessed_image
            
            # Detect language if enabled
            language = self._detect_language(image) if self.language_detection_enabled else 'en'
            
            # Extract text using multiple OCR engines
            ocr_result = self._extract_text(image, language)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(image, ocr_result)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create processed image object
            processed_image = ProcessedImage(
                metadata=metadata,
                ocr_result=ocr_result,
                preprocessed_image=preprocessed_image,
                processing_steps=processing_steps,
                quality_metrics=quality_metrics
            )
            
            logger.info(f"OCR processing completed in {processing_time:.2f} seconds")
            return processed_image
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise
    
    def _extract_image_metadata(self, image_path: str) -> ImageMetadata:
        """Extract image metadata"""
        try:
            # Get file information
            file_size = os.path.getsize(image_path)
            file_hash = self._calculate_file_hash(image_path)
            
            # Get file format
            file_format = Path(image_path).suffix.lower()
            
            # Get file dates
            stat = os.stat(image_path)
            creation_date = datetime.fromtimestamp(stat.st_ctime)
            modification_date = datetime.fromtimestamp(stat.st_mtime)
            
            # Load image to get metadata
            with Image.open(image_path) as img:
                dimensions = img.size
                color_mode = img.mode
                dpi = img.info.get('dpi', (72, 72))
                has_transparency = img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            
            return ImageMetadata(
                filename=Path(image_path).name,
                file_size=file_size,
                file_hash=file_hash,
                format=file_format,
                dimensions=dimensions,
                color_mode=color_mode,
                dpi=dpi,
                has_transparency=has_transparency,
                creation_date=creation_date,
                modification_date=modification_date
            )
            
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
            raise
    
    def _load_image(self, image_path: str) -> np.ndarray:
        """Load image as numpy array"""
        try:
            # Load image using OpenCV
            image = cv2.imread(image_path)
            
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            return image
            
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise
    
    def _preprocess_image(self, image: np.ndarray) -> Tuple[np.ndarray, List[str]]:
        """Preprocess image for better OCR results"""
        processing_steps = []
        processed_image = image.copy()
        
        try:
            # Resize image if enabled
            if self.resize_enabled:
                height, width = processed_image.shape[:2]
                new_height = int(height * self.resize_factor)
                new_width = int(width * self.resize_factor)
                processed_image = cv2.resize(processed_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                processing_steps.append(f"Resized by factor {self.resize_factor}")
            
            # Convert to grayscale
            if len(processed_image.shape) == 3:
                processed_image = cv2.cvtColor(processed_image, cv2.COLOR_RGB2GRAY)
                processing_steps.append("Converted to grayscale")
            
            # Denoise if enabled
            if self.denoise_enabled:
                processed_image = cv2.fastNlMeansDenoising(processed_image)
                processing_steps.append("Applied denoising")
            
            # Enhance contrast if enabled
            if self.contrast_enhancement_enabled:
                processed_image = cv2.equalizeHist(processed_image)
                processing_steps.append("Enhanced contrast")
            
            # Deskew if enabled
            if self.deskew_enabled:
                processed_image = self._deskew_image(processed_image)
                processing_steps.append("Applied deskewing")
            
            # Binarize if enabled
            if self.binarization_enabled:
                processed_image = self._binarize_image(processed_image)
                processing_steps.append("Applied binarization")
            
            return processed_image, processing_steps
            
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            return image, ["Preprocessing failed"]
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image to correct rotation"""
        try:
            # Find contours
            contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return image
            
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Get minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            # Correct angle
            if angle < -45:
                angle += 90
            
            # Rotate image
            if abs(angle) > 0.5:  # Only rotate if angle is significant
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            return image
            
        except Exception as e:
            logger.error(f"Error deskewing image: {e}")
            return image
    
    def _binarize_image(self, image: np.ndarray) -> np.ndarray:
        """Binarize image using adaptive thresholding"""
        try:
            # Apply adaptive thresholding
            binary_image = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            return binary_image
            
        except Exception as e:
            logger.error(f"Error binarizing image: {e}")
            return image
    
    def _detect_language(self, image: np.ndarray) -> str:
        """Detect language of text in image"""
        try:
            if not self.tesseract_enabled:
                return 'en'
            
            # Use Tesseract to detect language
            osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
            detected_language = osd.get('script', 'Latin')
            
            # Map script to language
            language_map = {
                'Latin': 'en',
                'Cyrillic': 'ru',
                'Arabic': 'ar',
                'Chinese': 'zh',
                'Japanese': 'ja',
                'Korean': 'ko'
            }
            
            return language_map.get(detected_language, 'en')
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return 'en'
    
    def _extract_text(self, image: np.ndarray, language: str) -> OCRResult:
        """Extract text using multiple OCR engines"""
        start_time = datetime.now()
        
        # Try different OCR engines in order of preference
        ocr_results = []
        
        # Try EasyOCR first (most accurate for many languages)
        if self.easyocr_enabled:
            try:
                easyocr_result = self._extract_with_easyocr(image, language)
                if easyocr_result and easyocr_result.text.strip():
                    ocr_results.append(easyocr_result)
                    logger.info("Text extracted with EasyOCR")
            except Exception as e:
                logger.error(f"Error with EasyOCR: {e}")
        
        # Try Tesseract
        if self.tesseract_enabled:
            try:
                tesseract_result = self._extract_with_tesseract(image, language)
                if tesseract_result and tesseract_result.text.strip():
                    ocr_results.append(tesseract_result)
                    logger.info("Text extracted with Tesseract")
            except Exception as e:
                logger.error(f"Error with Tesseract: {e}")
        
        # Try TrOCR (for printed text)
        if self.trocr_enabled:
            try:
                trocr_result = self._extract_with_trocr(image)
                if trocr_result and trocr_result.text.strip():
                    ocr_results.append(trocr_result)
                    logger.info("Text extracted with TrOCR")
            except Exception as e:
                logger.error(f"Error with TrOCR: {e}")
        
        # Choose best result
        if ocr_results:
            best_result = max(ocr_results, key=lambda x: x.confidence)
        else:
            # Create empty result
            best_result = OCRResult(
                text="",
                confidence=0.0,
                bounding_boxes=[],
                words=[],
                lines=[],
                paragraphs=[],
                language=language,
                processing_time=0.0,
                quality_score=0.0
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        best_result.processing_time = processing_time
        
        return best_result
    
    def _extract_with_easyocr(self, image: np.ndarray, language: str) -> OCRResult:
        """Extract text using EasyOCR"""
        try:
            # Convert image to PIL Image
            pil_image = Image.fromarray(image)
            
            # Perform OCR
            results = self.easyocr_reader.readtext(image)
            
            # Process results
            text_parts = []
            bounding_boxes = []
            words = []
            lines = []
            
            for result in results:
                bbox, text, confidence = result
                
                if confidence >= self.min_confidence and len(text.strip()) >= self.min_text_length:
                    text_parts.append(text)
                    
                    # Convert bbox to standard format
                    bbox_dict = {
                        'x': int(min(point[0] for point in bbox)),
                        'y': int(min(point[1] for point in bbox)),
                        'width': int(max(point[0] for point in bbox) - min(point[0] for point in bbox)),
                        'height': int(max(point[1] for point in bbox) - min(point[1] for point in bbox))
                    }
                    bounding_boxes.append(bbox_dict)
                    
                    # Add word info
                    words.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox_dict
                    })
                    
                    # Add line info
                    lines.append({
                        'text': text,
                        'confidence': confidence,
                        'bbox': bbox_dict
                    })
            
            # Combine text
            full_text = ' '.join(text_parts)
            
            # Calculate average confidence
            avg_confidence = sum(result[2] for result in results) / len(results) if results else 0.0
            
            # Group words into paragraphs
            paragraphs = self._group_into_paragraphs(words)
            
            return OCRResult(
                text=full_text,
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                words=words,
                lines=lines,
                paragraphs=paragraphs,
                language=language,
                processing_time=0.0,
                quality_score=0.0
            )
            
        except Exception as e:
            logger.error(f"Error with EasyOCR extraction: {e}")
            raise
    
    def _extract_with_tesseract(self, image: np.ndarray, language: str) -> OCRResult:
        """Extract text using Tesseract"""
        try:
            # Convert image to PIL Image
            pil_image = Image.fromarray(image)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                pil_image,
                lang=language,
                config=self.tesseract_config
            )
            
            # Get detailed data
            data = pytesseract.image_to_data(
                pil_image,
                lang=language,
                config=self.tesseract_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Process results
            words = []
            lines = []
            bounding_boxes = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0 and len(data['text'][i].strip()) >= self.min_text_length:
                    word_info = {
                        'text': data['text'][i],
                        'confidence': float(data['conf'][i]) / 100.0,
                        'bbox': {
                            'x': int(data['left'][i]),
                            'y': int(data['top'][i]),
                            'width': int(data['width'][i]),
                            'height': int(data['height'][i])
                        }
                    }
                    words.append(word_info)
                    bounding_boxes.append(word_info['bbox'])
                    
                    # Add line info
                    lines.append(word_info)
            
            # Group words into paragraphs
            paragraphs = self._group_into_paragraphs(words)
            
            # Calculate average confidence
            avg_confidence = sum(word['confidence'] for word in words) / len(words) if words else 0.0
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                bounding_boxes=bounding_boxes,
                words=words,
                lines=lines,
                paragraphs=paragraphs,
                language=language,
                processing_time=0.0,
                quality_score=0.0
            )
            
        except Exception as e:
            logger.error(f"Error with Tesseract extraction: {e}")
            raise
    
    def _extract_with_trocr(self, image: np.ndarray) -> OCRResult:
        """Extract text using TrOCR"""
        try:
            # Convert image to PIL Image
            pil_image = Image.fromarray(image)
            
            # Process image
            pixel_values = self.trocr_processor(pil_image, return_tensors="pt").pixel_values
            
            # Generate text
            generated_ids = self.trocr_model_instance.generate(pixel_values)
            generated_text = self.trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # TrOCR doesn't provide detailed word-level information
            words = [{'text': generated_text, 'confidence': 0.8, 'bbox': {'x': 0, 'y': 0, 'width': 0, 'height': 0}}]
            lines = words.copy()
            paragraphs = self._group_into_paragraphs(words)
            
            return OCRResult(
                text=generated_text,
                confidence=0.8,  # Default confidence for TrOCR
                bounding_boxes=[],
                words=words,
                lines=lines,
                paragraphs=paragraphs,
                language='en',
                processing_time=0.0,
                quality_score=0.0
            )
            
        except Exception as e:
            logger.error(f"Error with TrOCR extraction: {e}")
            raise
    
    def _group_into_paragraphs(self, words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group words into paragraphs based on spatial proximity"""
        if not words:
            return []
        
        paragraphs = []
        current_paragraph = []
        
        for word in words:
            if not current_paragraph:
                current_paragraph.append(word)
            else:
                # Check if word is close to previous word
                prev_word = current_paragraph[-1]
                if self._are_words_close(prev_word, word):
                    current_paragraph.append(word)
                else:
                    # Start new paragraph
                    if current_paragraph:
                        paragraphs.append(self._create_paragraph(current_paragraph))
                    current_paragraph = [word]
        
        # Add last paragraph
        if current_paragraph:
            paragraphs.append(self._create_paragraph(current_paragraph))
        
        return paragraphs
    
    def _are_words_close(self, word1: Dict[str, Any], word2: Dict[str, Any]) -> bool:
        """Check if two words are close enough to be in the same paragraph"""
        bbox1 = word1['bbox']
        bbox2 = word2['bbox']
        
        # Calculate distance between words
        distance = abs(bbox2['x'] - (bbox1['x'] + bbox1['width']))
        
        # Words are close if distance is less than 50 pixels
        return distance < 50
    
    def _create_paragraph(self, words: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create paragraph from words"""
        if not words:
            return {'text': '', 'confidence': 0.0, 'bbox': {'x': 0, 'y': 0, 'width': 0, 'height': 0}}
        
        # Combine text
        text = ' '.join(word['text'] for word in words)
        
        # Calculate average confidence
        confidence = sum(word['confidence'] for word in words) / len(words)
        
        # Calculate bounding box
        x = min(word['bbox']['x'] for word in words)
        y = min(word['bbox']['y'] for word in words)
        width = max(word['bbox']['x'] + word['bbox']['width'] for word in words) - x
        height = max(word['bbox']['y'] + word['bbox']['height'] for word in words) - y
        
        return {
            'text': text,
            'confidence': confidence,
            'bbox': {'x': x, 'y': y, 'width': width, 'height': height}
        }
    
    def _calculate_quality_metrics(self, image: np.ndarray, ocr_result: OCRResult) -> Dict[str, float]:
        """Calculate quality metrics for the OCR result"""
        metrics = {}
        
        # Image quality metrics
        metrics['image_sharpness'] = self._calculate_sharpness(image)
        metrics['image_contrast'] = self._calculate_contrast(image)
        metrics['image_brightness'] = self._calculate_brightness(image)
        
        # OCR quality metrics
        metrics['text_confidence'] = ocr_result.confidence
        metrics['text_length'] = len(ocr_result.text)
        metrics['word_count'] = len(ocr_result.words)
        metrics['line_count'] = len(ocr_result.lines)
        metrics['paragraph_count'] = len(ocr_result.paragraphs)
        
        # Overall quality score
        metrics['overall_quality'] = self._calculate_overall_quality(metrics)
        
        return metrics
    
    def _calculate_sharpness(self, image: np.ndarray) -> float:
        """Calculate image sharpness using Laplacian variance"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            return min(laplacian_var / 1000.0, 1.0)  # Normalize to 0-1
        except:
            return 0.0
    
    def _calculate_contrast(self, image: np.ndarray) -> float:
        """Calculate image contrast"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            contrast = gray.std()
            return min(contrast / 100.0, 1.0)  # Normalize to 0-1
        except:
            return 0.0
    
    def _calculate_brightness(self, image: np.ndarray) -> float:
        """Calculate image brightness"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image
            brightness = gray.mean()
            return min(brightness / 255.0, 1.0)  # Normalize to 0-1
        except:
            return 0.0
    
    def _calculate_overall_quality(self, metrics: Dict[str, float]) -> float:
        """Calculate overall quality score"""
        # Weighted combination of metrics
        weights = {
            'image_sharpness': 0.3,
            'image_contrast': 0.2,
            'text_confidence': 0.3,
            'text_length': 0.2
        }
        
        score = 0.0
        total_weight = 0.0
        
        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
                total_weight += weight
        
        return score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def export_result(self, processed_image: ProcessedImage, format: str = 'json') -> str:
        """Export OCR result in specified format"""
        if format.lower() == 'json':
            return self._export_json(processed_image)
        elif format.lower() == 'txt':
            return self._export_txt(processed_image)
        elif format.lower() == 'csv':
            return self._export_csv(processed_image)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self, processed_image: ProcessedImage) -> str:
        """Export OCR result as JSON"""
        data = {
            'metadata': {
                'filename': processed_image.metadata.filename,
                'dimensions': processed_image.metadata.dimensions,
                'format': processed_image.metadata.format,
                'file_size': processed_image.metadata.file_size
            },
            'ocr_result': {
                'text': processed_image.ocr_result.text,
                'confidence': processed_image.ocr_result.confidence,
                'language': processed_image.ocr_result.language,
                'processing_time': processed_image.ocr_result.processing_time,
                'word_count': len(processed_image.ocr_result.words),
                'line_count': len(processed_image.ocr_result.lines),
                'paragraph_count': len(processed_image.ocr_result.paragraphs)
            },
            'quality_metrics': processed_image.quality_metrics,
            'processing_steps': processed_image.processing_steps
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def _export_txt(self, processed_image: ProcessedImage) -> str:
        """Export OCR result as plain text"""
        return processed_image.ocr_result.text
    
    def _export_csv(self, processed_image: ProcessedImage) -> str:
        """Export OCR result as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Word', 'Confidence', 'X', 'Y', 'Width', 'Height'])
        
        # Write word data
        for word in processed_image.ocr_result.words:
            bbox = word['bbox']
            writer.writerow([
                word['text'],
                word['confidence'],
                bbox['x'],
                bbox['y'],
                bbox['width'],
                bbox['height']
            ])
        
        return output.getvalue()
