from rest_framework import status

from neves_be.common.exceptions import NevesBackEndError


class TranslationError(NevesBackEndError):
    def __init__(self, details: str):
        super().__init__(
            code="TRANSLATION_ERROR",
            title="Translation service error",
            details=details,
            http_status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @classmethod
    def invalid_target_language_token(cls, target_lang: str):
        details = f"Invalid translation target language token: '{target_lang}'."
        return cls(details)

    @classmethod
    def unsupported_source_language_selection(cls):
        details = (
            "Configured translation tokenizer does not support source language "
            "selection."
        )
        return cls(details)

    @classmethod
    def missing_source_languages(cls):
        details = "No translation source languages configured."
        return cls(details)

    @classmethod
    def failed_attempt_for_source_lang(cls, source_lang: str):
        details = f"Failed translation attempt for source language '{source_lang}'."
        return cls(details)

    @classmethod
    def invalid_english_output(cls, invalid_outputs: list[str]):
        details = "Translation model did not produce valid English output."
        if invalid_outputs:
            details = f"{details} Attempts: {', '.join(invalid_outputs)}"
        return cls(details)
