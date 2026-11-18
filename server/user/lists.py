"""MCP tools for managing the authenticated user's personal lists."""

import re
from typing import Annotated, ClassVar

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, StringConstraints, field_validator

from client.pool import get_client
from client.user.lists import UserListsClient
from config.api import DEFAULT_LIMIT
from config.mcp.descriptions import (
    LIMIT_DESCRIPTION,
    PAGE_DESCRIPTION,
    USER_LIST_ALLOW_COMMENTS_DESCRIPTION,
    USER_LIST_DESCRIPTION_DESCRIPTION,
    USER_LIST_DISPLAY_NUMBERS_DESCRIPTION,
    USER_LIST_ID_DESCRIPTION,
    USER_LIST_ITEM_TYPE_DESCRIPTION,
    USER_LIST_ITEMS_DESCRIPTION,
    USER_LIST_NAME_DESCRIPTION,
    USER_LIST_PRIVACY_DESCRIPTION,
    USER_LIST_READ_ITEM_TYPE_DESCRIPTION,
    USER_LIST_REMOVE_ITEMS_DESCRIPTION,
    USER_LIST_SORT_BY_DESCRIPTION,
    USER_LIST_SORT_HOW_DESCRIPTION,
)
from models.formatters.user_lists import UserListFormatters
from models.user.lists import (
    LIST_COLLECTION_ITEM_TYPES,
    CreateUserList,
    ListNameText,
    ListPrivacy,
    ListSortBy,
    ListSortHow,
    UpdateUserList,
    UserListCollection,
    UserListItemsRequest,
)
from server.base import (
    CollectionItemIdentifier,
    CollectionRequestItem,
    LimitOnly,
    ToolErrors,
    unwrap_or_raise,
)
from utils.api.errors import handle_api_errors_func

ListId = Annotated[str | int, Field(description=USER_LIST_ID_DESCRIPTION)]
ListName = Annotated[ListNameText, Field(description=USER_LIST_NAME_DESCRIPTION)]
ListDescription = Annotated[
    str | None, Field(description=USER_LIST_DESCRIPTION_DESCRIPTION)
]
Privacy = Annotated[
    ListPrivacy | None, Field(description=USER_LIST_PRIVACY_DESCRIPTION)
]
DisplayNumbers = Annotated[
    bool | None, Field(description=USER_LIST_DISPLAY_NUMBERS_DESCRIPTION)
]
AllowComments = Annotated[
    bool | None, Field(description=USER_LIST_ALLOW_COMMENTS_DESCRIPTION)
]
SortBy = Annotated[ListSortBy | None, Field(description=USER_LIST_SORT_BY_DESCRIPTION)]
SortHow = Annotated[
    ListSortHow | None, Field(description=USER_LIST_SORT_HOW_DESCRIPTION)
]
ItemType = Annotated[
    UserListCollection, Field(description=USER_LIST_ITEM_TYPE_DESCRIPTION)
]


class UserListItemIdentifier(CollectionItemIdentifier):
    """Identify a list item to remove; people take IMDB ``nm`` IDs."""

    _identifier_error_prefix: ClassVar[str] = "List item"

    @field_validator("imdb_id", mode="after")
    @classmethod
    def _validate_imdb_id_format(cls, v: str | None) -> str | None:
        """Accept title IDs (tt) and person IDs (nm)."""
        if v is not None and not re.match(r"^(tt|nm)\d+$", v):
            raise ValueError(
                "imdb_id must be 'tt' or 'nm' followed by digits"
                + f" (e.g., 'tt0468569', 'nm0000206'), got: '{v}'"
            )
        return v


class UserListRequestItem(UserListItemIdentifier, CollectionRequestItem):
    """Identify a list item to add, with optional VIP notes."""


class UserListIdentifier(BaseModel):
    """Validate a list identifier before constructing an endpoint."""

    list_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class UserListItemsParams(LimitOnly):
    """Validate list-content filters and standard limit/page combinations."""

    item_type: UserListCollection | None = None


def _list_id(list_id: str | int) -> str:
    return UserListIdentifier(list_id=str(list_id)).list_id


def _result_or_raise[T](result: T | str, operation: str, list_id: str = "me") -> T:
    return unwrap_or_raise(
        result, resource_type="user_list", resource_id=list_id, operation=operation
    )


def _items_request(
    item_type: UserListCollection,
    items: list[UserListRequestItem] | list[UserListItemIdentifier],
) -> UserListItemsRequest:
    return UserListItemsRequest.model_validate(
        {item_type: [item.build_item_payload() for item in items]}
    )


@handle_api_errors_func
async def fetch_user_lists() -> str:
    """Fetch your personal lists with IDs, slugs, privacy, counts and descriptions.

    Requires OAuth.
    """
    result = await get_client(UserListsClient).get_user_lists()
    return UserListFormatters.format_lists(_result_or_raise(result, "fetch_user_lists"))


@handle_api_errors_func
async def fetch_user_list_items(
    list_id: ListId,
    item_type: Annotated[
        UserListCollection | None,
        Field(description=USER_LIST_READ_ITEM_TYPE_DESCRIPTION),
    ] = None,
    limit: Annotated[int, Field(description=LIMIT_DESCRIPTION)] = DEFAULT_LIMIT,
    page: Annotated[int | None, Field(description=PAGE_DESCRIPTION)] = None,
) -> str:
    """Read items of your own list, including private lists. Requires OAuth.

    Filter by one item type, or omit for all types. With page omitted,
    auto-paginates up to limit total items (0 uses the repository safety cap).
    With page specified, returns that page and navigation metadata.
    """
    identifier = _list_id(list_id)
    params = UserListItemsParams(item_type=item_type, limit=limit, page=page)
    result = await get_client(UserListsClient).get_user_list_items(
        identifier,
        item_type=LIST_COLLECTION_ITEM_TYPES[params.item_type]
        if params.item_type
        else None,
        limit=params.limit,
        page=params.page,
    )
    return UserListFormatters.format_list_items(
        _result_or_raise(result, "fetch_user_list_items", identifier), identifier
    )


@handle_api_errors_func
async def create_user_list(
    name: ListName,
    description: ListDescription = None,
    privacy: Privacy = None,
    display_numbers: DisplayNumbers = None,
    allow_comments: AllowComments = None,
    sort_by: SortBy = None,
    sort_how: SortHow = None,
) -> str:
    """Create your personal list. Only name is required; private by default.

    Requires OAuth.
    """
    request = CreateUserList(
        name=name,
        description=description,
        privacy=privacy,
        display_numbers=display_numbers,
        allow_comments=allow_comments,
        sort_by=sort_by,
        sort_how=sort_how,
    )
    result = await get_client(UserListsClient).create_user_list(request)
    user_list = _result_or_raise(result, "create_user_list")
    return "Created personal list.\n\n" + UserListFormatters.format_lists([user_list])


@handle_api_errors_func
async def update_user_list(
    list_id: ListId,
    name: Annotated[
        ListNameText | None, Field(description=USER_LIST_NAME_DESCRIPTION)
    ] = None,
    description: ListDescription = None,
    privacy: Privacy = None,
    display_numbers: DisplayNumbers = None,
    allow_comments: AllowComments = None,
    sort_by: SortBy = None,
    sort_how: SortHow = None,
) -> str:
    """Update your personal list by numeric ID or slug.

    Supply at least one field; omitted fields stay unchanged. Requires OAuth.
    """
    identifier = _list_id(list_id)
    request = UpdateUserList(
        name=name,
        description=description,
        privacy=privacy,
        display_numbers=display_numbers,
        allow_comments=allow_comments,
        sort_by=sort_by,
        sort_how=sort_how,
    )
    result = await get_client(UserListsClient).update_user_list(identifier, request)
    user_list = _result_or_raise(result, "update_user_list", identifier)
    return "Updated personal list.\n\n" + UserListFormatters.format_lists([user_list])


@handle_api_errors_func
async def delete_user_list(list_id: ListId) -> str:
    """Permanently delete your personal list and all its items by ID or slug.

    Requires OAuth.
    """
    identifier = _list_id(list_id)
    result = await get_client(UserListsClient).delete_user_list(identifier)
    _result_or_raise(result, "delete_user_list", identifier)
    return f"Deleted personal list: {identifier}."


@handle_api_errors_func
async def add_user_list_items(
    list_id: ListId,
    item_type: ItemType,
    items: Annotated[
        list[UserListRequestItem],
        Field(description=USER_LIST_ITEMS_DESCRIPTION, min_length=1),
    ],
) -> str:
    """Add movies, shows, seasons, episodes or people to your personal list.

    Supports optional VIP notes. Requires OAuth.
    """
    identifier = _list_id(list_id)
    request = _items_request(item_type, items)
    result = await get_client(UserListsClient).add_user_list_items(identifier, request)
    summary = _result_or_raise(result, "add_user_list_items", identifier)
    return UserListFormatters.format_items(summary, "added", item_type, identifier)


@handle_api_errors_func
async def remove_user_list_items(
    list_id: ListId,
    item_type: ItemType,
    items: Annotated[
        list[UserListItemIdentifier],
        Field(description=USER_LIST_REMOVE_ITEMS_DESCRIPTION, min_length=1),
    ],
) -> str:
    """Remove movies, shows, seasons, episodes or people from your personal list.

    Requires OAuth.
    """
    identifier = _list_id(list_id)
    request = _items_request(item_type, items)
    result = await get_client(UserListsClient).remove_user_list_items(
        identifier, request
    )
    summary = _result_or_raise(result, "remove_user_list_items", identifier)
    return UserListFormatters.format_items(summary, "removed", item_type, identifier)


def register_user_list_tools(mcp: FastMCP) -> None:
    """Register OAuth-only personal list management tools in the user domain."""
    for handler in (
        fetch_user_lists,
        create_user_list,
        update_user_list,
        delete_user_list,
        add_user_list_items,
        remove_user_list_items,
        fetch_user_list_items,
    ):
        wrapped = ToolErrors.with_error_handling(
            operation=f"{handler.__name__}_tool", tool=handler.__name__
        )(handler)
        mcp.tool(name=handler.__name__)(wrapped)
