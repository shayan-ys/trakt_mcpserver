"""Request and response models for personal user lists."""

from datetime import datetime
from typing import Annotated, ClassVar, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

from models.movies.movie import TraktMovie
from models.shows.episode import TraktEpisode
from models.shows.show import TraktShow
from models.sync.watchlist import (
    SyncWatchlistNotFound,
    SyncWatchlistSummaryCount,
    TraktSeason,
    TraktSyncWatchlistRequest,
)
from models.types.ids import TraktPersonIds

ListPrivacy = Literal["private", "link", "friends", "public"]
ListSortBy = Literal[
    "rank",
    "added",
    "title",
    "released",
    "runtime",
    "popularity",
    "random",
    "percentage",
    "imdb_rating",
    "tmdb_rating",
    "rt_tomatometer",
    "rt_audience",
    "metascore",
    "votes",
    "imdb_votes",
    "tmdb_votes",
    "my_rating",
    "watched",
    "collected",
]
ListSortHow = Literal["asc", "desc"]
UserListItemType = Literal["movie", "show", "season", "episode", "person"]
UserListCollection = Literal["movies", "shows", "seasons", "episodes", "people"]
LIST_COLLECTION_ITEM_TYPES: dict[UserListCollection, UserListItemType] = {
    "movies": "movie",
    "shows": "show",
    "seasons": "season",
    "episodes": "episode",
    "people": "person",
}
ListNameText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class UserListFields(BaseModel):
    """Optional fields shared by list creation and updates."""

    description: str | None = None
    privacy: ListPrivacy | None = None
    display_numbers: bool | None = None
    allow_comments: bool | None = None
    sort_by: ListSortBy | None = None
    sort_how: ListSortHow | None = None


class CreateUserList(UserListFields):
    """Create a personal list, leaving omitted defaults to Trakt."""

    name: ListNameText


class UpdateUserList(UserListFields):
    """Update at least one field without overwriting omitted settings."""

    name: ListNameText | None = None

    @model_validator(mode="after")
    def require_changes(self) -> "UpdateUserList":
        """Reject updates with no non-null fields."""
        if not self.model_dump(exclude_none=True):
            raise ValueError("Provide at least one field to update")
        return self


class UserListIds(BaseModel):
    """Stable Trakt list identifier and slug."""

    trakt: int
    slug: str


class UserList(BaseModel):
    """Personal list metadata returned by Trakt."""

    name: str
    description: str | None = None
    privacy: ListPrivacy
    item_count: int = Field(ge=0)
    ids: UserListIds


class UserListPerson(BaseModel):
    """Person identity within a personal list item."""

    name: str
    ids: TraktPersonIds


class UserListPersonRequestItem(BaseModel):
    """Person entry for list add/remove requests, identified by IDs only."""

    name: str | None = None
    ids: TraktPersonIds
    notes: str | None = Field(
        default=None, max_length=500, description="User notes (VIP only)"
    )

    @model_validator(mode="after")
    def require_identifier(self) -> "UserListPersonRequestItem":
        """People have no year, so title and year cannot identify them."""
        if not self.ids.model_dump(exclude_none=True):
            raise ValueError(
                "List person item must include trakt_id, slug, imdb_id or tmdb_id"
            )
        return self


class UserListItemsRequest(TraktSyncWatchlistRequest):
    """List add/remove payload: one item collection, which may be people."""

    FIELDS: ClassVar[tuple[str, ...]] = (*TraktSyncWatchlistRequest.FIELDS, "people")

    people: list[UserListPersonRequestItem] | None = Field(
        default=None, min_length=1, description="List payload for people"
    )


class UserListSummaryCount(SyncWatchlistSummaryCount):
    """List add/remove counts, including people."""

    people: int = Field(default=0, ge=0)


class UserListNotFound(SyncWatchlistNotFound):
    """List items Trakt could not match, including people."""

    people: Annotated[list[UserListPersonRequestItem], Field(default_factory=list)]


class UserListItemsSummary(BaseModel):
    """List add/remove result with counts and unmatched items."""

    added: UserListSummaryCount | None = None
    existing: UserListSummaryCount | None = None
    deleted: UserListSummaryCount | None = None
    not_found: UserListNotFound = Field(
        default_factory=lambda: UserListNotFound(
            movies=[], shows=[], seasons=[], episodes=[], people=[]
        )
    )


class UserListItem(BaseModel):
    """Personal list entry, distinct from the underlying media's Trakt ID."""

    rank: int = Field(ge=1)
    id: int = Field(ge=1)
    listed_at: datetime
    notes: str | None = None
    type: UserListItemType
    movie: TraktMovie | None = None
    show: TraktShow | None = None
    season: TraktSeason | None = None
    episode: TraktEpisode | None = None
    person: UserListPerson | None = None
