"""
ocr.py — PDF text extraction with scanned PDF fallback
Optimized for Render deployment
"""

import os
import pdfplumber
import fitz
import io
from PIL import Image
import easyocr


def get_reader():
    """
    Load EasyOCR only when needed.
    Prevents Render memory crash during startup.
    """
    return easyocr.Reader(['en'], gpu=False, verbose=False)


def _pdf_has_text(filepath: str) -> bool:

    try:
        with pdfplumber.open(filepath) as pdf:

            for page in pdf.pages:

                text = page.extract_text()

                if text and len(text.strip()) > 50:
                    return True

    except Exception:
        pass

    return False


def _extract_text_pdfplumber(filepath: str) -> str:

    text = ""

    with pdfplumber.open(filepath) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text.strip()


def _extract_text_ocr_pdf(filepath: str) -> str:

    reader = get_reader()

    text = ""
    doc = fitz.open(filepath)

    for page_num, page in enumerate(doc):

        print(f"OCR Page {page_num + 1}/{len(doc)}")

        mat = fitz.Matrix(200 / 72, 200 / 72)

        pix = page.get_pixmap(
            matrix=mat,
            colorspace=fitz.csGRAY
        )

        img = Image.open(
            io.BytesIO(
                pix.tobytes("png")
            )
        )

        result = reader.readtext(
            img,
            detail=0,
            paragraph=True
        )

        text += "\n".join(result) + "\n"

    doc.close()

    return text.strip()


def _extract_text_ocr_image(filepath: str) -> str:

    reader = get_reader()

    result = reader.readtext(
        filepath,
        detail=0,
        paragraph=True
    )

    return "\n".join(result)


def extract_text(file_path: str) -> str:

    ext = os.path.splitext(file_path)[1].lower()

    try:

        if ext == ".pdf":

            if _pdf_has_text(file_path):

                print("Digital PDF detected")

                text = _extract_text_pdfplumber(file_path)

            else:

                print("Scanned PDF detected")

                text = _extract_text_ocr_pdf(file_path)

        else:

            print("Image detected")

            text = _extract_text_ocr_image(file_path)

        if not text.strip():

            return (
                "ERROR: Could not extract text "
                "from the uploaded file."
            )

        return text

    except Exception as e:

        return f"ERROR: {str(e)}"
