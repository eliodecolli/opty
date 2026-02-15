from enum import StrEnum


class DraftSource(StrEnum):
    DRAFT_FILE = "draft"
    INTERACTIVE = "interactive"
    UNKNOWN = "unknown"
