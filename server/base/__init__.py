"""Base classes and mixins for MCP server components."""

from .collection_inputs import CollectionItemIdentifier, CollectionRequestItem
from .error_mixin import ToolErrors, unwrap_or_raise
from .identifier_mixin import IdentifierValidatorMixin
from .limit_page_mixin import LimitPageValidatorMixin
from .params import (
    CommentIdParam,
    EpisodeIdParam,
    LimitOnly,
    MovieIdParam,
    PeriodParams,
    PersonIdParam,
    SeasonIdParam,
    ShowIdParam,
)

__all__ = [
    "CollectionItemIdentifier",
    "CollectionRequestItem",
    "CommentIdParam",
    "EpisodeIdParam",
    "IdentifierValidatorMixin",
    "LimitOnly",
    "LimitPageValidatorMixin",
    "MovieIdParam",
    "PeriodParams",
    "PersonIdParam",
    "SeasonIdParam",
    "ShowIdParam",
    "ToolErrors",
    "unwrap_or_raise",
]
