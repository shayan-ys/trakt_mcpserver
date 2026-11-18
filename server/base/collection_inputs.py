"""Item inputs shared by personal collection mutations (watchlist, lists)."""

from typing import Any

from pydantic import Field, field_validator

from .identifier_mixin import IdentifierValidatorMixin


class CollectionItemIdentifier(IdentifierValidatorMixin):
    """Identify one item for a collection removal."""

    def build_item_payload(self) -> dict[str, Any]:
        """Build the Trakt request item: ids plus optional title and year."""
        payload: dict[str, Any] = {"ids": self.build_ids_dict()}
        if self.title:
            payload["title"] = self.title
        if self.year:
            payload["year"] = self.year
        return payload


class CollectionRequestItem(CollectionItemIdentifier):
    """Identify one item for a collection addition, with optional notes."""

    notes: str | None = Field(
        default=None,
        max_length=500,
        description="Optional notes (VIP only, 500 char max)",
    )

    @field_validator("notes", mode="before")
    @classmethod
    def _strip_notes(cls, v: object) -> object:
        """Strip whitespace from notes field."""
        return v.strip() if isinstance(v, str) else v

    def build_item_payload(self) -> dict[str, Any]:
        """Build the Trakt request item, including notes when supplied."""
        payload = super().build_item_payload()
        if self.notes:
            payload["notes"] = self.notes
        return payload
