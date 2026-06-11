"""Service for analyzing screenshots and extracting data."""
import logging
import re
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
import pytesseract

from src.config import config
from src.models import AnalysisResult, ExtractedText, MarketItem

logger = logging.getLogger(__name__)

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH


class ImageAnalysisService:
    """Service responsible for analyzing images and extracting market data."""

    def __init__(self):
        """Initialize the image analysis service."""
        self._tesseract_config = r'--oem 3 --psm 6'  # Assume uniform block of text

    def analyze(self, screenshot_path: Path) -> AnalysisResult:
        """
        Analyze a screenshot and extract market item data.
        
        Args:
            screenshot_path: Path to the screenshot file.
            
        Returns:
            AnalysisResult with extracted item data or error.
        """
        try:
            # Load image
            image = cv2.imread(str(screenshot_path))
            if image is None:
                return AnalysisResult(
                    screenshot_path=str(screenshot_path),
                    error="Failed to load image"
                )
            
            logger.info(f"Analyzing image: {screenshot_path}")
            
            # Extract text from regions
            extracted_text = self._extract_text_from_regions(image)
            
            # Parse and create market item
            item = self._parse_market_item(extracted_text, screenshot_path)
            
            return AnalysisResult(
                screenshot_path=str(screenshot_path),
                item=item,
                extracted_text=extracted_text
            )
            
        except Exception as e:
            logger.exception(f"Error during image analysis: {e}")
            return AnalysisResult(
                screenshot_path=str(screenshot_path),
                error=str(e)
            )

    def _extract_text_from_regions(self, image: np.ndarray) -> ExtractedText:
        """
        Extract text from different regions of the image.
        
        Note: This is a simplified implementation. In production, you would
        calibrate ROI coordinates based on example.png with colored blocks.
        
        Args:
            image: OpenCV image (BGR format).
            
        Returns:
            ExtractedText with text from each region.
        """
        height, width = image.shape[:2]
        
        # Define ROIs based on typical game interface layout
        # These should be adjusted based on actual screenshot layout
        roi_left = int(width * config.ROI_LEFT_MARGIN)
        roi_right = int(width * config.ROI_RIGHT_MARGIN)
        
        # Title region (left side, upper portion)
        title_roi = image[0:int(height * 0.3), roi_right:int(width)]
        
        # Price regions (right side)
        price_area = image[int(height * 0.2):int(height * 0.6), roi_right:int(width)]
        
        # Extract text using OCR
        extracted = ExtractedText()
        
        # Title text
        extracted.title_text = self._ocr_text(title_roi)
        logger.debug(f"Title OCR: {extracted.title_text}")
        
        # Price text (all prices together)
        price_text = self._ocr_text(price_area)
        logger.debug(f"Price OCR: {price_text}")
        
        # Parse individual prices from combined text
        prices = self._parse_prices(price_text)
        extracted.buy_price_text = str(prices.get("buy", ""))
        extracted.sell_price_text = str(prices.get("sell", ""))
        extracted.avg_price_text = str(prices.get("avg", ""))
        
        # Tier extraction (try to find Roman numerals)
        extracted.tier_text = self._extract_tier(extracted.title_text)
        
        return extracted

    def _ocr_text(self, image_roi: np.ndarray) -> str:
        """
        Perform OCR on image region.
        
        Args:
            image_roi: Region of interest.
            
        Returns:
            Extracted text string.
        """
        # Preprocess for better OCR accuracy
        gray = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Perform OCR
        text = pytesseract.image_to_string(
            binary,
            lang=config.OCR_LANG,
            config=self._tesseract_config
        ).strip()
        
        return text

    def _parse_prices(self, text: str) -> dict:
        """
        Parse prices from OCR text.
        
        This is a simplified parser. In production, you would use the
        color-coded regions from example.png to identify which price is which.
        
        Args:
            text: OCR text containing prices.
            
        Returns:
            Dictionary with parsed prices.
        """
        prices = {"buy": 0, "sell": 0, "avg": 0}
        
        # Extract all numbers from text
        numbers = re.findall(r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?', text)
        
        # Clean and convert numbers
        clean_numbers = []
        for num in numbers:
            # Replace commas and dots for proper parsing
            cleaned = num.replace(',', '.').replace('.', '')
            try:
                clean_numbers.append(int(cleaned))
            except ValueError:
                continue
        
        # Assign to price fields (order depends on UI layout)
        # This assumes: sell, buy, avg order - adjust based on actual layout
        if len(clean_numbers) >= 3:
            prices["sell"] = clean_numbers[0]
            prices["buy"] = clean_numbers[1]
            prices["avg"] = clean_numbers[2]
        elif len(clean_numbers) == 2:
            prices["sell"] = clean_numbers[0]
            prices["buy"] = clean_numbers[1]
            prices["avg"] = int((clean_numbers[0] + clean_numbers[1]) / 2)
        elif len(clean_numbers) == 1:
            prices["sell"] = clean_numbers[0]
            prices["buy"] = clean_numbers[0]
            prices["avg"] = clean_numbers[0]
        
        return prices

    def _extract_tier(self, text: str) -> str:
        """
        Extract tier (Roman numerals) from text.
        
        Args:
            text: Text to search for tier.
            
        Returns:
            Tier string (e.g., "I", "II", "III", etc.) or empty string.
        """
        # Look for Roman numerals
        roman_pattern = r'\b(?:I{1,3}|IV|V|VI{0,3}|IX|X)\b'
        match = re.search(roman_pattern, text)
        return match.group(0) if match else ""

    def _parse_market_item(
        self, 
        extracted: ExtractedText, 
        screenshot_path: Path
    ) -> MarketItem | None:
        """
        Create a MarketItem from extracted text.
        
        Args:
            extracted: Extracted text data.
            screenshot_path: Path to original screenshot.
            
        Returns:
            MarketItem if data is valid, None otherwise.
        """
        # Clean item name
        item_name = extracted.title_text.strip()
        if not item_name:
            logger.warning("No item name extracted")
            return None
        
        # Create timestamp from filename
        filename = screenshot_path.stem  # e.g., "2025-01-15-14-30-45"
        try:
            dt = datetime.strptime(filename, "%Y-%m-%d-%H-%M-%S")
            screenshot_date = dt.strftime(config.DATE_FORMAT)
        except ValueError:
            screenshot_date = datetime.now().strftime(config.DATE_FORMAT)
        
        return MarketItem(
            item_name=item_name,
            sell_price=extracted.sell_price_text or 0,
            buy_price=extracted.buy_price_text or 0,
            average_price=extracted.avg_price_text or 0,
            tier=extracted.tier_text,
            screenshot_date=screenshot_date
        )
