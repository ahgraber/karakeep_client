import asyncio
import json
from unittest.mock import AsyncMock, mock_open, patch

from hypothesis import assume, given, settings, strategies as st
import pytest

from karakeep_client.karakeep import APIError, AuthenticationError, KarakeepClient


@pytest.fixture
def client():
    return KarakeepClient(api_key="test_key", base_url="https://test.karakeep.app")


@pytest.fixture
def sample_bookmark_data():
    """Sample bookmark data that matches OpenAPI schema."""
    return {
        "id": "bookmark1",
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": "2023-01-01T00:00:00Z",
        "title": "Test Bookmark 1",
        "archived": False,
        "favourited": True,
        "taggingStatus": "success",
        "summarizationStatus": "pending",
        "note": None,
        "summary": None,
        "tags": [],
        "content": {"type": "link", "url": "https://example.com"},
        "assets": [],
    }


@pytest.fixture
def sample_paginated_response():
    """Sample paginated bookmarks response."""
    return {
        "bookmarks": [
            {
                "id": "bookmark1",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": "2023-01-01T00:00:00Z",
                "title": "Test Bookmark 1",
                "archived": False,
                "favourited": True,
                "taggingStatus": "success",
                "summarizationStatus": "pending",
                "note": None,
                "summary": None,
                "tags": [],
                "content": {"type": "link", "url": "https://example.com"},
                "assets": [],
            }
        ],
        "nextCursor": "next_page_cursor",
    }


@pytest.fixture
def sample_asset_data():
    """Sample asset data that matches OpenAPI schema."""
    return {
        "assetId": "asset123",
        "fileName": "test.pdf",
        "contentType": "application/pdf",
        "size": 1024,
    }


@pytest.fixture
def sample_error_response():
    """Sample API error response matching OpenAPI schema."""
    return {"code": "NOT_FOUND", "message": "Bookmark not found"}


@pytest.mark.asyncio
async def test_get_bookmarks_paged_success(client: KarakeepClient, sample_paginated_response):
    # Arrange
    with patch.object(client, "_call", return_value=sample_paginated_response):
        # Act
        result = await client.get_bookmarks_paged(limit=1)

    # Assert
    assert len(result.bookmarks) == 1
    assert result.bookmarks[0].id == "bookmark1"
    assert result.next_cursor == "next_page_cursor"


@pytest.mark.asyncio
async def test_get_bookmarks_paged_limit_validation(client: KarakeepClient):
    """Test that get_bookmarks_paged validates limit parameter according to OpenAPI spec."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Maximum limit is 100"):
        await client.get_bookmarks_paged(limit=101)


@pytest.mark.asyncio
async def test_get_bookmarks_paged_with_all_parameters(client: KarakeepClient, sample_paginated_response):
    """Test get_bookmarks_paged with all optional parameters."""
    # Arrange
    with patch.object(client, "_call", return_value=sample_paginated_response) as mock_call:
        # Act
        await client.get_bookmarks_paged(
            archived=True, favourited=False, sort_order="asc", limit=50, cursor="some_cursor", include_content=True
        )

    # Assert
    mock_call.assert_called_once_with(
        "GET",
        "bookmarks",
        params={
            "archived": True,
            "favourited": False,
            "sortOrder": "asc",
            "limit": 50,
            "cursor": "some_cursor",
            "includeContent": True,
        },
    )


@pytest.mark.asyncio
async def test_get_bookmarks_paged_none_params_filtered(client: KarakeepClient, sample_paginated_response):
    """Test that None parameters are filtered out of request."""
    # Arrange
    with patch.object(client, "_call", return_value=sample_paginated_response) as mock_call:
        # Act
        await client.get_bookmarks_paged(archived=None, favourited=None)

    # Assert - all parameters are passed, filtering happens in _call
    mock_call.assert_called_once_with(
        "GET",
        "bookmarks",
        params={
            "archived": None,
            "favourited": None,
            "sortOrder": None,
            "limit": None,
            "cursor": None,
            "includeContent": False,
        },
    )


@pytest.mark.asyncio
async def test_get_bookmark_success(client: KarakeepClient, sample_bookmark_data):
    # Arrange
    bookmark_id = "bookmark1"

    with patch.object(client, "_call", return_value=sample_bookmark_data):
        # Act
        result = await client.get_bookmark(bookmark_id)

    # Assert
    assert result.id == bookmark_id
    assert result.title == "Test Bookmark 1"


@pytest.mark.asyncio
async def test_get_bookmark_with_include_content_param(client: KarakeepClient, sample_bookmark_data):
    """Test get_bookmark respects include_content parameter."""
    # Arrange
    bookmark_id = "bookmark1"
    with patch.object(client, "_call", return_value=sample_bookmark_data) as mock_call:
        # Act
        await client.get_bookmark(bookmark_id, include_content=False)

    # Assert
    mock_call.assert_called_once_with("GET", f"bookmarks/{bookmark_id}", params={"includeContent": False})


@pytest.mark.asyncio
async def test_search_bookmarks_success(client: KarakeepClient, sample_paginated_response):
    """Test search_bookmarks with required query parameter."""
    # Arrange
    query = "test query"
    with patch.object(client, "_call", return_value=sample_paginated_response) as mock_call:
        # Act
        result = await client.search_bookmarks(query)

    # Assert
    assert len(result.bookmarks) == 1
    assert result.bookmarks[0].id == "bookmark1"
    mock_call.assert_called_once_with(
        "GET",
        "bookmarks/search",
        params={"q": query, "sortOrder": None, "limit": None, "cursor": None, "includeContent": True},
    )


@pytest.mark.asyncio
async def test_search_bookmarks_with_all_parameters(client: KarakeepClient, sample_paginated_response):
    """Test search_bookmarks with all optional parameters."""
    # Arrange
    with patch.object(client, "_call", return_value=sample_paginated_response) as mock_call:
        # Act
        await client.search_bookmarks(
            q="python", sort_order="relevance", limit=25, cursor="search_cursor", include_content=False
        )

    # Assert
    mock_call.assert_called_once_with(
        "GET",
        "bookmarks/search",
        params={
            "q": "python",
            "sortOrder": "relevance",
            "limit": 25,
            "cursor": "search_cursor",
            "includeContent": False,
        },
    )


@pytest.mark.asyncio
async def test_search_bookmarks_limit_validation(client: KarakeepClient):
    """Test that search_bookmarks validates limit parameter."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Maximum limit is 100"):
        await client.search_bookmarks("query", limit=101)


@pytest.mark.asyncio
async def test_create_bookmark_link_type_success(client: KarakeepClient, sample_bookmark_data):
    """Test create_bookmark with link type."""
    # Arrange
    with patch.object(client, "_call", return_value=sample_bookmark_data) as mock_call:
        # Act
        result = await client.create_bookmark(
            bookmark_type="link", url="https://example.com", title="Test Link", favourited=True
        )

    # Assert
    assert result.id == "bookmark1"
    mock_call.assert_called_once_with(
        "POST",
        "bookmarks",
        data={"type": "link", "url": "https://example.com", "title": "Test Link", "favourited": True},
    )


@pytest.mark.asyncio
async def test_create_bookmark_text_type_success(client: KarakeepClient, sample_bookmark_data):
    """Test create_bookmark with text type."""
    # Arrange
    text_bookmark_data = sample_bookmark_data.copy()
    text_bookmark_data["content"] = {"type": "text", "text": "Sample text content"}

    with patch.object(client, "_call", return_value=text_bookmark_data) as mock_call:
        # Act
        result = await client.create_bookmark(
            bookmark_type="text", text="Sample text content", source_url="https://source.example.com"
        )

    # Assert
    assert result.id == "bookmark1"
    mock_call.assert_called_once_with(
        "POST",
        "bookmarks",
        data={"type": "text", "text": "Sample text content", "sourceUrl": "https://source.example.com"},
    )


@pytest.mark.asyncio
async def test_create_bookmark_asset_type_success(client: KarakeepClient, sample_bookmark_data):
    """Test create_bookmark with asset type."""
    # Arrange
    asset_bookmark_data = sample_bookmark_data.copy()
    asset_bookmark_data["content"] = {"type": "asset", "assetType": "pdf", "assetId": "asset123"}

    with patch.object(client, "_call", return_value=asset_bookmark_data) as mock_call:
        # Act
        result = await client.create_bookmark(
            bookmark_type="asset", asset_type="pdf", asset_id="asset123", file_name="document.pdf"
        )

    # Assert
    assert result.id == "bookmark1"
    mock_call.assert_called_once_with(
        "POST",
        "bookmarks",
        data={"type": "asset", "assetType": "pdf", "assetId": "asset123", "fileName": "document.pdf"},
    )


@pytest.mark.asyncio
async def test_create_bookmark_link_missing_url(client: KarakeepClient):
    """Test create_bookmark link type validation."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Argument 'url' is required"):
        await client.create_bookmark(bookmark_type="link")


@pytest.mark.asyncio
async def test_create_bookmark_text_missing_text(client: KarakeepClient):
    """Test create_bookmark text type validation."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Argument 'text' is required"):
        await client.create_bookmark(bookmark_type="text")


@pytest.mark.asyncio
async def test_create_bookmark_asset_missing_fields(client: KarakeepClient):
    """Test create_bookmark asset type validation."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="Argument 'asset_id' is required"):
        await client.create_bookmark(bookmark_type="asset", asset_type="pdf")


@pytest.mark.asyncio
async def test_delete_bookmark_success(client: KarakeepClient):
    """Test delete_bookmark returns None on success."""
    # Arrange
    bookmark_id = "bookmark1"
    with patch.object(client, "_call", return_value={}) as mock_call:
        # Act
        result = await client.delete_bookmark(bookmark_id)

    # Assert
    assert result is None
    mock_call.assert_called_once_with("DELETE", f"bookmarks/{bookmark_id}")


@pytest.mark.asyncio
async def test_update_bookmark_success(client: KarakeepClient):
    """Test update_bookmark with partial data."""
    # Arrange
    bookmark_id = "bookmark1"
    update_data = {"title": "Updated Title", "archived": True}
    mock_response = {
        "id": bookmark_id,
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": "2023-01-02T00:00:00Z",
        "title": "Updated Title",
        "archived": True,
        "favourited": False,
        "taggingStatus": "success",
        "summarizationStatus": "success",
        "userId": "user1",
    }

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        # Act
        result = await client.update_bookmark(bookmark_id, update_data)

    # Assert
    from karakeep_client.models import BookmarkUpdateResponse

    assert isinstance(result, BookmarkUpdateResponse)
    assert result.id == bookmark_id
    assert result.archived is True
    mock_call.assert_called_once_with("PATCH", f"bookmarks/{bookmark_id}", data=update_data)


@pytest.mark.asyncio
async def test_update_bookmark_minimal_patch_response(client: KarakeepClient):
    """PATCH response without tags/content/assets validates without error."""
    mock_response = {
        "id": "bookmark1",
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": None,
        "archived": False,
        "favourited": False,
        "taggingStatus": None,
        "summarizationStatus": None,
        "userId": "user1",
    }

    with patch.object(client, "_call", return_value=mock_response):
        result = await client.update_bookmark("bookmark1", {"archived": False})

    from karakeep_client.models import BookmarkUpdateResponse

    assert isinstance(result, BookmarkUpdateResponse)
    assert result.title is None
    assert result.note is None


@pytest.mark.asyncio
async def test_add_bookmark_tags_with_tag_ids(client: KarakeepClient):
    """Test add_bookmark_tags with tag IDs."""
    # Arrange
    bookmark_id = "bookmark1"
    tag_ids = ["tag1", "tag2"]
    mock_response = {"attached": tag_ids}

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        # Act
        result = await client.add_bookmark_tags(bookmark_id, tag_ids=tag_ids)

    # Assert
    from karakeep_client.models import BookmarkTagsAttachResponse

    assert isinstance(result, BookmarkTagsAttachResponse)
    assert result.attached == tag_ids
    mock_call.assert_called_once_with(
        "POST", f"bookmarks/{bookmark_id}/tags", data={"tags": [{"tagId": "tag1"}, {"tagId": "tag2"}]}
    )


@pytest.mark.asyncio
async def test_add_bookmark_tags_with_tag_names(client: KarakeepClient):
    """Test add_bookmark_tags with tag names."""
    # Arrange
    bookmark_id = "bookmark1"
    tag_names = ["python", "tutorial"]
    mock_response = {"attached": ["tag1", "tag2"]}

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        # Act
        result = await client.add_bookmark_tags(bookmark_id, tag_names=tag_names)

    # Assert
    from karakeep_client.models import BookmarkTagsAttachResponse

    assert isinstance(result, BookmarkTagsAttachResponse)
    assert result.attached == ["tag1", "tag2"]
    mock_call.assert_called_once_with(
        "POST", f"bookmarks/{bookmark_id}/tags", data={"tags": [{"tagName": "python"}, {"tagName": "tutorial"}]}
    )


@pytest.mark.asyncio
async def test_delete_bookmark_tags_success(client: KarakeepClient):
    """Test delete_bookmark_tags returns BookmarkTagsDetachResponse."""
    bookmark_id = "bookmark1"
    tag_ids = ["tag1", "tag2"]
    mock_response = {"detached": tag_ids}

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        result = await client.delete_bookmark_tags(bookmark_id, tag_ids=tag_ids)

    from karakeep_client.models import BookmarkTagsDetachResponse

    assert isinstance(result, BookmarkTagsDetachResponse)
    assert result.detached == tag_ids
    mock_call.assert_called_once_with(
        "DELETE", f"bookmarks/{bookmark_id}/tags", data={"tags": [{"tagId": "tag1"}, {"tagId": "tag2"}]}
    )


@pytest.mark.asyncio
async def test_add_bookmark_tags_with_attached_by(client: KarakeepClient):
    """attached_by is emitted on every tag entry in the request body."""
    bookmark_id = "bookmark1"
    mock_response = {"attached": ["tag1"]}

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        await client.add_bookmark_tags(
            bookmark_id, tag_ids=["tag1"], tag_names=["python"], attached_by="ai"
        )

    mock_call.assert_called_once_with(
        "POST",
        f"bookmarks/{bookmark_id}/tags",
        data={"tags": [{"tagId": "tag1", "attachedBy": "ai"}, {"tagName": "python", "attachedBy": "ai"}]},
    )


@pytest.mark.asyncio
async def test_delete_bookmark_tags_with_attached_by(client: KarakeepClient):
    """attached_by is emitted on every tag entry for detach requests too."""
    bookmark_id = "bookmark1"
    mock_response = {"detached": ["tag1"]}

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        await client.delete_bookmark_tags(bookmark_id, tag_ids=["tag1"], attached_by="human")

    mock_call.assert_called_once_with(
        "DELETE",
        f"bookmarks/{bookmark_id}/tags",
        data={"tags": [{"tagId": "tag1", "attachedBy": "human"}]},
    )


@pytest.mark.asyncio
async def test_create_bookmark_with_source(client: KarakeepClient, sample_bookmark_data):
    """source is forwarded to the API when provided."""
    with patch.object(client, "_call", return_value=sample_bookmark_data) as mock_call:
        await client.create_bookmark(
            bookmark_type="link", url="https://example.com", source="import"
        )

    mock_call.assert_called_once_with(
        "POST",
        "bookmarks",
        data={"type": "link", "url": "https://example.com", "source": "import"},
    )


@pytest.mark.asyncio
async def test_add_bookmark_tags_validation_no_tags(client: KarakeepClient):
    """Test add_bookmark_tags validates that at least one tag source is provided."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="At least one of 'tag_ids' or 'tag_names' must be provided"):
        await client.add_bookmark_tags("bookmark1")


@pytest.mark.asyncio
async def test_add_bookmark_tags_validation_invalid_type(client: KarakeepClient):
    """Test add_bookmark_tags validates tag_ids type."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match="'tag_ids' must be a list"):
        # Use type: ignore to test runtime validation
        await client.add_bookmark_tags("bookmark1", tag_ids="not_a_list")  # type: ignore


def test_create_reuses_existing_client_instance(client: KarakeepClient):
    """Test create() reuses the stored AsyncClient instance."""
    # Arrange
    reusable_client = AsyncMock()

    with patch.object(KarakeepClient, "_ensure_client", return_value=reusable_client) as mock_ensure:
        # Act
        first_client = client.create()
        second_client = client.create()

    # Assert
    assert first_client is second_client is reusable_client
    mock_ensure.assert_called_once()


@pytest.mark.asyncio
async def test_call_with_reusable_client_passes_existing_instance(client: KarakeepClient):
    """Test _call uses an existing client instead of creating a new one."""
    # Arrange
    reusable_client = AsyncMock()
    client._client = reusable_client

    with patch.object(client, "_make_request", AsyncMock(return_value={"ok": True})) as mock_make_request:
        # Act
        response = await client._call("GET", "bookmarks")

    # Assert
    assert response == {"ok": True}
    mock_make_request.assert_awaited_once()
    assert mock_make_request.await_args.args[0] is reusable_client


@pytest.mark.asyncio
async def test_call_without_reusable_client_uses_temporary_client(client: KarakeepClient):
    """Test _call creates and cleans up a temporary AsyncClient when none is stored."""
    # Arrange
    temp_client = AsyncMock()
    temp_client.__aenter__.return_value = temp_client
    temp_client.__aexit__.return_value = None

    with (
        patch.object(client, "_ensure_client", return_value=temp_client) as mock_ensure,
        patch.object(client, "_make_request", AsyncMock(return_value={"ok": True})) as mock_make_request,
    ):
        # Act
        response = await client._call("GET", "bookmarks")

    # Assert
    assert response == {"ok": True}
    mock_ensure.assert_called_once()
    mock_make_request.assert_awaited_once()
    assert mock_make_request.await_args.args[0] is temp_client
    temp_client.__aenter__.assert_awaited_once()
    temp_client.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_async_context_manager_manages_client_lifecycle(client: KarakeepClient):
    """Test async context manager creates and then closes the reusable client."""
    # Arrange
    managed_client = AsyncMock()

    with patch.object(KarakeepClient, "_ensure_client", return_value=managed_client) as mock_ensure:
        # Act
        async with client as scoped_client:
            assert scoped_client is client
            assert client._client is managed_client
            mock_ensure.assert_called_once()
            managed_client.aclose.assert_not_awaited()

    # Assert
    managed_client.aclose.assert_awaited_once()
    assert client._client is None


@pytest.mark.asyncio
async def test_aclose_closes_and_clears_reusable_client(client: KarakeepClient):
    """Test aclose() shuts down the stored client and clears the reference."""
    # Arrange
    reusable_client = AsyncMock()
    client._client = reusable_client

    # Act
    await client.aclose()

    # Assert
    reusable_client.aclose.assert_awaited_once()
    assert client._client is None


@pytest.mark.asyncio
async def test_close_raises_when_called_inside_running_loop(client: KarakeepClient):
    """Test close() refuses to run when an event loop is active."""
    # Arrange
    reusable_client = AsyncMock()
    client._client = reusable_client

    # Act & Assert
    with pytest.raises(RuntimeError, match=r"close\(\) cannot be called while an event loop is running"):
        client.close()

    reusable_client.aclose.assert_not_awaited()


def test_close_runs_async_close_when_no_running_loop(client: KarakeepClient):
    """Test close() runs aclose() when no event loop is running."""
    # Arrange
    reusable_client = AsyncMock()
    client._client = reusable_client

    with patch("karakeep_client.karakeep.asyncio.get_running_loop", side_effect=RuntimeError):
        # Act
        client.close()

    # Assert
    reusable_client.aclose.assert_awaited_once()
    assert client._client is None


@pytest.mark.parametrize(
    "content_data,expected_url",
    [
        # link content -> returns url
        (
            {"type": "link", "url": "https://example.com/link"},
            "https://example.com/link",
        ),
        # text content with sourceUrl -> returns sourceUrl
        (
            {"type": "text", "text": "Some text", "sourceUrl": "https://example.com/source"},
            "https://example.com/source",
        ),
        # text content without sourceUrl -> returns None
        (
            {"type": "text", "text": "Some text without sourceUrl"},
            None,
        ),
        # asset content with sourceUrl -> returns sourceUrl
        (
            {"type": "asset", "assetType": "pdf", "assetId": "pdf123", "sourceUrl": "https://example.com/asset-source"},
            "https://example.com/asset-source",
        ),
        # asset content without sourceUrl -> returns None
        (
            {"type": "asset", "assetType": "image", "assetId": "img456"},
            None,
        ),
        # unknown content type -> returns None
        (
            {"type": "unknown"},
            None,
        ),
    ],
    ids=[
        "link",
        "text-with-source-url",
        "text-no-source-url",
        "asset-with-source-url",
        "asset-no-source-url",
        "unknown",
    ],
)
def test_extract_url_from_bookmark(content_data, expected_url):
    """Test that extract_url_from_bookmark returns the correct URL for each content type."""
    from karakeep_client.karakeep import extract_url_from_bookmark
    from karakeep_client.models import Bookmark

    bookmark_data = {
        "id": "test_bookmark",
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": None,
        "title": "Test",
        "archived": False,
        "favourited": False,
        "taggingStatus": "success",
        "summarizationStatus": None,
        "note": None,
        "summary": None,
        "tags": [],
        "content": content_data,
        "assets": [],
    }
    bookmark = Bookmark.model_validate(bookmark_data)
    assert extract_url_from_bookmark(bookmark) == expected_url


@pytest.mark.asyncio
async def test_get_bookmark_id_by_url_normalization(client: KarakeepClient):
    """Test that get_bookmark_id_by_url succeeds when URLs differ only by normalization."""
    search_response = {
        "bookmarks": [
            {
                "id": "bookmark1",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": None,
                "title": "Test",
                "archived": False,
                "favourited": False,
                "taggingStatus": "success",
                "summarizationStatus": None,
                "note": None,
                "summary": None,
                "tags": [],
                "content": {
                    "type": "link",
                    "url": "https://example.com/",  # Note: with trailing slash
                },
                "assets": [],
            }
        ],
        "nextCursor": None,
    }

    with patch.object(client, "search_bookmarks") as mock_search:
        from karakeep_client.models import PaginatedBookmarks

        mock_search.return_value = PaginatedBookmarks.model_validate(search_response)

        # Search for URL without trailing slash - should still find the bookmark
        result = await client.get_bookmark_id_by_url("https://example.com")  # No trailing slash
        assert result == "bookmark1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "search_url,stored_url",
    [
        # trailing slash normalization (existing case, repeated for completeness)
        ("https://example.com", "https://example.com/"),
        # query string preserved
        ("https://example.com/page?q=1", "https://example.com/page?q=1"),
        # fragment preserved
        ("https://example.com/page#top", "https://example.com/page#top"),
        # path with trailing slash
        ("https://example.com/path/", "https://example.com/path/"),
    ],
    ids=["trailing-slash", "query-string", "fragment", "path-trailing-slash"],
)
async def test_get_bookmark_id_by_url_normalization_shapes(
    client: KarakeepClient, search_url, stored_url
):
    """Test that get_bookmark_id_by_url matches across normalization-equivalent URLs."""
    search_response = {
        "bookmarks": [
            {
                "id": "found_bookmark",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": None,
                "title": "Test",
                "archived": False,
                "favourited": False,
                "taggingStatus": None,
                "summarizationStatus": None,
                "note": None,
                "summary": None,
                "tags": [],
                "content": {"type": "link", "url": stored_url},
                "assets": [],
            }
        ],
        "nextCursor": None,
    }

    with patch.object(client, "search_bookmarks") as mock_search:
        from karakeep_client.models import PaginatedBookmarks

        mock_search.return_value = PaginatedBookmarks.model_validate(search_response)
        result = await client.get_bookmark_id_by_url(search_url)

    assert result == "found_bookmark"


@pytest.mark.asyncio
async def test_get_bookmark_id_by_url_skips_malformed_source_url(client: KarakeepClient):
    """A text bookmark with a non-URL source_url is skipped; the matching link bookmark is still found."""
    search_response = {
        "bookmarks": [
            {
                "id": "text_bookmark",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": None,
                "title": "Text",
                "archived": False,
                "favourited": False,
                "taggingStatus": None,
                "summarizationStatus": None,
                "note": None,
                "summary": None,
                "tags": [],
                "content": {"type": "text", "text": "notes", "sourceUrl": "not a url at all"},
                "assets": [],
            },
            {
                "id": "link_bookmark",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": None,
                "title": "Link",
                "archived": False,
                "favourited": False,
                "taggingStatus": None,
                "summarizationStatus": None,
                "note": None,
                "summary": None,
                "tags": [],
                "content": {"type": "link", "url": "https://example.com/"},
                "assets": [],
            },
        ],
        "nextCursor": None,
    }

    with patch.object(client, "search_bookmarks") as mock_search:
        from karakeep_client.models import PaginatedBookmarks

        mock_search.return_value = PaginatedBookmarks.model_validate(search_response)
        result = await client.get_bookmark_id_by_url("https://example.com")

    assert result == "link_bookmark"


@pytest.mark.asyncio
async def test_get_bookmark_id_by_url_all_candidates_malformed(client: KarakeepClient):
    """Returns None when all search results have non-URL source URLs."""
    search_response = {
        "bookmarks": [
            {
                "id": "text_bookmark",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": None,
                "title": "Text",
                "archived": False,
                "favourited": False,
                "taggingStatus": None,
                "summarizationStatus": None,
                "note": None,
                "summary": None,
                "tags": [],
                "content": {"type": "text", "text": "notes", "sourceUrl": "not a url"},
                "assets": [],
            },
        ],
        "nextCursor": None,
    }

    with patch.object(client, "search_bookmarks") as mock_search:
        from karakeep_client.models import PaginatedBookmarks

        mock_search.return_value = PaginatedBookmarks.model_validate(search_response)
        result = await client.get_bookmark_id_by_url("https://example.com")

    assert result is None


@pytest.mark.asyncio
async def test_get_bookmark_id_by_url_not_found(client: KarakeepClient):
    """Test get_bookmark_id_by_url returns None when bookmark not found."""
    # Arrange
    empty_response = {"bookmarks": [], "nextCursor": None}

    with patch.object(client, "search_bookmarks") as mock_search:
        from karakeep_client.models import PaginatedBookmarks

        mock_search.return_value = PaginatedBookmarks.model_validate(empty_response)

        # Act
        result = await client.get_bookmark_id_by_url("https://notfound.com")

        # Assert
        assert result is None


@pytest.mark.asyncio
async def test_get_bookmark_id_by_url_empty_url_returns_none(client: KarakeepClient):
    """Test get_bookmark_id_by_url with empty URL returns None."""
    # Arrange & Act & Assert
    result = await client.get_bookmark_id_by_url("")
    assert result is None

    result = await client.get_bookmark_id_by_url("   ")
    assert result is None


@pytest.mark.parametrize(
    "bookmark_type,required_params,expected_error",
    [
        ("link", {}, "Argument 'url' is required"),
        ("text", {}, "Argument 'text' is required"),
        ("asset", {"asset_type": "pdf"}, "Argument 'asset_id' is required"),
        ("asset", {"asset_id": "123"}, "Argument 'asset_type'"),
    ],
)
@pytest.mark.asyncio
async def test_create_bookmark_validation_errors(
    client: KarakeepClient, bookmark_type, required_params, expected_error
):
    """Test create_bookmark validation for different bookmark types."""
    # Arrange & Act & Assert
    with pytest.raises(ValueError, match=expected_error):
        await client.create_bookmark(bookmark_type=bookmark_type, **required_params)


@pytest.mark.parametrize(
    "limit,should_raise",
    [
        (99, False),
        (100, False),
        (101, True),
        (1000, True),
    ],
)
@pytest.mark.asyncio
async def test_limit_validation(client: KarakeepClient, sample_paginated_response, limit, should_raise):
    """Test limit parameter validation for paginated endpoints."""
    if should_raise:
        with pytest.raises(ValueError, match="Maximum limit is 100"):
            await client.get_bookmarks_paged(limit=limit)
        with pytest.raises(ValueError, match="Maximum limit is 100"):
            await client.search_bookmarks("query", limit=limit)
    else:
        with patch.object(client, "_call", return_value=sample_paginated_response):
            result1 = await client.get_bookmarks_paged(limit=limit)
            result2 = await client.search_bookmarks("query", limit=limit)
            assert len(result1.bookmarks) == 1
            assert len(result2.bookmarks) == 1


# Test client initialization
class TestKarakeepClientInit:
    """Test KarakeepClient initialization and configuration."""

    def test_client_init_with_params(self):
        """Test client initialization with explicit parameters."""
        # Arrange & Act
        client = KarakeepClient(api_key="test_key", base_url="https://test.example.com", timeout=60.0, verbose=True)

        # Assert
        assert client.api_key == "test_key"
        assert client.base_url == "https://test.example.com"
        assert client.timeout == 60.0
        assert client.verbose is True
        assert "Bearer test_key" in client._default_headers["Authorization"]

    def test_client_init_missing_api_key(self):
        """Test client initialization fails without API key."""
        # Ensure environment variables are not set
        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValueError, match="API key must be provided"):
            KarakeepClient(base_url="https://test.example.com")

    def test_client_init_missing_base_url(self):
        """Test client initialization fails without base URL."""
        # Ensure environment variables are not set
        with patch.dict("os.environ", {}, clear=True), pytest.raises(ValueError, match="Base URL must be provided"):
            KarakeepClient(api_key="test_key")

    @patch.dict("os.environ", {"KARAKEEP_API_KEY": "env_key", "KARAKEEP_BASE_URL": "https://env.example.com"})
    def test_client_init_from_environment(self):
        """Test client initialization from environment variables."""
        # Arrange & Act
        client = KarakeepClient()

        # Assert
        assert client.api_key == "env_key"
        assert client.base_url == "https://env.example.com"


# Test URL validation function
class TestURLValidation:
    """Test URL validation functionality."""

    @pytest.mark.parametrize(
        "input_url,expected_output",
        [
            # trailing slash added by HttpUrl normalization
            ("https://example.com", "https://example.com/"),
            ("http://example.com", "http://example.com/"),
            # path preserved
            ("https://sub.example.com/path", "https://sub.example.com/path"),
            # port, query, fragment preserved
            (
                "https://example.com:8080/path?query=value#fragment",
                "https://example.com:8080/path?query=value#fragment",
            ),
        ],
    )
    def test_validate_url_valid_urls(self, input_url, expected_output):
        """Test validate_url returns the expected normalized form."""
        from karakeep_client.karakeep import validate_url

        result = validate_url(input_url)
        assert result == expected_output

    @pytest.mark.parametrize(
        "input_url,expected_output",
        [
            # default port stripped by HttpUrl normalization
            ("https://example.com:443/path", "https://example.com/path"),
            # non-default port preserved
            ("https://example.com:9090/path", "https://example.com:9090/path"),
            # percent-encoded path preserved as-is
            ("https://example.com/path%20with%20spaces", "https://example.com/path%20with%20spaces"),
            # unicode domain (IDN / punycode) preserved
            ("https://xn--nxasmq6b.example.com/path", "https://xn--nxasmq6b.example.com/path"),
            # mixed-case scheme and host normalized to lowercase
            ("HTTPS://EXAMPLE.COM/path", "https://example.com/path"),
            # deeply nested path with query and fragment preserved
            ("https://example.com/a/b/c/d?x=1&y=2#section", "https://example.com/a/b/c/d?x=1&y=2#section"),
            # userinfo preserved
            ("https://user:pass@example.com/path", "https://user:pass@example.com/path"),
        ],
    )
    def test_validate_url_normalization_boundaries(self, input_url, expected_output):
        """Test validate_url on URL shapes that stress normalization layers.

        This test locks in behavior — if a URL is rejected, change the
        expectation to pytest.raises(ValueError) rather than deleting the case.
        """
        from karakeep_client.karakeep import validate_url

        result = validate_url(input_url)
        assert result == expected_output

    @pytest.mark.parametrize(
        "url,expected",
        [
            # Passes basic regex but has no valid TLD — rejected at regex layer
            ("http://localhost/path", ValueError("URL does not match expected url regex")),
            # Valid-looking but scheme-only after normalization — rejected at regex layer
            ("http://.", ValueError("URL does not match expected url regex")),
            # Very long URL: passes all layers, returned unchanged
            ("https://example.com/" + "a" * 2048, "https://example.com/" + "a" * 2048),
            # Empty port stripped by HttpUrl normalization
            ("https://example.com:/path", "https://example.com/path"),
            # Double slash in path preserved as-is
            ("https://example.com//path", "https://example.com//path"),
        ],
    )
    def test_validate_url_multi_layer_seams(self, url, expected):
        """Test URLs that may pass one validation layer but fail another."""
        from karakeep_client.karakeep import validate_url

        if isinstance(expected, ValueError):
            with pytest.raises(ValueError, match=str(expected)):
                validate_url(url)
        else:
            result = validate_url(url)
            assert result == expected

    @pytest.mark.parametrize(
        "invalid_url,expected_error",
        [
            ("", "URL cannot be empty"),
            ("   ", "URL cannot be empty"),
            ("not-a-url", "URL does not match expected url regex"),
            ("ftp://", "URL does not match expected url regex"),
            ("http://", "URL does not match expected url regex"),
        ],
    )
    def test_validate_url_invalid_urls(self, invalid_url, expected_error):
        """Test validate_url with invalid URLs."""
        from karakeep_client.karakeep import validate_url

        # Act & Assert
        with pytest.raises(ValueError, match=expected_error):
            validate_url(invalid_url)


class TestValidateUrlProperties:
    """Property-based tests for validate_url using Hypothesis."""

    @given(st.text())
    @settings(max_examples=500)
    def test_no_unexpected_exceptions(self, url: str) -> None:
        """validate_url only ever raises ValueError or returns a non-empty str."""
        from karakeep_client.karakeep import validate_url

        try:
            result = validate_url(url)
            assert isinstance(result, str)
            assert result
        except ValueError:
            pass

    @given(
        st.from_regex(
            r"https://[a-z]{3,10}\.[a-z]{2,4}(/[a-z0-9]{0,8})?",
            fullmatch=True,
        )
    )
    def test_idempotent_on_valid_inputs(self, url: str) -> None:
        """validate_url(validate_url(url)) == validate_url(url) for inputs that pass."""
        from karakeep_client.karakeep import validate_url

        try:
            first = validate_url(url)
        except ValueError:
            assume(False)  # discard — only test idempotency on inputs that actually pass
        second = validate_url(first)
        assert first == second

    @given(
        st.builds(
            lambda scheme, host, tld, port, path, query, fragment: (
                f"{scheme}://{host}.{tld}"
                + (f":{port}" if port else "")
                + (f"/{path}" if path else "")
                + (f"?{query}" if query else "")
                + (f"#{fragment}" if fragment else "")
            ),
            scheme=st.sampled_from(["http", "https"]),
            host=st.from_regex(r"[a-z]{3,12}", fullmatch=True),
            tld=st.sampled_from(["com", "org", "net", "io", "dev", "co.uk"]),
            port=st.one_of(st.none(), st.integers(min_value=80, max_value=9999).map(str)),
            path=st.one_of(
                st.none(),
                st.from_regex(r"[a-z0-9/]{1,30}", fullmatch=True),
            ),
            query=st.one_of(
                st.none(),
                st.from_regex(r"[a-z]+=[\w]{1,10}", fullmatch=True),
            ),
            fragment=st.one_of(
                st.none(),
                st.from_regex(r"[a-z]{1,10}", fullmatch=True),
            ),
        )
    )
    @settings(max_examples=300)
    def test_idempotent_on_diverse_urls(self, url: str) -> None:
        """Idempotency property over URLs with ports, paths, queries, and fragments."""
        from karakeep_client.karakeep import validate_url

        try:
            first = validate_url(url)
        except ValueError:
            assume(False)
        second = validate_url(first)
        assert first == second


@pytest.mark.asyncio
async def test_upload_new_asset_returns_asset(client: KarakeepClient, sample_asset_data):
    """Test that upload_new_asset returns Asset object."""
    with (
        patch.object(client, "_call", return_value=sample_asset_data),
        patch("os.path.isfile", return_value=True),
        patch("mimetypes.guess_type", return_value=("application/pdf", None)),
        patch("builtins.open", mock_open(read_data=b"fake file content")),
    ):
        result = await client.upload_new_asset("/fake/path/test.pdf")

        # Should return an Asset object
        from karakeep_client.models import Asset

        assert isinstance(result, Asset)
        assert result.asset_id == "asset123"
        assert result.file_name == "test.pdf"


@pytest.mark.asyncio
async def test_upload_new_asset_file_not_found(client: KarakeepClient):
    """Test upload_new_asset with non-existent file."""
    # Arrange & Act & Assert
    with patch("os.path.isfile", return_value=False), pytest.raises(FileNotFoundError):
        await client.upload_new_asset("/nonexistent/file.pdf")


@pytest.mark.asyncio
async def test_get_asset_returns_bytes(client: KarakeepClient):
    """Test get_asset returns bytes."""
    # Arrange
    asset_id = "asset123"
    fake_content = b"fake asset content"

    with patch.object(client, "_call", return_value=fake_content):
        # Act
        result = await client.get_asset(asset_id)

    # Assert
    assert result == fake_content
    assert isinstance(result, bytes)


@pytest.mark.asyncio
async def test_attach_bookmark_asset_success(client: KarakeepClient):
    """Test attach_bookmark_asset success."""
    # Arrange
    bookmark_id = "bookmark1"
    asset_id = "asset123"
    asset_type = "screenshot"
    mock_response = {"id": asset_id, "assetType": asset_type}

    with patch.object(client, "_call", return_value=mock_response) as mock_call:
        # Act
        result = await client.attach_bookmark_asset(bookmark_id, asset_id, asset_type)

    # Assert
    from karakeep_client.models import BookmarkAsset

    assert isinstance(result, BookmarkAsset)
    assert result.id == asset_id
    assert result.asset_type == asset_type
    mock_call.assert_called_once_with(
        "POST", f"bookmarks/{bookmark_id}/assets", data={"id": asset_id, "assetType": asset_type}
    )


@pytest.mark.asyncio
async def test_authentication_error(client: KarakeepClient):
    """Test that AuthenticationError is raised properly."""
    # Arrange & Act & Assert
    with (
        patch.object(client, "_call", side_effect=AuthenticationError("Authentication failed")),
        pytest.raises(AuthenticationError),
    ):
        await client.get_bookmarks_paged()


@pytest.mark.asyncio
async def test_api_error(client: KarakeepClient):
    # Arrange & Act & Assert
    with patch.object(client, "_call", side_effect=APIError("Server Error")), pytest.raises(APIError):
        await client.get_bookmarks_paged()


@pytest.mark.asyncio
async def test_endpoints_non_regression(client: KarakeepClient):
    """Test that existing endpoints (bookmarks/assets) behave unchanged."""
    # Test get_bookmarks_paged returns PaginatedBookmarks
    mock_paginated_response = {
        "bookmarks": [
            {
                "id": "bookmark1",
                "createdAt": "2023-01-01T00:00:00Z",
                "modifiedAt": None,
                "title": "Test",
                "archived": False,
                "favourited": False,
                "taggingStatus": "success",
                "summarizationStatus": None,
                "note": None,
                "summary": None,
                "tags": [],
                "content": {"type": "link", "url": "https://example.com"},
                "assets": [],
            }
        ],
        "nextCursor": "next",
    }

    with patch.object(client, "_call", return_value=mock_paginated_response):
        result = await client.get_bookmarks_paged()

        from karakeep_client.models import PaginatedBookmarks

        assert isinstance(result, PaginatedBookmarks)
        assert len(result.bookmarks) == 1
        assert result.next_cursor == "next"

    # Test get_bookmark returns Bookmark
    mock_bookmark_response = {
        "id": "bookmark1",
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": None,
        "title": "Test",
        "archived": False,
        "favourited": False,
        "taggingStatus": "success",
        "summarizationStatus": None,
        "note": None,
        "summary": None,
        "tags": [],
        "content": {"type": "link", "url": "https://example.com"},
        "assets": [],
    }

    with patch.object(client, "_call", return_value=mock_bookmark_response):
        result = await client.get_bookmark("bookmark1")

        from karakeep_client.models import Bookmark

        assert isinstance(result, Bookmark)
        assert result.id == "bookmark1"
