"""Data models for karakeep client.

Refer to the karakeep openapi spec:
https://raw.githubusercontent.com/karakeep-app/karakeep/refs/heads/main/packages/open-api/karakeep-openapi-spec.json

NOTE: models accept both snake_case and camelCase input. Default serialization
uses camelCase alias; use `<object>.model_dump(by_alias=False)` for snake_case output.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class KarakeepBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )


class StatusTypes(str, Enum):
    success = "success"
    failure = "failure"
    pending = "pending"


class NumBookmarksByAttachedType(KarakeepBaseModel):
    ai: Optional[float] = None
    human: Optional[float] = None


class TagShort(KarakeepBaseModel):
    id: str
    name: str
    attached_by: Literal["ai", "human"] = Field(alias="attachedBy")


class Tag(KarakeepBaseModel):
    id: str
    name: str
    num_bookmarks: float = Field(alias="numBookmarks")
    num_bookmarks_by_attached_type: NumBookmarksByAttachedType = Field(alias="numBookmarksByAttachedType")


class Type(str, Enum):
    link = "link"


class ContentTypeLink(KarakeepBaseModel):
    type: Literal["link"] = "link"
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = Field(default=None, alias="imageUrl")
    image_asset_id: Optional[str] = Field(default=None, alias="imageAssetId")
    screenshot_asset_id: Optional[str] = Field(default=None, alias="screenshotAssetId")
    full_page_archive_asset_id: Optional[str] = Field(default=None, alias="fullPageArchiveAssetId")
    precrawled_archive_asset_id: Optional[str] = Field(default=None, alias="precrawledArchiveAssetId")
    video_asset_id: Optional[str] = Field(default=None, alias="videoAssetId")
    favicon: Optional[str] = None
    html_content: Optional[str] = Field(default=None, alias="htmlContent")
    content_asset_id: Optional[str] = Field(default=None, alias="contentAssetId")
    crawled_at: Optional[str] = Field(default=None, alias="crawledAt")
    author: Optional[str] = None
    publisher: Optional[str] = None
    date_published: Optional[str] = Field(default=None, alias="datePublished")
    date_modified: Optional[str] = Field(default=None, alias="dateModified")


class ContentTypeUnknown(KarakeepBaseModel):
    type: Literal["unknown"] = "unknown"


class ContentTypeText(KarakeepBaseModel):
    type: Literal["text"] = "text"
    text: str
    source_url: Optional[str] = Field(default=None, alias="sourceUrl")


class ContentTypeAsset(KarakeepBaseModel):
    type: Literal["asset"] = "asset"
    asset_type: Literal["image", "pdf"] = Field(alias="assetType")
    asset_id: str = Field(alias="assetId")
    file_name: Optional[str] = Field(default=None, alias="fileName")
    source_url: Optional[str] = Field(default=None, alias="sourceUrl")
    size: Optional[float] = None
    content: Optional[str] = None


class BookmarkAsset(KarakeepBaseModel):
    id: str
    asset_type: Literal[
        "linkHtmlContent",
        "screenshot",
        "assetScreenshot",
        "bannerImage",
        "fullPageArchive",
        "video",
        "bookmarkAsset",
        "precrawledArchive",
        "unknown",
    ] = Field(alias="assetType")


class Asset(KarakeepBaseModel):
    asset_id: str = Field(alias="assetId")
    content_type: str = Field(alias="contentType")
    size: float
    file_name: str = Field(alias="fileName")


class Bookmark(KarakeepBaseModel):
    id: str
    created_at: str = Field(alias="createdAt")
    modified_at: Optional[str] = Field(alias="modifiedAt")
    title: Optional[str] = None
    archived: bool
    favourited: bool
    tagging_status: Optional[Literal["success", "failure", "pending"]] = Field(alias="taggingStatus")
    summarization_status: Optional[Literal["success", "failure", "pending"]] = Field(
        default=None, alias="summarizationStatus"
    )
    note: Optional[str] = None
    summary: Optional[str] = None
    tags: List[TagShort]
    content: Union[ContentTypeLink, ContentTypeText, ContentTypeAsset, ContentTypeUnknown]
    assets: List[BookmarkAsset]


class PaginatedBookmarks(KarakeepBaseModel):
    bookmarks: List[Bookmark]
    next_cursor: Optional[str] = Field(alias="nextCursor")


class Highlight(KarakeepBaseModel):
    bookmark_id: str = Field(alias="bookmarkId")
    start_offset: float = Field(alias="startOffset")
    end_offset: float = Field(alias="endOffset")
    color: Literal["yellow", "red", "green", "blue"] = "yellow"
    text: Optional[str] = None
    note: Optional[str] = None
    id: str
    user_id: str = Field(alias="userId")
    created_at: str = Field(alias="createdAt")


class PaginatedHighlights(KarakeepBaseModel):
    highlights: List[Highlight]
    next_cursor: Optional[str] = Field(alias="nextCursor")


class BookmarkList(KarakeepBaseModel):
    id: str
    name: str
    description: Optional[str] = None
    icon: str
    parent_id: Optional[str] = Field(default=None, alias="parentId")
    type: Literal["manual", "smart"] = "manual"
    query: Optional[str] = None
    public: bool
