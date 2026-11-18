"""Markdown formatting for personal list metadata, contents and summaries."""

from typing import TYPE_CHECKING

from models.formatters.utils import format_pagination_header, format_title_year
from models.types.pagination import PaginatedResponse
from models.user.lists import (
    UserList,
    UserListCollection,
    UserListItem,
    UserListItemsSummary,
)

if TYPE_CHECKING:
    from models.sync.watchlist import TraktSyncWatchlistItem
    from models.user.lists import UserListPersonRequestItem


class UserListFormatters:
    """Format personal list metadata, contents and mutation results."""

    @staticmethod
    def format_lists(lists: list[UserList]) -> str:
        """Display list identifiers, visibility, item counts and descriptions."""
        lines = ["# Your Personal Lists", ""]
        if not lists:
            lines.append("You have no personal lists.")
        for user_list in lists:
            lines.extend(
                [
                    f"## {user_list.name}",
                    f"- Trakt ID: {user_list.ids.trakt}",
                    f"- Slug: {user_list.ids.slug}",
                    f"- Privacy: {user_list.privacy}",
                    f"- Items: {user_list.item_count}",
                    f"- Description: {user_list.description or ''}",
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def format_items(
        summary: UserListItemsSummary,
        operation: str,
        item_type: UserListCollection,
        list_id: str,
    ) -> str:
        """Report changed, existing and not-found items for one list mutation."""
        lines = [f"# List {operation.title()} - {item_type.title()}", ""]
        lines.append(f"List: {list_id}")
        lines.append("")
        counts = summary.added if operation == "added" else summary.deleted
        total = getattr(counts, item_type) if counts else 0
        if total:
            lines.append(
                f"✅ Successfully {operation} **{total}** {item_type} item(s)"
                + f" {'to' if operation == 'added' else 'from'} your list."
            )
        else:
            lines.append(f"No {item_type} items were {operation}.")
        lines.append("")
        existing = getattr(summary.existing, item_type) if summary.existing else 0
        if operation == "added" and existing:
            lines.append(f"## Items Already in List ({existing})")
            lines.append("")
        not_found: list[TraktSyncWatchlistItem] | list[UserListPersonRequestItem] = (
            getattr(summary.not_found, item_type)
        )
        if not_found:
            lines.append(f"## Items Not Found ({len(not_found)})")
            lines.append("")
            for item in not_found:
                ids: dict[str, object] = (
                    item.ids.model_dump(exclude_none=True) if item.ids else {}
                )
                label = ", ".join(f"{key}: {value}" for key, value in ids.items())
                lines.append(f"- {label or 'Unknown item'}")
        return "\n".join(lines)

    @staticmethod
    def format_list_items(
        data: list[UserListItem] | PaginatedResponse[UserListItem], list_id: str
    ) -> str:
        """Display item identity, notes and page navigation when available."""
        lines = [f"# Your Personal List Items: {list_id}", ""]
        if isinstance(data, PaginatedResponse):
            lines.append(format_pagination_header(data))
            items = data.data
        else:
            items = data
        if not items:
            lines.append("No items found in this list.")
        for item in items:
            title = "Unavailable item"
            year: int | None = None
            ids = None
            if item.type == "movie" and item.movie:
                title, year, ids = item.movie.title, item.movie.year, item.movie.ids
            elif item.type == "show" and item.show:
                title, year, ids = item.show.title, item.show.year, item.show.ids
            elif item.type == "season" and item.season:
                title = f"Season {item.season.number}"
                ids = item.season.ids
                if item.show:
                    title = f"{item.show.title} - {title}"
                    year = item.show.year
            elif item.type == "episode" and item.episode:
                title = f"S{item.episode.season:02d}E{item.episode.number:02d}"
                if item.episode.title:
                    title += f": {item.episode.title}"
                ids = item.episode.ids
                if item.show:
                    title = f"{item.show.title} - {title}"
                    year = item.show.year
            elif item.type == "person" and item.person:
                title, ids = item.person.name, item.person.ids
            trakt_id = ids.trakt if ids is not None else None
            lines.append(
                f"- #{item.rank} **{format_title_year(title, year)}**"
                + f" | Type: {item.type} | Trakt ID: {trakt_id or 'N/A'}"
                + f" | List item ID: {item.id}"
            )
            if item.notes:
                lines.append(f"  - Notes: {item.notes}")
        return "\n".join(lines)
