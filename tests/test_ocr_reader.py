"""Tests for OCR text extraction."""

import pytest

from app.vision.ocr_reader import OCRReader, OCRReaderError


def test_read_text_returns_confident_regions(monkeypatch):
    """OCR should return text with valid bounds and confidence."""
    from PIL import Image

    fake_data = {
        "text": ["", "WhatsApp", "noise", "invalid"],
        "conf": ["-1", "95", "15", "bad"],
        "left": ["0", "10", "20", "0"],
        "top": ["0", "20", "30", "0"],
        "width": ["0", "100", "30", "0"],
        "height": ["0", "25", "10", "0"],
    }

    monkeypatch.setattr(
        "app.vision.ocr_reader.pytesseract.image_to_data",
        lambda *args, **kwargs: fake_data,
    )

    regions = OCRReader(min_confidence=40).read_text(
        Image.new("RGB", (200, 100))
    )

    assert len(regions) == 1
    assert regions[0].text == "WhatsApp"
    assert regions[0].confidence == 95
    assert regions[0].center == (60, 32)


def test_read_text_wraps_tesseract_errors(monkeypatch):
    """OCR engine errors should become a controlled exception."""
    from PIL import Image

    def fail_ocr(*args, **kwargs):
        raise RuntimeError("Tesseract unavailable")

    monkeypatch.setattr(
        "app.vision.ocr_reader.pytesseract.image_to_data",
        fail_ocr,
    )

    with pytest.raises(OCRReaderError, match="OCR failed"):
        OCRReader().read_text(Image.new("RGB", (100, 100)))


def test_reader_rejects_invalid_confidence_threshold():
    """Confidence thresholds must be between zero and one hundred."""
    with pytest.raises(ValueError, match="between 0 and 100"):
        OCRReader(min_confidence=101)