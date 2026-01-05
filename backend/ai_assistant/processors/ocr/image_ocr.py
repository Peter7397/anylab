"""
Image OCR processing module.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# OCR support
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    Image = None
    logger.warning("pytesseract or Pillow not available - OCR will be disabled")


class ImageOCRProcessor:
    """Perform OCR on images with multiple PSM modes and multi-language support"""
    
    def __init__(self):
        """Initialize OCR processor with language configuration"""
        # Get OCR languages from settings (default: English only)
        self.ocr_languages = getattr(settings, 'OCR_LANGUAGES', ['eng'])
        if isinstance(self.ocr_languages, str):
            # Handle comma-separated string
            self.ocr_languages = [lang.strip() for lang in self.ocr_languages.split(',')]
        # Format for Tesseract: 'eng' or 'eng+chi_sim' for multiple languages
        self.tesseract_lang = '+'.join(self.ocr_languages) if len(self.ocr_languages) > 1 else self.ocr_languages[0]
        logger.info(f"ImageOCRProcessor initialized with languages: {self.tesseract_lang}")
    
    def ocr_image(self, pil_image, page_num: int, source: str = "image", languages: str = None, return_dict: bool = False):
        """
        Perform OCR on a PIL image with multiple PSM modes, enhancements, and multi-language support.
        
        Args:
            pil_image: PIL Image to OCR
            page_num: Page number for logging
            source: Source description for logging
            languages: Optional language override (e.g., 'eng', 'chi_sim', 'eng+chi_sim')
                      If None, uses OCR_LANGUAGES from settings
            return_dict: If True, returns dict with quality metrics. If False, returns text string (backward compatibility)
            
        Returns:
            If return_dict=True: Dictionary with:
            - text: Extracted text string
            - quality_score: OCR quality score (0.0 to 1.0)
            - confidence: Average confidence from Tesseract (if available)
            - method: Method used ('psm', 'enhanced', 'combined', 'fallback')
            If return_dict=False: Extracted text string (backward compatible)
        """
        if not OCR_AVAILABLE:
            return {'text': '', 'quality_score': 0.0, 'confidence': 0.0, 'method': 'unavailable'} if return_dict else ''
        
        # Use provided languages or default from settings
        lang_param = languages or self.tesseract_lang
        
        ocr_text = ""
        quality_score = 0.0
        confidence = 0.0
        method = 'none'
        
        # Enhanced PSM modes for different layouts
        if pil_image.size[0] < 500 or pil_image.size[1] < 100:
            # Small images: Prefer single line/word modes
            psm_modes = [7, 8, 6, 3]
        else:
            # Full pages: Try best layout modes first
            psm_modes = [1, 4, 5, 3, 6]
        
        # Try all PSM modes and select the best result
        best_text = ""
        best_psm = None
        best_text_length = 0
        best_confidence = 0.0
        
        for psm in psm_modes:
            try:
                test_text = pytesseract.image_to_string(
                    pil_image,
                    lang=lang_param,
                    config=f'--psm {psm}'
                )
                if test_text and test_text.strip():
                    text_length = len(test_text.strip())
                    # Try to get confidence score if available
                    try:
                        ocr_data = pytesseract.image_to_data(pil_image, lang=lang_param, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
                        confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                    except Exception:
                        avg_confidence = 0.0
                    
                    # Score based on text length and confidence
                    score = (text_length / 1000.0) * 0.5 + (avg_confidence / 100.0) * 0.5  # Normalized score
                    
                    if score > (best_text_length / 1000.0 * 0.5 + best_confidence / 100.0 * 0.5):
                        best_text = test_text
                        best_psm = psm
                        best_text_length = text_length
                        best_confidence = avg_confidence
                        logger.debug(f"PSM {psm} extracted {text_length} chars (confidence: {avg_confidence:.1f}%) from {source} (page {page_num})")
            except Exception as e:
                logger.debug(f"PSM {psm} failed for {source} (page {page_num}): {e}")
                continue
        
        # Use the best result
        if best_text:
            ocr_text = best_text
            confidence = best_confidence
            method = f'psm_{best_psm}'
            # Calculate quality score: based on text length, confidence, and non-empty result
            quality_score = min(1.0, (best_text_length / 1000.0) * 0.4 + (best_confidence / 100.0) * 0.6)
            logger.debug(f"OCR successful with PSM {best_psm} (extracted {best_text_length} chars, confidence: {best_confidence:.1f}%, quality: {quality_score:.2f}) on {source} (page {page_num})")
        else:
            logger.warning(f"No text extracted from any PSM mode for {source} (page {page_num})")
        
        # If still no text, try with image enhancement
        if not ocr_text.strip():
            try:
                enhancement_strategies = [
                    ('contrast', lambda img: ImageEnhance.Contrast(img).enhance(2.0)),
                    ('sharpness', lambda img: ImageEnhance.Sharpness(img).enhance(2.0)),
                    ('brightness', lambda img: ImageEnhance.Brightness(img).enhance(1.2)),
                ]
                
                # Try each enhancement strategy
                for strategy_name, enhance_func in enhancement_strategies:
                    try:
                        enhanced = enhance_func(pil_image)
                        # Try multiple PSM modes with enhanced image
                        for psm in [1, 4, 5, 3, 6]:
                            try:
                                test_text = pytesseract.image_to_string(
                                    enhanced, 
                                    lang=lang_param, 
                                    config=f'--psm {psm}'
                                )
                                if test_text and test_text.strip():
                                    text_length = len(test_text.strip())
                                    # Get confidence for enhanced image
                                    try:
                                        ocr_data = pytesseract.image_to_data(enhanced, lang=lang_param, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
                                        confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                                    except Exception:
                                        avg_confidence = 0.0
                                    
                                    # Score based on text length and confidence
                                    score = (text_length / 1000.0) * 0.4 + (avg_confidence / 100.0) * 0.6
                                    current_score = (len(ocr_text.strip()) / 1000.0) * 0.4 + (confidence / 100.0) * 0.6
                                    
                                    # Use the best result (highest score)
                                    if score > current_score:
                                        ocr_text = test_text
                                        confidence = avg_confidence
                                        method = f'enhanced_{strategy_name}_psm_{psm}'
                                        quality_score = min(1.0, score)
                                        logger.debug(
                                            f"OCR successful with {strategy_name} enhancement and PSM {psm} "
                                            f"(extracted {text_length} chars, confidence: {avg_confidence:.1f}%, quality: {quality_score:.2f}) on {source} (page {page_num})"
                                        )
                            except Exception:
                                continue
                        if ocr_text.strip():
                            break
                    except Exception as e:
                        logger.debug(f"{strategy_name} enhancement failed for {source} (page {page_num}): {e}")
                        continue
                
                # Try combined enhancements (contrast + sharpness)
                if not ocr_text.strip():
                    try:
                        enhanced = ImageEnhance.Contrast(pil_image).enhance(2.0)
                        enhanced = ImageEnhance.Sharpness(enhanced).enhance(2.0)
                        enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))  # Noise reduction
                        for psm in [1, 4, 5, 3]:
                            try:
                                test_text = pytesseract.image_to_string(
                                    enhanced,
                                    lang=lang_param,
                                    config=f'--psm {psm}'
                                )
                                if test_text and test_text.strip():
                                    text_length = len(test_text.strip())
                                    try:
                                        ocr_data = pytesseract.image_to_data(enhanced, lang=lang_param, config=f'--psm {psm}', output_type=pytesseract.Output.DICT)
                                        confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                                    except Exception:
                                        avg_confidence = 0.0
                                    
                                    score = (text_length / 1000.0) * 0.4 + (avg_confidence / 100.0) * 0.6
                                    current_score = (len(ocr_text.strip()) / 1000.0) * 0.4 + (confidence / 100.0) * 0.6
                                    
                                    if score > current_score:
                                        ocr_text = test_text
                                        confidence = avg_confidence
                                        method = f'combined_psm_{psm}'
                                        quality_score = min(1.0, score)
                                        logger.debug(f"OCR successful with combined enhancements and PSM {psm} (quality: {quality_score:.2f}) on {source} (page {page_num})")
                                    break
                            except Exception:
                                continue
                    except Exception as e:
                        logger.debug(f"Combined enhancement failed for {source} (page {page_num}): {e}")
            except Exception as e:
                logger.debug(f"Image enhancement failed for {source} (page {page_num}): {e}")
        
        # Final fallback: try with default settings
        if not ocr_text.strip():
            try:
                ocr_text = pytesseract.image_to_string(pil_image, lang=lang_param, config='--psm 3')
                if ocr_text.strip():
                    method = 'fallback_psm_3'
                    try:
                        ocr_data = pytesseract.image_to_data(pil_image, lang=lang_param, config='--psm 3', output_type=pytesseract.Output.DICT)
                        confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                        confidence = sum(confidences) / len(confidences) if confidences else 0.0
                        quality_score = min(1.0, (len(ocr_text.strip()) / 1000.0) * 0.4 + (confidence / 100.0) * 0.6)
                    except Exception:
                        confidence = 0.0
                        quality_score = min(1.0, len(ocr_text.strip()) / 1000.0)
                    logger.debug(f"OCR successful with default PSM 3 (lang: {lang_param}, quality: {quality_score:.2f}) on {source} (page {page_num})")
            except Exception as e:
                logger.debug(f"OCR failed completely for {source} (page {page_num}): {e}")
        
        # Return structured result with quality metrics or just text (backward compatibility)
        if return_dict:
            return {
                'text': ocr_text,
                'quality_score': quality_score,
                'confidence': confidence,
                'method': method,
            }
        else:
            # Backward compatibility: return text string
            return ocr_text

