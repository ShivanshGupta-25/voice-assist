"""Verification helpers for screen-observation results."""

from dataclasses import dataclass

from app.vision.ocr_reader import TextRegion


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Result of checking whether expected text is visible."""

    verified: bool
    expected_text: str
    matched_text: str | None = None
    confidence: float | None = None


class ActionVerifier:
    """Verify visible text using previously collected OCR results."""

    def verify_text_visible(
        self,
        expected_text: str,
        regions: list[TextRegion],
    ) -> VerificationResult:
        """Check whether normalized expected text is present."""
        expected = " ".join(expected_text.casefold().split())

        if not expected:
            raise ValueError("Expected text must not be empty.")

        for region in regions:
            observed = " ".join(region.text.casefold().split())

            if expected in observed:
                return VerificationResult(
                    verified=True,
                    expected_text=expected_text,
                    matched_text=region.text,
                    confidence=region.confidence,
                )

        return VerificationResult(
            verified=False,
            expected_text=expected_text,
        )