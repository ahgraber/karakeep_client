"""Tests for the Karakeep client models to verify alignment with OpenAPI spec."""

from pydantic import ValidationError
import pytest

from karakeep_client.models import (
    Bookmark,
    BookmarkAsset,
    BookmarkList,
    ContentTypeAsset,
    ContentTypeLink,
    ContentTypeText,
    ContentTypeUnknown,
    Highlight,
    StatusTypes,
    Tag,
    TagShort,
)


class TestStatusTypes:
    """Test StatusTypes enum validation."""

    def test_valid_status_values(self):
        """Test that StatusTypes accepts valid enum values."""
        assert StatusTypes.success == "success"
        assert StatusTypes.failure == "failure"
        assert StatusTypes.pending == "pending"

    def test_status_types_string_comparison(self):
        """Test that StatusTypes can be compared with strings."""
        assert StatusTypes.success == "success"
        assert StatusTypes.failure != "invalid"


class TestTagShort:
    """Test TagShort model validation."""

    def test_valid_attached_by_values(self):
        """Test TagShort with valid attachedBy values."""
        # Test with 'ai'
        tag_data = {"id": "tag1", "name": "Python", "attachedBy": "ai"}
        tag = TagShort.model_validate(tag_data)
        assert tag.attached_by == "ai"

        # Test with 'human'
        tag_data = {"id": "tag2", "name": "JavaScript", "attachedBy": "human"}
        tag = TagShort.model_validate(tag_data)
        assert tag.attached_by == "human"

    def test_invalid_attached_by_raises_error(self):
        """Test TagShort with invalid attachedBy value raises ValidationError."""
        tag_data = {"id": "tag1", "name": "Python", "attachedBy": "robot"}
        with pytest.raises(ValidationError) as exc_info:
            TagShort.model_validate(tag_data)
        assert "Input should be 'ai' or 'human'" in str(exc_info.value)

    def test_alias_roundtrip(self):
        """Test TagShort alias consistency."""
        tag_data = {"id": "tag1", "name": "Python", "attachedBy": "ai"}
        tag = TagShort.model_validate(tag_data)
        dumped = tag.model_dump(by_alias=True)
        assert dumped["attachedBy"] == "ai"

    def test_missing_required_fields_raises_error(self):
        """Test TagShort with missing required fields raises ValidationError."""
        # Missing 'attachedBy' field
        tag_data = {"id": "tag1", "name": "Python"}
        with pytest.raises(ValidationError) as exc_info:
            TagShort.model_validate(tag_data)
        assert "Field required" in str(exc_info.value)


class TestTag:
    """Test Tag model validation."""

    def test_with_nested_num_bookmarks_by_attached_type(self):
        """Test Tag model with nested NumBookmarksByAttachedType."""
        tag_data = {
            "id": "tag123",
            "name": "Python",
            "numBookmarks": 42.0,
            "numBookmarksByAttachedType": {"ai": 25.0, "human": 17.0},
        }
        tag = Tag.model_validate(tag_data)
        assert tag.num_bookmarks == 42.0
        assert tag.num_bookmarks_by_attached_type.ai == 25.0
        assert tag.num_bookmarks_by_attached_type.human == 17.0

    def test_with_partial_num_bookmarks_by_attached_type(self):
        """Test Tag with partial NumBookmarksByAttachedType data."""
        tag_data = {
            "id": "tag123",
            "name": "Python",
            "numBookmarks": 42.0,
            "numBookmarksByAttachedType": {"ai": 25.0, "human": None},  # None should be valid
        }
        tag = Tag.model_validate(tag_data)
        assert tag.num_bookmarks_by_attached_type.ai == 25.0
        assert tag.num_bookmarks_by_attached_type.human is None


class TestContentTypeLink:
    """Test ContentTypeLink model validation."""

    def test_accepts_content_asset_id(self):
        """Test that ContentTypeLink accepts contentAssetId and round-trips with model_dump(by_alias=True)."""
        link_data = {
            "type": "link",
            "url": "https://example.com",
            "title": "Test Title",
            "contentAssetId": "test_asset_id_123",
            "pdfAssetId": "pdf_asset_456",
            "crawlStatus": "success",
        }

        link = ContentTypeLink.model_validate(link_data)
        assert link.content_asset_id == "test_asset_id_123"
        assert link.pdf_asset_id == "pdf_asset_456"
        assert link.crawl_status == "success"

        # Test round-trip with aliases
        dumped = link.model_dump(by_alias=True)
        assert dumped["contentAssetId"] == "test_asset_id_123"
        assert dumped["pdfAssetId"] == "pdf_asset_456"
        assert dumped["crawlStatus"] == "success"

    def test_all_aliases(self):
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
            "pdfAssetId": "pdf_456",
            "crawlStatus": "pending",
            "crawledAt": "2023-01-01T00:00:00Z",
            "author": "Test Author",
            "publisher": "Test Publisher",
            "datePublished": "2023-01-01T00:00:00Z",
            "dateModified": "2023-01-01T00:00:00Z",
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
        assert link.pdf_asset_id == "pdf_456"
        assert link.crawl_status == "pending"
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
        assert dumped["pdfAssetId"] == "pdf_456"
        assert dumped["crawlStatus"] == "pending"
        assert dumped["crawledAt"] == "2023-01-01T00:00:00Z"
        assert dumped["datePublished"] == "2023-01-01T00:00:00Z"
        assert dumped["dateModified"] == "2023-01-01T00:00:00Z"

    def test_missing_url_raises_error(self):
        """Test ContentTypeLink with missing url raises ValidationError."""
        link_data = {"type": "link", "title": "Test"}  # Missing required 'url'
        with pytest.raises(ValidationError) as exc_info:
            ContentTypeLink.model_validate(link_data)
        assert "Field required" in str(exc_info.value)


class TestContentTypeText:
    """Test ContentTypeText model validation."""

    def test_source_url(self):
        """Test that ContentTypeText has sourceUrl field."""
        text_data = {"type": "text", "text": "Some text content", "sourceUrl": "https://example.com/source"}

        text = ContentTypeText.model_validate(text_data)
        assert text.source_url == "https://example.com/source"

        # Test round-trip with aliases
        dumped = text.model_dump(by_alias=True)
        assert dumped["sourceUrl"] == "https://example.com/source"

    def test_with_empty_text(self):
        """Test ContentTypeText with empty text string."""
        text_data = {"type": "text", "text": ""}
        content = ContentTypeText.model_validate(text_data)
        # Empty string is actually valid for text field - this tests current behavior
        assert content.text == ""


class TestContentTypeAsset:
    """Test ContentTypeAsset model validation."""

    def test_valid_asset_types(self):
        """Test ContentTypeAsset with valid asset types."""
        # Test with image
        asset_data = {"type": "asset", "assetType": "image", "assetId": "img123"}
        asset = ContentTypeAsset.model_validate(asset_data)
        assert asset.asset_type == "image"
        assert asset.asset_id == "img123"

        # Test with pdf
        asset_data = {"type": "asset", "assetType": "pdf", "assetId": "pdf456"}
        asset = ContentTypeAsset.model_validate(asset_data)
        assert asset.asset_type == "pdf"

    def test_invalid_asset_type_raises_error(self):
        """Test ContentTypeAsset with invalid asset type raises ValidationError."""
        asset_data = {
            "type": "asset",
            "assetType": "video",  # Invalid - only 'image' and 'pdf' allowed
            "assetId": "vid123",
        }
        with pytest.raises(ValidationError) as exc_info:
            ContentTypeAsset.model_validate(asset_data)
        assert "Input should be 'image' or 'pdf'" in str(exc_info.value)

    def test_alias_roundtrip(self):
        """Test ContentTypeAsset alias consistency."""
        asset_data = {
            "type": "asset",
            "assetType": "image",
            "assetId": "img123",
            "fileName": "test.jpg",
            "sourceUrl": "https://example.com/source",
        }
        asset = ContentTypeAsset.model_validate(asset_data)
        dumped = asset.model_dump(by_alias=True)
        assert dumped["assetType"] == "image"
        assert dumped["assetId"] == "img123"
        assert dumped["fileName"] == "test.jpg"
        assert dumped["sourceUrl"] == "https://example.com/source"


class TestContentTypeUnknown:
    """Test ContentTypeUnknown model validation."""

    def test_minimal_content(self):
        """Test ContentTypeUnknown with minimal data."""
        content = ContentTypeUnknown.model_validate({"type": "unknown"})
        assert content.type == "unknown"


class TestBookmarkAsset:
    """Test BookmarkAsset model validation."""

    @pytest.mark.parametrize(
        "asset_type",
        [
            "linkHtmlContent",
            "screenshot",
            "pdf",
            "assetScreenshot",
            "bannerImage",
            "fullPageArchive",
            "video",
            "bookmarkAsset",
            "precrawledArchive",
            "userUploaded",
            "avatar",
            "unknown",
        ],
    )
    def test_valid_asset_types(self, asset_type):
        """Test BookmarkAsset with all valid asset types."""
        asset_data = {"id": "asset123", "assetType": asset_type}
        asset = BookmarkAsset.model_validate(asset_data)
        assert asset.asset_type == asset_type

    def test_invalid_asset_type_raises_error(self):
        """Test BookmarkAsset with invalid asset type raises ValidationError."""
        asset_data = {"id": "asset123", "assetType": "invalidType"}
        with pytest.raises(ValidationError) as exc_info:
            BookmarkAsset.model_validate(asset_data)
        error_msg = str(exc_info.value)
        assert "Input should be" in error_msg

    def test_accepts_link_html_content(self):
        """Test that BookmarkAsset accepts assetType='linkHtmlContent'."""
        asset_data = {"id": "test_asset_id", "assetType": "linkHtmlContent"}

        asset = BookmarkAsset.model_validate(asset_data)
        assert asset.asset_type == "linkHtmlContent"

        # Test optional file name
        with_file_name = BookmarkAsset.model_validate({"id": "test_asset_id", "assetType": "pdf", "fileName": "doc.pdf"})
        assert with_file_name.file_name == "doc.pdf"

        # Test round-trip with aliases
        dumped = asset.model_dump(by_alias=True)
        assert dumped["assetType"] == "linkHtmlContent"


class TestBookmark:
    """Test Bookmark model validation."""

    def test_with_null_tagging_status(self):
        """Test that Bookmark validates when taggingStatus=None."""
        bookmark_data = {
            "id": "test_id",
            "createdAt": "2023-01-01T00:00:00Z",
            "modifiedAt": None,
            "title": "Test",
            "archived": False,
            "favourited": False,
            "source": "web",
            "userId": "user-123",
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

    def test_with_text_content(self):
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
            "content": {"type": "text", "text": "Some text content", "sourceUrl": "https://example.com/source"},
            "assets": [],
        }

        bookmark = Bookmark.model_validate(bookmark_data)
        assert bookmark.content.type == "text"
        assert bookmark.content.text == "Some text content"
        assert bookmark.content.source_url == "https://example.com/source"

    def test_with_asset_content(self):
        """Test Bookmark with ContentTypeAsset."""
        bookmark_data = {
            "id": "test_id",
            "createdAt": "2023-01-01T00:00:00Z",
            "modifiedAt": None,
            "title": "Test Asset",
            "archived": False,
            "favourited": False,
            "taggingStatus": "success",
            "summarizationStatus": None,
            "note": None,
            "summary": None,
            "tags": [],
            "content": {"type": "asset", "assetType": "pdf", "assetId": "pdf123"},
            "assets": [],
        }

        bookmark = Bookmark.model_validate(bookmark_data)
        assert bookmark.content.type == "asset"
        assert bookmark.content.asset_type == "pdf"
        assert bookmark.content.asset_id == "pdf123"

    def test_with_unknown_content(self):
        """Test Bookmark with ContentTypeUnknown."""
        bookmark_data = {
            "id": "test_id",
            "createdAt": "2023-01-01T00:00:00Z",
            "modifiedAt": None,
            "title": "Test Unknown",
            "archived": False,
            "favourited": False,
            "taggingStatus": "success",
            "summarizationStatus": None,
            "note": None,
            "summary": None,
            "tags": [],
            "content": {"type": "unknown"},
            "assets": [],
        }

        bookmark = Bookmark.model_validate(bookmark_data)
        assert bookmark.content.type == "unknown"

    def test_with_empty_tags_list(self):
        """Test Bookmark with empty tags list."""
        bookmark_data = {
            "id": "test_id",
            "createdAt": "2023-01-01T00:00:00Z",
            "modifiedAt": None,
            "archived": False,
            "favourited": False,
            "taggingStatus": None,
            "tags": [],  # Empty list should be valid
            "content": {"type": "link", "url": "https://example.com"},
            "assets": [],
        }
        bookmark = Bookmark.model_validate(bookmark_data)
        assert bookmark.tags == []

    def test_with_multiple_tags(self):
        """Test Bookmark with multiple tags."""
        bookmark_data = {
            "id": "test_id",
            "createdAt": "2023-01-01T00:00:00Z",
            "modifiedAt": None,
            "archived": False,
            "favourited": False,
            "taggingStatus": "success",
            "tags": [
                {"id": "tag1", "name": "Python", "attachedBy": "ai"},
                {"id": "tag2", "name": "Tutorial", "attachedBy": "human"},
            ],
            "content": {"type": "link", "url": "https://example.com"},
            "assets": [],
        }
        bookmark = Bookmark.model_validate(bookmark_data)
        assert len(bookmark.tags) == 2
        assert bookmark.tags[0].name == "Python"
        assert bookmark.tags[1].attached_by == "human"

    def test_missing_required_fields_raises_error(self):
        """Test Bookmark with missing required fields raises ValidationError."""
        # Missing 'id' field
        bookmark_data = {
            "createdAt": "2023-01-01T00:00:00Z",
            "archived": False,
            "favourited": False,
            "tags": [],
            "content": {"type": "unknown"},
            "assets": [],
        }
        with pytest.raises(ValidationError) as exc_info:
            Bookmark.model_validate(bookmark_data)
        assert "Field required" in str(exc_info.value)

    def test_comprehensive_aliases(self):
        """Test comprehensive alias round-trip for Bookmark model."""
        bookmark_data = {
            "id": "bm123",
            "createdAt": "2023-01-01T00:00:00Z",
            "modifiedAt": "2023-01-02T00:00:00Z",
            "title": "Test Bookmark",
            "archived": False,
            "favourited": True,
            "source": "api",
            "userId": "user-123",
            "taggingStatus": "success",
            "summarizationStatus": "pending",
            "note": "Test note",
            "summary": "Test summary",
            "tags": [{"id": "tag1", "name": "Python", "attachedBy": "ai"}],
            "content": {"type": "link", "url": "https://example.com"},
            "assets": [{"id": "asset1", "assetType": "screenshot"}],
        }

        bookmark = Bookmark.model_validate(bookmark_data)
        dumped = bookmark.model_dump(by_alias=True)

        # Verify all camelCase aliases are preserved
        assert dumped["createdAt"] == "2023-01-01T00:00:00Z"
        assert dumped["modifiedAt"] == "2023-01-02T00:00:00Z"
        assert dumped["source"] == "api"
        assert dumped["userId"] == "user-123"
        assert dumped["taggingStatus"] == "success"
        assert dumped["summarizationStatus"] == "pending"
        assert dumped["tags"][0]["attachedBy"] == "ai"
        assert dumped["assets"][0]["assetType"] == "screenshot"


class TestHighlight:
    """Test Highlight model validation."""

    @pytest.mark.parametrize("color", ["yellow", "red", "green", "blue"])
    def test_valid_colors(self, color):
        """Test Highlight with all valid color values."""
        highlight_data = {
            "bookmarkId": "bm123",
            "startOffset": 10.0,
            "endOffset": 20.0,
            "color": color,
            "id": "hl123",
            "userId": "user123",
            "createdAt": "2023-01-01T00:00:00Z",
        }
        highlight = Highlight.model_validate(highlight_data)
        assert highlight.color == color

    def test_invalid_color_raises_error(self):
        """Test Highlight with invalid color raises ValidationError."""
        highlight_data = {
            "bookmarkId": "bm123",
            "startOffset": 10.0,
            "endOffset": 20.0,
            "color": "purple",  # Invalid color
            "id": "hl123",
            "userId": "user123",
            "createdAt": "2023-01-01T00:00:00Z",
        }
        with pytest.raises(ValidationError) as exc_info:
            Highlight.model_validate(highlight_data)
        assert "Input should be" in str(exc_info.value)

    def test_default_color(self):
        """Test Highlight uses default color when not specified."""
        highlight_data = {
            "bookmarkId": "bm123",
            "startOffset": 10.0,
            "endOffset": 20.0,
            "id": "hl123",
            "userId": "user123",
            "createdAt": "2023-01-01T00:00:00Z",
        }
        highlight = Highlight.model_validate(highlight_data)
        assert highlight.color == "yellow"  # Default value

    def test_comprehensive_aliases(self):
        """Test comprehensive alias round-trip for Highlight model."""
        highlight_data = {
            "bookmarkId": "bm123",
            "startOffset": 10.5,
            "endOffset": 25.7,
            "color": "red",
            "text": "Highlighted text",
            "note": "My note",
            "id": "hl123",
            "userId": "user456",
            "createdAt": "2023-01-01T00:00:00Z",
        }

        highlight = Highlight.model_validate(highlight_data)
        dumped = highlight.model_dump(by_alias=True)

        # Verify all camelCase aliases are preserved
        assert dumped["bookmarkId"] == "bm123"
        assert dumped["startOffset"] == 10.5
        assert dumped["endOffset"] == 25.7
        assert dumped["userId"] == "user456"
        assert dumped["createdAt"] == "2023-01-01T00:00:00Z"


class TestBookmarkList:
    """Test BookmarkList model validation."""

    @pytest.mark.parametrize("list_type", ["manual", "smart"])
    def test_valid_types(self, list_type):
        """Test BookmarkList with valid type values."""
        list_data = {
            "id": "list123",
            "name": "My List",
            "icon": "📚",
            "type": list_type,
            "public": False,
            "hasCollaborators": True,
            "userRole": "owner",
        }
        bookmark_list = BookmarkList.model_validate(list_data)
        assert bookmark_list.type == list_type

    def test_invalid_type_raises_error(self):
        """Test BookmarkList with invalid type raises ValidationError."""
        list_data = {
            "id": "list123",
            "name": "My List",
            "icon": "📚",
            "type": "automatic",  # Invalid type
            "public": False,
            "hasCollaborators": False,
            "userRole": "viewer",
        }
        with pytest.raises(ValidationError) as exc_info:
            BookmarkList.model_validate(list_data)
        assert "Input should be 'manual' or 'smart'" in str(exc_info.value)

    def test_default_type(self):
        """Test BookmarkList uses default type when not specified."""
        list_data = {
            "id": "list123",
            "name": "My List",
            "icon": "📚",
            "public": False,
            "hasCollaborators": False,
            "userRole": "viewer",
        }
        bookmark_list = BookmarkList.model_validate(list_data)
        assert bookmark_list.type == "manual"  # Default value
