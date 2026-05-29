"""Domain errors raised by the ingestion pipeline."""


class IngestionError(Exception):
    """Base class for all ingestion failures."""


class UnsupportedFileType(IngestionError):
    """File extension / content type is not one we can parse."""


class FileTooLarge(IngestionError):
    """File exceeds the configured upload size limit."""


class CorruptFile(IngestionError):
    """File signature doesn't match its extension (possible spoof/corruption)."""
