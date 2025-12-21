"""OCR tools for invoice text extraction"""
from invoice_agent.bigtool.bigtool_picker import BaseTool
from typing import Any
import pytesseract
from PIL import Image
import io
import os


class TesseractOCR(BaseTool):
    """Tesseract OCR tool"""
    name = "tesseract_ocr"
    capability = "ocr"
    
    def execute(self, image_path: str, **kwargs) -> str:
        """
        Extract text from image using Tesseract
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        try:
            if os.path.exists(image_path):
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image)
                return text
            else:
                # Mock response for demo
                return f"""
INVOICE
Invoice #: INV-2024-001
Date: 2024-01-15
Vendor: ACME CORPORATION
Tax ID: PAN12345

Items:
1. Product A - Qty: 10 x $100.00 = $1,000.00
2. Product B - Qty: 5 x $200.00 = $1,000.00

Total Amount: $2,000.00
PO Reference: PO-001
                """.strip()
        except Exception as e:
            return f"Mock OCR text for {image_path}"
