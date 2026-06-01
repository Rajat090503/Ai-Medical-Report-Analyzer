"""
ocr.py  —  PDF text extraction with scanned PDF fallback
Tries pdfplumber first (fast, accurate for digital PDFs).
Falls back to EasyOCR for scanned / image-based PDFs.
"""

import os
import pdfplumber
import easyocr
import fitz      # PyMuPDF — for rendering scanned PDF pages to images
import io
from PIL import Image

# Initialise EasyOCR once (takes a few seconds to load model)
print("Loading EasyOCR model...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)
print("EasyOCR ready.")


def _pdf_has_text(filepath: str) -> bool:
    """Return True if pdfplumber finds meaningful text in the PDF."""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t and len(t.strip()) > 50:
                    return True
    except Exception:
        pass
    return False


def _extract_text_pdfplumber(filepath: str) -> str:
    """Extract text from a digital (text-based) PDF."""
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _extract_text_ocr_pdf(filepath: str) -> str:
    """Render each page of a scanned PDF to an image, then run EasyOCR."""
    text = ""
    doc  = fitz.open(filepath)

    for page_num, page in enumerate(doc):
        print(f"   OCR: processing page {page_num + 1}/{len(doc)}...")

        # Render at 200 DPI (higher = better OCR accuracy)
        mat = fitz.Matrix(200 / 72, 200 / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        result = reader.readtext(img, detail=0, paragraph=True)
        text  += "\n".join(result) + "\n"

    doc.close()
    return text.strip()


def _extract_text_ocr_image(filepath: str) -> str:
    """Run EasyOCR directly on an image file (jpg, png, etc.)."""
    result = reader.readtext(filepath, detail=0, paragraph=True)
    return "\n".join(result)


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC FUNCTION
# ─────────────────────────────────────────────────────────────────────────────
def extract_text(file_path: str) -> str:
    """
    Smart extraction:
      - Digital PDF  → pdfplumber  (fast, accurate)
      - Scanned PDF  → PyMuPDF render + EasyOCR
      - Image file   → EasyOCR directly
    """
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == ".pdf":
            if _pdf_has_text(file_path):
                print("   Digital PDF detected — using pdfplumber")
                text = _extract_text_pdfplumber(file_path)
            else:
                print("   Scanned PDF detected — using OCR (this may take 10-30s)")
                text = _extract_text_ocr_pdf(file_path)
        else:
            # jpg, png, bmp, tiff etc.
            print("   Image file detected — using OCR")
            text = _extract_text_ocr_image(file_path)

        if not text.strip():
            return "ERROR: Could not extract any text. The file may be corrupted or very low quality."

        return text

    except Exception as e:
        return f"ERROR: {str(e)}"
