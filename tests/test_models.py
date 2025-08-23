"""Tests for the Karakeep client models to verify alignment with OpenAPI spec."""

from karakeep_client.models import (
    Bookmark,
    BookmarkAsset,
    ContentTypeLink,
    ContentTypeText,
    TagShort,
)


def test_bookmark_with_null_tagging_status():
    """Test that Bookmark validates when taggingStatus=None."""
    bookmark_data = {
        "id": "test_id",
        "createdAt": "2023-01-01T00:00:00Z",
        "modifiedAt": None,
        "title": "Test",
        "archived": False,
        "favourited": False,
        "taggingStatus": None,  # This should be allowed
        "summarizationStatus": None,
        "note": None,
        "summary": None,
        "tags": [],
        "content": {"type": "link", "url": "https://example.com"},
        "assets": [],
    }

    bookmark = Bookmark.model_validate(bookmark_data)
    assert bookmark.tagging_status is None

    # Test round-trip with aliases
    dumped = bookmark.model_dump(by_alias=True)
    assert dumped["taggingStatus"] is None


def test_content_type_link_accepts_content_asset_id():
    """Test that ContentTypeLink accepts contentAssetId and round-trips with model_dump(by_alias=True)."""
    link_data = {
        "type": "link",
        "url": "https://example.com",
        "title": "Test Title",
        "contentAssetId": "test_asset_id_123"
    }

    link = ContentTypeLink.model_validate(link_data)
    assert link.content_asset_id == "test_asset_id_123"

    # Test round-trip with aliases
    dumped = link.model_dump(by_alias=True)
    assert dumped["contentAssetId"] == "test_asset_id_123"


def test_content_type_text_source_url():
    """Test that ContentTypeText has sourceUrl field."""
    text_data = {
        "type": "text",
        "text": "Some text content",
        "sourceUrl": "https://example.com/source"
    }

    text = ContentTypeText.model_validate(text_data)
    assert text.source_url == "https://example.com/source"

    # Test round-trip with aliases
    dumped = text.model_dump(by_alias=True)
    assert dumped["sourceUrl"] == "https://example.com/source"


def test_bookmark_asset_accepts_link_html_content():
    """Test that BookmarkAsset accepts assetType='linkHtmlContent'."""
    asset_data = {
        "id": "test_asset_id",
        "assetType": "linkHtmlContent"
    }

    asset = BookmarkAsset.model_validate(asset_data)
    assert asset.asset_type == "linkHtmlContent"

    # Test round-trip with aliases
    dumped = asset.model_dump(by_alias=True)
    assert dumped["assetType"] == "linkHtmlContent"


def test_content_type_link_all_aliases():
    """Test that all ContentTypeLink fields have correct aliases."""
    link_data = {
        "type": "link",
        "url": "https://example.com",
        "title": "Test",
        "description": "Test description",
        "imageUrl": "https://example.com/image.jpg",
        "imageAssetId": "img_asset_123",
        "screenshotAssetId": "screenshot_123",
        "fullPageArchiveAssetId": "archive_123",
        "precrawledArchiveAssetId": "precrawl_123",
        "videoAssetId": "video_123",
        "favicon": "https://example.com/favicon.ico",
        "htmlContent": "<html>content</html>",
        "contentAssetId": "content_123",
        "crawledAt": "2023-01-01T00:00:00Z",
        "author": "Test Author",
        "publisher": "Test Publisher",
        "datePublished": "2023-01-01T00:00:00Z",
        "dateModified": "2023-01-01T00:00:00Z"
    }

    link = ContentTypeLink.model_validate(link_data)

    # Test that all fields are accessible via snake_case
    assert link.image_url == "https://example.com/image.jpg"
    assert link.image_asset_id == "img_asset_123"
    assert link.screenshot_asset_id == "screenshot_123"
    assert link.full_page_archive_asset_id == "archive_123"
    assert link.precrawled_archive_asset_id == "precrawl_123"
    assert link.video_asset_id == "video_123"
    assert link.html_content == "<html>content</html>"
    assert link.content_asset_id == "content_123"
    assert link.crawled_at == "2023-01-01T00:00:00Z"
    assert link.date_published == "2023-01-01T00:00:00Z"
    assert link.date_modified == "2023-01-01T00:00:00Z"

    # Test round-trip with aliases (should be camelCase)
    dumped = link.model_dump(by_alias=True)
    assert dumped["imageUrl"] == "https://example.com/image.jpg"
    assert dumped["imageAssetId"] == "img_asset_123"
    assert dumped["screenshotAssetId"] == "screenshot_123"
    assert dumped["fullPageArchiveAssetId"] == "archive_123"
    assert dumped["precrawledArchiveAssetId"] == "precrawl_123"
    assert dumped["videoAssetId"] == "video_123"
    assert dumped["htmlContent"] == "<html>content</html>"
    assert dumped["contentAssetId"] == "content_123"
    assert dumped["crawledAt"] == "2023-01-01T00:00:00Z"
    assert dumped["datePublished"] == "2023-01-01T00:00:00Z"
    assert dumped["dateModified"] == "2023-01-01T00:00:00Z"


def test_bookmark_with_text_content():
    """Test Bookmark with text content type."""
    bookmark_data = {
        "id": "test_id",
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
            "type": "text",
            "text": "Some text content",
            "sourceUrl": "https://example.com/source"
        },
        "assets": [],
    }

    bookmark = Bookmark.model_validate(bookmark_data)
    assert bookmark.content.type == "text"
    assert bookmark.content.text == "Some text content"
    assert bookmark.content.source_url == "https://example.com/source"
