from unittest.mock import AsyncMock, mock_open, patch

import pytest

from karakeep_client.karakeep import APIError, AuthenticationError, KarakeepClient


@pytest.fixture
def client():
    return KarakeepClient(api_key="test_key", base_url="https://test.karakeep.app")


@pytest.mark.asyncio
async def test_get_bookmarks_paged_success(client: KarakeepClient):
    # Arrange
    mock_response = {
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

    with patch.object(client, "_call", return_value=mock_response):
        # Act
        result = await client.get_bookmarks_paged(limit=1)

    # Assert
    assert len(result.bookmarks) == 1
    assert result.bookmarks[0].id == "bookmark1"
    assert result.next_cursor == "next_page_cursor"


@pytest.mark.asyncio
async def test_get_bookmark_success(client: KarakeepClient):
    # Arrange
    bookmark_id = "bookmark1"
    mock_response = {
        "id": bookmark_id,
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": "2023-01-01T00:00:00Z",
        "title": "Test Bookmark",
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

    with patch.object(client, "_call", return_value=mock_response):
        # Act
        result = await client.get_bookmark(bookmark_id)

    # Assert
    assert result.id == bookmark_id
    assert result.title == "Test Bookmark"


@pytest.mark.asyncio
async def test_api_error(client: KarakeepClient):
    # Arrange & Act & Assert
    with patch.object(client, "_call", side_effect=APIError("Server Error")), pytest.raises(APIError):
        await client.get_bookmarks_paged()


@pytest.mark.asyncio
async def test_authentication_error(client: KarakeepClient):
    # Arrange & Act & Assert
    with (
        patch.object(client, "_call", side_effect=AuthenticationError("Unauthorized")),
        pytest.raises(AuthenticationError),
    ):
        await client.get_bookmarks_paged()


def test_extract_url_from_bookmark():
    """Test that _extract_url_from_bookmark returns appropriate URLs."""
    from karakeep_client.karakeep import _extract_url_from_bookmark
    from karakeep_client.models import Bookmark, ContentTypeLink, ContentTypeText

    # Test with link content
    link_bookmark_data = {
        "id": "link_bookmark",
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
        "content": {"type": "link", "url": "https://example.com/link"},
        "assets": [],
    }
    link_bookmark = Bookmark.model_validate(link_bookmark_data)
    assert _extract_url_from_bookmark(link_bookmark) == "https://example.com/link"

    # Test with text content having sourceUrl
    text_bookmark_data = {
        "id": "text_bookmark",
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
        "content": {"type": "text", "text": "Some text", "sourceUrl": "https://example.com/source"},
        "assets": [],
    }
    text_bookmark = Bookmark.model_validate(text_bookmark_data)
    assert _extract_url_from_bookmark(text_bookmark) == "https://example.com/source"

    # Test with no extractable URL
    no_url_bookmark_data = {
        "id": "no_url_bookmark",
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
        "content": {"type": "text", "text": "Some text without sourceUrl"},
        "assets": [],
    }
    no_url_bookmark = Bookmark.model_validate(no_url_bookmark_data)
    assert _extract_url_from_bookmark(no_url_bookmark) is None


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
async def test_upload_new_asset_returns_asset(client: KarakeepClient):
    """Test that upload_new_asset returns Asset object."""
    mock_asset_response = {
        "assetId": "asset123",
        "fileName": "test.pdf",
        "contentType": "application/pdf",
        "size": 1024,
    }

    with (
        patch.object(client, "_call", return_value=mock_asset_response),
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
