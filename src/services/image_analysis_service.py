"""Service for analyzing screenshots and extracting data."""
import json
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
            
            # Log extracted text for debugging
            self._log_extracted_text(extracted_text)
            
            # Parse and create market item
            item = self._parse_market_item(extracted_text, screenshot_path)
            
            # Save debug image if enabled
            if config.DEBUG_MODE:
                self._save_debug_image(image, screenshot_path, extracted_text)
            
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

    def _log_extracted_text(self, extracted: ExtractedText) -> None:
        """Log extracted text for debugging."""
        logger.debug(f"Extracted text - Title: '{extracted.title_text}'")
        logger.debug(f"Extracted text - Buy price: '{extracted.buy_price_text}'")
        logger.debug(f"Extracted text - Sell price: '{extracted.sell_price_text}'")
        logger.debug(f"Extracted text - Avg price: '{extracted.avg_price_text}'")

    def _extract_text_from_regions(self, image: np.ndarray) -> ExtractedText:
        """
        Extract text from different regions of the image using ROI config.
        
        Args:
            image: OpenCV image (BGR format).
            
        Returns:
            ExtractedText with text from each region.
        """
        height, width = image.shape[:2]
        
        # Get ROI coordinates from config
        rois = config.roi_coordinates
        
        # Check if we have valid ROI coordinates (not all zeros)
        has_valid_rois = any(
            roi.get("x1", 0) > 0 or roi.get("y1", 0) > 0 
            for roi in rois.values()
        )

        extracted = ExtractedText()
        
        if has_valid_rois:
            # Use configured ROI coordinates
            logger.info("Using configured ROI coordinates")
            
            # Title region
            if "title" in rois and self._is_valid_roi(rois["title"]):
                title_roi = self._get_roi(image, rois["title"])
                extracted.title_text = self._ocr_text(title_roi)
            
            # Buy price region
            if "buy_price" in rois and self._is_valid_roi(rois["buy_price"]):
                buy_roi = self._get_roi(image, rois["buy_price"])
                extracted.buy_price_text = self._ocr_text(buy_roi)
            
            # Sell price region
            if "sell_price" in rois and self._is_valid_roi(rois["sell_price"]):
                sell_roi = self._get_roi(image, rois["sell_price"])
                extracted.sell_price_text = self._ocr_text(sell_roi)
            
            # Avg price region
            if "avg_price" in rois and self._is_valid_roi(rois["avg_price"]):
                avg_roi = self._get_roi(image, rois["avg_price"])
                extracted.avg_price_text = self._ocr_text(avg_roi)
            
        else:
            # Fallback: Use relative coordinates (deprecated, but for backwards compatibility)
            logger.warning("No valid ROI coordinates found, using fallback method")
            roi_right = int(width * config.ROI_RIGHT_MARGIN)
            
            # Title region (right side of screen)
            title_roi = image[0:int(height * 0.3), roi_right:int(width)]
            
            # Price regions (right side)
            price_area = image[int(height * 0.2):int(height * 0.6), roi_right:int(width)]
            
            # Extract text using OCR
            extracted.title_text = self._ocr_text(title_roi)
            logger.debug(f"Title OCR (fallback): {extracted.title_text}")
            
            # Price text (all prices together)
            price_text = self._ocr_text(price_area)
            logger.debug(f"Price OCR (fallback): {price_text}")
            
            # Parse individual prices from combined text
            prices = self._parse_prices(price_text)
            extracted.buy_price_text = str(prices.get("buy", ""))
            extracted.sell_price_text = str(prices.get("sell", ""))
            extracted.avg_price_text = str(prices.get("avg", ""))
            
        return extracted

    def _is_valid_roi(self, roi: dict) -> bool:
        """Check if ROI has valid coordinates."""
        return (
            roi.get("x1", 0) > 0 or 
            roi.get("y1", 0) > 0
        )

    def _get_roi(self, image: np.ndarray, roi: dict) -> np.ndarray:
        """Extract ROI from image."""
        x1, y1 = roi["x1"], roi["y1"]
        x2, y2 = roi["x2"], roi["y2"]
        return image[y1:y2, x1:x2]

    def _save_debug_image(
        self, 
        image: np.ndarray, 
        screenshot_path: Path,
        extracted: ExtractedText
    ) -> None:
        """Save debug image with ROI overlays and extracted text."""
        debug_image = image.copy()
        rois = config.roi_coordinates
        
        # Draw ROI rectangles and labels
        for name, roi in rois.items():
            if self._is_valid_roi(roi):
                color = config.COLOR_RANGES.get(name, {}).get("lower", (0, 255, 0))
                if isinstance(color, tuple) and len(color) == 3:
                    # Convert from dict format to tuple
                    color = (color[0], color[1], color[2])
                else:
                    color = (0, 255, 0)
                
                cv2.rectangle(
                    debug_image,
                    (roi["x1"], roi["y1"]),
                    (roi["x2"], roi["y2"]),
                    color,
                    2
                )
                cv2.putText(
                    debug_image,
                    name,
                    (roi["x1"], roi["y1"] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )
        
        # Add extracted text overlay
        text_y = 30
        text_lines = [
            f"Title: {extracted.title_text[:50]}",
            f"Buy: {extracted.buy_price_text} | Sell: {extracted.sell_price_text} | Avg: {extracted.avg_price_text}",
        ]
        
        for i, line in enumerate(text_lines):
            cv2.putText(
                debug_image,
                line,
                (10, text_y + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        # Save debug image
        debug_path = screenshot_path.parent / f"debug_{screenshot_path.name}"
        cv2.imwrite(str(debug_path), debug_image)
        logger.debug(f"Debug image saved: {debug_path}")

    def _ocr_text(self, image_roi: np.ndarray) -> str:
        """
        Perform OCR on image region with preprocessing.
        
        Args:
            image_roi: Region of interest.
            
        Returns:
            Extracted text string.
        """
        if image_roi.size == 0:
            return ""
        
        # Preprocess for better OCR accuracy
        gray = cv2.cvtColor(image_roi, cv2.COLOR_BGR2GRAY)
        
        # Resize to increase text size (helps with small text)
        scale_factor = 2
        resized = cv2.resize(
            gray, 
            (0, 0), 
            fx=scale_factor, 
            fy=scale_factor,
            interpolation=cv2.INTER_CUBIC
        )

        # Adaptive thresholding (better than OTSU for varied lighting)
        binary = cv2.adaptiveThreshold(
            resized,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,  # Block size (must be odd)
            2    # C
        )
        
        # Morphological operations to connect broken characters
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Perform OCR
        text = pytesseract.image_to_string(
            cleaned,
            lang=config.OCR_LANG,
            config=self._tesseract_config
        ).strip()
        
        return text

    def _parse_prices(self, text: str) -> dict:
        """
        Parse prices from OCR text with context awareness.
        
        This looks for numbers with context clues in the text.
        
        Args:
            text: OCR text containing prices.
            
        Returns:
            Dictionary with parsed prices.
        """
        prices = {"buy": 0, "sell": 0, "avg": 0}
        
        # Pattern to find numbers (handles both comma and dot as thousand separators)
        number_pattern = r'\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?'
        
        # Find all numbers with their surrounding context
        matches = re.finditer(number_pattern, text)
        
        numbers = []
        for match in matches:
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].lower()
            num_str = match.group().replace(',', '').replace('.', '')
            
            try:
                num = int(num_str)
                numbers.append({
                    "value": num,
                    "context": context,
                    "original": match.group()
                })
            except ValueError:
                continue
        
        # Try to identify each price by context
        for item in numbers:
            ctx = item["context"]
            
            # Check for buy price indicators
            if any(word in ctx for word in ["куп", "buy", "покуп"]):
                if prices["buy"] == 0:
                    prices["buy"] = item["value"]
            # Check for sell price indicators
            elif any(word in ctx for word in ["прод", "sell", "прода"]):
                if prices["sell"] == 0:
                    prices["sell"] = item["value"]
            # Check for average price indicators
            elif any(word in ctx for word in ["сред", "avg", "average", "ср"]):
                if prices["avg"] == 0:
                    prices["avg"] = item["value"]
        
        # If we have 3+ numbers and no context matched, assume order: sell, buy, avg
        if prices["sell"] == 0 and prices["buy"] == 0 and prices["avg"] == 0:
            if len(numbers) >= 3:
                prices["sell"] = numbers[0]["value"]
                prices["buy"] = numbers[1]["value"]
                prices["avg"] = numbers[2]["value"]
            elif len(numbers) == 2:
                prices["sell"] = numbers[0]["value"]
                prices["buy"] = numbers[1]["value"]
                prices["avg"] = int((numbers[0]["value"] + numbers[1]["value"]) / 2)
            elif len(numbers) == 1:
                prices["sell"] = numbers[0]["value"]
                prices["buy"] = numbers[0]["value"]
                prices["avg"] = numbers[0]["value"]
        
        return prices

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
        # Clean item name - remove common OCR artifacts
        item_name = extracted.title_text.strip()
        
        # Filter out common OCR errors
        if item_name in ["oy", "оу", "ou", "00", "OO", "qq", ""]:
            logger.warning(f"Invalid item name detected (OCR error): '{item_name}'")
            return None
        
        if len(item_name) < 2:
            logger.warning(f"Item name too short: '{item_name}'")
            return None
        
        # Create timestamp from filename
        filename = screenshot_path.stem  # e.g., "2025-01-15-14-30-45"
        try:
            dt = datetime.strptime(filename, "%Y-%m-%d-%H-%M-%S")
            screenshot_date = dt.strftime(config.DATE_FORMAT)
        except ValueError:
            screenshot_date = datetime.now().strftime(config.DATE_FORMAT)
        
        # Parse prices (in case they weren't extracted as numbers)
        buy_price = self._safe_parse_int(extracted.buy_price_text)
        sell_price = self._safe_parse_int(extracted.sell_price_text)
        avg_price = self._safe_parse_int(extracted.avg_price_text)
        
        return MarketItem(
            item_name=item_name,
            sell_price=sell_price,
            buy_price=buy_price,
            average_price=avg_price,
            screenshot_date=screenshot_date
        )

    def _safe_parse_int(self, value: str | int) -> int:
        """Safely parse integer from string."""
        if isinstance(value, int):
            return value
        if not value:
            return 0
        try:
            # Remove common separators
            cleaned = str(value).replace(',', '').replace('.', '')
            return int(cleaned)
        except (ValueError, TypeError):
            return 0
