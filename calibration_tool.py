#!/usr/bin/env python3
"""Calibration tool for defining ROI regions on example.png.

This tool allows manual selection of regions for OCR by drawing rectangles
on the example image and saving coordinates to config.

Usage:
    python calibration_tool.py
"""
import logging
from pathlib import Path

import cv2

from src.config import config

logger = logging.getLogger(__name__)


class ROISelector:
    """Interactive tool to select ROI regions on an image."""

    def __init__(self, image_path: Path):
        """
        Initialize the ROI selector.
        
        Args:
            image_path: Path to the image to annotate.
        """
        self.image_path = image_path
        self.image = cv2.imread(str(image_path))
        if self.image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        self.original = self.image.copy()
        self.current_roi = None
        self.rois = {}
        
        # ROI names for the game interface
        self.roi_names = [
            "title",      # Синий блок - название предмета
            "buy_price",  # Красный блок - цена покупки
            "sell_price", # Зелёный блок - цена продажи
            "avg_price",  # Фиолетовый блок - средняя цена
            "tier",       # Оранжевый блок - тир
        ]
        
        self.current_roi_index = 0
        self.window_name = "ROI Selector - Select regions"
        
        # Colors for each ROI (BGR format)
        self.colors = {
            "title": (255, 0, 0),      # Blue
            "buy_price": (0, 0, 255),  # Red
            "sell_price": (0, 255, 0), # Green
            "avg_price": (255, 0, 255),# Purple
            "tier": (0, 165, 255),     # Orange
        }

    def _get_current_roi_name(self) -> str:
        """Get the name of the current ROI being selected."""
        if self.current_roi_index < len(self.roi_names):
            return self.roi_names[self.current_roi_index]
        return ""

    def _mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for ROI selection."""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.current_roi = (x, y)
            
        elif event == cv2.EVENT_LBUTTONUP:
            if self.current_roi:
                x1, y1 = self.current_roi
                x2, y2 = x, y
                
                roi_name = self._get_current_roi_name()
                self.rois[roi_name] = {
                    "x1": min(x1, x2),
                    "y1": min(y1, y2),
                    "x2": max(x1, x2),
                    "y2": max(y1, y2),
                }
                
                # Draw the ROI on the image
                self._draw_all_rois()
                
                logger.info(f"Saved ROI '{roi_name}': {self.rois[roi_name]}")
                
                # Move to next ROI
                self.current_roi_index += 1
                
                if self.current_roi_index >= len(self.roi_names):
                    logger.info("All ROIs selected!")
                    self._save_config()
                    cv2.putText(
                        self.image,
                        "DONE - Press 'q' to quit",
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )
                
                self.current_roi = None

    def _draw_all_rois(self):
        """Draw all selected ROIs on the image."""
        self.image = self.original.copy()
        
        for name, roi in self.rois.items():
            color = self.colors.get(name, (255, 255, 255))
            cv2.rectangle(
                self.image,
                (roi["x1"], roi["y1"]),
                (roi["x2"], roi["y2"]),
                color,
                2
            )
            cv2.putText(
                self.image,
                name,
                (roi["x1"], roi["y1"] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1
            )

    def _save_config(self):
        """Save ROI coordinates to a config file."""
        import json
        
        output_file = config.BASE_DIR / "roi_config.json"
        
        roi_data = {
            "description": "ROI coordinates for OCR regions. Adjust these based on your screen resolution.",
            "note": "Coordinates are in pixels from top-left corner",
            "rois": self.rois
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(roi_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"ROI configuration saved to: {output_file}")

    def run(self):
        """Start the interactive ROI selection."""
        logger.info(f"Opening image: {self.image_path}")
        logger.info(f"Select ROIs in this order: {', '.join(self.roi_names)}")
        logger.info("Click and drag to select each region, then release mouse button.")
        
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
        
        while True:
            # Display instructions
            display_image = self.image.copy()
            current_name = self._get_current_roi_name()
            
            if current_name:
                cv2.putText(
                    display_image,
                    f"Select: {current_name}",
                    (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )
                cv2.putText(
                    display_image,
                    f"Progress: {self.current_roi_index}/{len(self.roi_names)}",
                    (50, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
            
            cv2.imshow(self.window_name, display_image)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                logger.info("Exiting...")
                break
            elif key == ord('r'):
                # Reset all selections
                self.rois = {}
                self.current_roi_index = 0
                self.current_roi = None
                self.image = self.original.copy()
                logger.info("Reset - start selecting from the beginning")
            elif key == ord('u'):
                # Undo last selection
                if self.rois and self.current_roi_index > 0:
                    self.current_roi_index -= 1
                    roi_name = self.roi_names[self.current_roi_index]
                    if roi_name in self.rois:
                        del self.rois[roi_name]
                    self.image = self.original.copy()
                    self._draw_all_rois()
                    logger.info(f"Undone: {roi_name}")
        
        cv2.destroyAllWindows()


def main():
    """Main entry point for calibration tool."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    example_path = config.EXAMPLE_FILE
    
    if not example_path.exists():
        logger.error(f"Example file not found: {example_path}")
        logger.info("Please ensure example.png exists in the project root.")
        return
    
    selector = ROISelector(example_path)
    selector.run()


if __name__ == "__main__":
    main()
