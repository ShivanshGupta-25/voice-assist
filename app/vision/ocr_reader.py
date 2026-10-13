"""OCR utilities for locating visible text on the desktop."""

import logging
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytesseract
from PIL import Image
from pytesseract import Output
from pytesseract import TesseractNotFoundError


logger = logging.getLogger(__name__)


class OCRReaderError(Exception):
    """Raised when OCR cannot process an image."""


@dataclass(frozen=True, slots=True)
class TextRegion:
    """A recognized text region and its image-relative bounds."""

    text: str
    confidence: float
    left: int
    top: int
    width: int
    height: int

    @property
    def center(self) -> tuple[int, int]:
        """Return the center point of the text region."""
        return (
            self.left + self.width // 2,
            self.top + self.height // 2,
        )


class OCRReader:
    """Extract visible text and bounding boxes from an image."""

    def __init__(
        self,
        language: str = "eng",
        min_confidence: float = 40.0,
        tesseract_path: str | None = None,
    ) -> None:
        """Configure and validate the OCR engine."""
        if not 0 <= min_confidence <= 100:
            raise ValueError(
                "min_confidence must be between 0 and 100."
            )

        if not language or not language.strip():
            raise ValueError("language must not be empty.")

        self.language = language.strip()
        self.min_confidence = min_confidence

        # Resolve the executable from explicit configuration,
        # the environment variable, or the system PATH.
        configured_path = (
            tesseract_path
            or os.getenv("TESSERACT_CMD")
        )

        if configured_path:
            executable_path = Path(
                configured_path
            ).expanduser()

            if not executable_path.is_file():
                raise OCRReaderError(
                    "Tesseract executable not found: "
                    f"{executable_path}"
                )

            executable = str(executable_path.resolve())

        else:
            executable = shutil.which("tesseract")

            if executable is None:
                raise OCRReaderError(
                    "Tesseract was not found. Install Tesseract OCR "
                    "or set TESSERACT_CMD to the full path of "
                    "tesseract.exe."
                )

        # Configure pytesseract before invoking the engine.
        pytesseract.pytesseract.tesseract_cmd = executable

        # Validate the executable and requested language.
        try:
            available_languages = pytesseract.get_languages(
                config=""
            )
        except TesseractNotFoundError as exc:
            raise OCRReaderError(
                "Tesseract could not be started. Check the executable "
                "path and Windows permissions."
            ) from exc
        except Exception as exc:
            logger.exception(
                "Unable to inspect Tesseract configuration"
            )
            raise OCRReaderError(
                f"Unable to inspect Tesseract configuration: {exc}"
            ) from exc

        requested_languages = set(
            self.language.split("+")
        )
        missing_languages = (
            requested_languages - set(available_languages)
        )

        if missing_languages:
            raise OCRReaderError(
                "Missing Tesseract language data: "
                f"{', '.join(sorted(missing_languages))}. "
                "Available languages: "
                f"{', '.join(available_languages)}"
            )

        logger.info(
            "OCR initialized successfully; language=%s",
            self.language,
        )

    def read_text(
        self,
        image: Image.Image,
    ) -> list[TextRegion]:
        """Recognize text regions without saving the image."""
        if not isinstance(image, Image.Image):
            raise TypeError(
                "image must be a PIL Image.Image instance."
            )

        try:
            data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=Output.DICT,
            )
        except TesseractNotFoundError as exc:
            raise OCRReaderError(
                "Tesseract executable was not found during OCR."
            ) from exc
        except Exception as exc:
            logger.exception("Tesseract OCR execution failed")
            raise OCRReaderError(
                f"OCR execution failed: {exc}"
            ) from exc

        regions: list[TextRegion] = []

        for index, raw_text in enumerate(data["text"]):
            text = raw_text.strip()

            if not text:
                continue

            try:
                confidence = float(data["conf"][index])
                left = int(data["left"][index])
                top = int(data["top"][index])
                width = int(data["width"][index])
                height = int(data["height"][index])
            except (ValueError, TypeError, KeyError, IndexError):
                continue

            if confidence < self.min_confidence:
                continue

            if width <= 0 or height <= 0:
                continue

            regions.append(
                TextRegion(
                    text=text,
                    confidence=confidence,
                    left=left,
                    top=top,
                    width=width,
                    height=height,
                )
            )

        return regions