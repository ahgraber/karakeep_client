"""Data models for karakeep client.

Refer to the karakeep openapi spec:
https://raw.githubusercontent.com/karakeep-app/karakeep/refs/heads/main/packages/open-api/karakeep-openapi-spec.json

NOTE: use `<object>.model_dump(by_alias=True)` to serialize these models
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class StatusTypes(str, Enum):
    success = "success"
    failure = "failure"
    pending = "pending"


class NumBookmarksByAttachedType(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    ai: Optional[float] = None
    human: Optional[float] = None


class TagShort(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    id: str
    name: str
    attached_by: Literal["ai", "human"] = Field(alias="attachedBy")


class Tag(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    id: str
    name: str
    num_bookmarks: float = Field(alias="numBookmarks")
    num_bookmarks_by_attached_type: NumBookmarksByAttachedType = Field(alias="numBookmarksByAttachedType")


class Type(str, Enum):
    link = "link"


class ContentTypeLink(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

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


class ContentTypeUnknown(BaseModel):
    type: Literal["unknown"] = "unknown"


class ContentTypeText(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    type: Literal["text"] = "text"
    text: str
    source_url: Optional[str] = Field(default=None, alias="sourceUrl")


class ContentTypeAsset(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    type: Literal["asset"] = "asset"
    asset_type: Literal["image", "pdf"] = Field(alias="assetType")
    asset_id: str = Field(alias="assetId")
    file_name: Optional[str] = Field(default=None, alias="fileName")
    source_url: Optional[str] = Field(default=None, alias="sourceUrl")
    size: Optional[float] = None
    content: Optional[str] = None


class BookmarkAsset(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

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


class Asset(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    asset_id: str = Field(alias="assetId")
    content_type: str = Field(alias="contentType")
    size: float
    file_name: str = Field(alias="fileName")


class Bookmark(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

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


class PaginatedBookmarks(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    bookmarks: List[Bookmark]
    next_cursor: Optional[str] = Field(alias="nextCursor")


class Highlight(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    bookmark_id: str = Field(alias="bookmarkId")
    start_offset: float = Field(alias="startOffset")
    end_offset: float = Field(alias="endOffset")
    color: Literal["yellow", "red", "green", "blue"] = "yellow"
    text: Optional[str] = None
    note: Optional[str] = None
    id: str
    user_id: str = Field(alias="userId")
    created_at: str = Field(alias="createdAt")


class PaginatedHighlights(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    highlights: List[Highlight]
    next_cursor: Optional[str] = Field(alias="nextCursor")


class BookmarkList(BaseModel):
    model_config = ConfigDict(alias_generator=lambda field_name: field_name, populate_by_name=True)

    id: str
    name: str
    description: Optional[str] = None
    icon: str
    parent_id: Optional[str] = Field(default=None, alias="parentId")
    type: Literal["manual", "smart"] = "manual"
    query: Optional[str] = None
    public: bool
