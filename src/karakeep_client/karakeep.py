from __future__ import annotations

import contextlib
from enum import Enum
import json
import logging
import os
import re
from typing import Any, Dict, List, Literal, Optional, Set, Union
from urllib.parse import urljoin

import httpx
from pydantic import HttpUrl
import validators

from .models import (
    Asset,
    Bookmark,
    BookmarkAsset,
    PaginatedBookmarks,
)

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def temp_env_var(key, value):
    """Context manager to temporarily set an environment variable."""
    original_value = os.getenv(key)
    os.environ[key] = value
    try:
        yield
    finally:
        if original_value is not None:
            os.environ[key] = original_value
        else:
            del os.environ[key]


# https://mathiasbynens.be/demo/url-regex
# https://gist.github.com/dperini/729294
# DO NOT CHANGE URL_REGEX
URL_REGEX = (
    r"(?:http|ftp)s?://"  # http:// or https://
    r"(?:\S+(?::\S*)?@)?"  # optional user:pass@
    r"(?![-_])(?:[-\w\u00a1-\uffff]{0,63}[^-_]\.)+"  # domain...
    r"(?:[a-z\u00a1-\uffff]{2,}\.?)"  # tld
    r"(?:[/?#]\S*)?"  # path
)


def validate_url(url: str) -> str:
    """Validate a URL.

    Args:
        url: The URL string to validate

    Returns:
    -------
        str: Validated and normalized URL
    """
    if not url or url.strip() == "":
        raise ValueError("URL cannot be empty")

    # First check if URL matches our regex pattern
    pattern = re.compile(URL_REGEX, re.IGNORECASE | re.UNICODE)
    if not pattern.match(url.strip()):
        raise ValueError(f"URL does not match expected url regex: {url}")

    validated = HttpUrl(url)
    url = str(validated)

    # ref: https://github.com/python-validators/validators/issues/139
    with temp_env_var("RAISE_VALIDATION_ERROR", "True"):
        _ = validators.url(url)

    return url


class APIError(Exception):
    """Base exception class for Karakeep API errors."""


class AuthenticationError(APIError):
    """Exception raised for authentication errors (401)."""


class KarakeepClient:
    """Asynchronous client for interacting with the Karakeep API.

    The KarakeepClient provides an asynchronous interface to interact with the Karakeep API using httpx.
    Features:
    - get all bookmarks
    - search bookmarks
    - get bookmark ID (given URL)
    - get single bookmark (by ID)
    - get bookmark assets (given bookmark ID)
    - get asset (by asset ID)
    - create, update, delete bookmarks
    - upload new asset (from file)
    - add, update, delete assets from bookmark
    - add, update, remove tags from bookmark

    Args:
        api_key: Karakeep API key. If None, will use KARAKEEP_API_KEY environment variable.
        base_url: Base URL for Karakeep API. If None, will use KARAKEEP_BASEURL environment variable.
        timeout: Request timeout in seconds (default: 30.0).
        verbose: Enable verbose logging (default: False).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        verbose: bool = False,
    ) -> None:
        self.api_key = api_key or os.environ.get("KARAKEEP_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set in KARAKEEP_API_KEY environment variable")

        self.base_url = base_url or os.environ.get("KARAKEEP_BASEURL")
        if not self.base_url:
            raise ValueError("Base URL must be provided or set in KARAKEEP_BASEURL environment variable")

        self.api_base_url = urljoin(self.base_url, "/api/v1/")  # needs trailing /
        self.timeout = timeout
        self.verbose = verbose

        self._default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def _call(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an API call to the Karakeep API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH).
            endpoint: API endpoint path.
            params: Query parameters.
            data: Request body data.
            files: Files to upload.
            extra_headers: Additional headers to merge with defaults.

        Returns:
            Response data as dict, list, or bytes depending on endpoint.

        Raises:
            AuthenticationError: If authentication fails (401).
            APIError: For other API errors.
        """
        headers = self._default_headers.copy()
        if extra_headers:
            headers.update(extra_headers)

        # For file uploads, don't set Content-Type header
        if files:
            headers.pop("Content-Type", None)

        url = urljoin(self.api_base_url, endpoint)

        # Clean params - remove None values
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        if self.verbose:
            logger.debug("Making %s request to %s", method, url)
            if params:
                logger.debug("Query params: %s", params)
            if data:
                logger.debug("Request data: %s", data)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data if data and not files else None,
                    files=files,
                    headers=headers,
                )

                if response.status_code == 401:
                    raise AuthenticationError("Authentication failed - check API key")

                # Handle 204 No Content responses
                if response.status_code == 204:
                    return {}

                response.raise_for_status()

                # For asset endpoints with Accept: */* header, return raw bytes
                if extra_headers and extra_headers.get("Accept") == "*/*":
                    return response.content

                # Try to parse as JSON
                try:
                    return response.json()
                except json.JSONDecodeError:
                    # If not JSON, return raw content
                    return response.content

            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code} error for {method} {url}"
                try:
                    error_detail = e.response.json()
                    error_msg += f": {error_detail}"
                except json.JSONDecodeError:
                    error_msg += f": {e.response.text}"
                raise APIError(error_msg) from e
            except httpx.RequestError as e:
                raise APIError(f"Request failed for {method} {url}: {e}") from e

    async def get_bookmarks_paged(
        self,
        archived: Optional[bool] = None,
        favourited: Optional[bool] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        include_content: bool = False,
    ) -> PaginatedBookmarks:
        """Get bookmarks, one page at a time. Corresponds to GET /bookmarks.

        This method fetches a single page of bookmarks.
        The 'limit' parameter controls the number of items per page for this API call.
        The 'cursor' parameter is used for pagination to get the next page.

        Args:
            archived: Filter by archived status (optional).
            favourited: Filter by favourited status (optional).
            sort_order: Sort order for results (optional).
            limit: Maximum number of bookmarks to return per page (optional, max 100).
            cursor: Pagination cursor for fetching the next page (optional).
            include_content: If set to true, bookmark's content will be included (default: False).
                Note: API default is True, but client defaults to False for performance.

        Returns:
            PaginatedBookmarks: Paginated list of bookmarks for the current page.

        Raises:
            ValueError: If limit exceeds 100.
            APIError: If the API request fails.
        """
        if limit is not None and limit > 100:
            raise ValueError("Maximum limit is 100")

        params = {
            "archived": archived,
            "favourited": favourited,
            "sortOrder": sort_order,
            "limit": limit,
            "cursor": cursor,
            "includeContent": include_content,
        }

        response_data = await self._call("GET", "bookmarks", params=params)

        try:
            return PaginatedBookmarks.model_validate(response_data)
        except Exception:
            logger.exception("Failed to validate PaginatedBookmarks response. Raw response: %s", response_data)
            raise

    async def get_bookmark(
        self,
        bookmark_id: str,
        include_content: bool = True,
    ) -> Bookmark:
        """Get a single bookmark by its ID. Corresponds to GET /bookmarks/{bookmarkId}.

        Args:
            bookmark_id: The ID of the bookmark to retrieve.
            include_content: If set to true, bookmark's content will be included (default: True).
                Note: This matches the API default.

        Returns:
            Bookmark: The requested bookmark.

        Raises:
            APIError: If the API request fails (e.g., 404 bookmark not found).
        """
        endpoint = f"bookmarks/{bookmark_id}"
        params = {"includeContent": include_content}
        response_data = await self._call("GET", endpoint, params=params)

        try:
            return Bookmark.model_validate(response_data)
        except Exception:
            logger.exception("Failed to validate Bookmark response. Raw response: %s", response_data)
            raise

    async def search_bookmarks(
        self,
        q: str,  # Search query is required
        sort_order: Optional[Literal["asc", "desc", "relevance"]] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        include_content: bool = True,
    ) -> PaginatedBookmarks:
        """Search for bookmarks. Corresponds to GET /bookmarks/search.

        Args:
            q: Search query.
            sort_order: Sort order for results (optional).
            limit: Maximum number of bookmarks to return per page (optional, max 100).
            cursor: Pagination cursor for fetching the next page (optional).
            include_content: If set to true, bookmark's content will be included (default: True).
                Note: This matches the API default.

        Returns:
            PaginatedBookmarks: Paginated list of bookmarks matching the search query.

        Raises:
            ValueError: If limit exceeds 100.
            APIError: If the API request fails.
        """
        if limit is not None and limit > 100:
            raise ValueError("Maximum limit is 100")

        params = {
            "q": q,
            "sortOrder": sort_order,
            "limit": limit,
            "cursor": cursor,
            "includeContent": include_content,
        }

        response_data = await self._call("GET", "bookmarks/search", params=params)

        try:
            return PaginatedBookmarks.model_validate(response_data)
        except Exception:
            logger.exception("Failed to validate PaginatedBookmarks response. Raw response: %s", response_data)
            raise

    async def get_bookmark_id_by_url(self, url: str) -> Optional[str]:
        """Get the bookmark ID by its URL.

        Args:
            url: The URL of the bookmark.

        Returns:
            The ID of the bookmark if found, None otherwise.
        """
        if not url or not url.strip():
            return None
        url = validate_url(url.strip())

        try:
            # Search for bookmarks with the URL as query
            search_response = await self.search_bookmarks(q=url.strip(), limit=100, include_content=True)

            # Find exact URL match
            for bookmark in search_response.bookmarks:
                bookmark_url = _extract_url_from_bookmark(bookmark, self.verbose)
                if bookmark_url and validate_url(bookmark_url.strip()) == url:
                    return bookmark.id

        except Exception as e:
            if self.verbose:
                logger.warning("Error finding bookmark by URL %s: %s", url, e)
            return None
        else:
            return None

    def _validate_bookmark_type_args(
        self,
        bookmark_type: str,
        url: Optional[str],
        text: Optional[str],
        asset_type: Optional[str],
        asset_id: Optional[str],
    ) -> None:
        """Validate type-specific arguments for bookmark creation.

        Args:
            bookmark_type: The type of bookmark.
            url: URL for link bookmarks.
            text: Text for text bookmarks.
            asset_type: Asset type for asset bookmarks.
            asset_id: Asset ID for asset bookmarks.

        Raises:
            ValueError: If required arguments are missing.
        """
        if bookmark_type == "link" and url is None:
            raise ValueError("Argument 'url' is required when bookmark_type is 'link'.")
        elif bookmark_type == "text" and text is None:
            raise ValueError("Argument 'text' is required when bookmark_type is 'text'.")
        elif bookmark_type == "asset":
            if asset_type is None:
                raise ValueError("Argument 'asset_type' ('image' or 'pdf') is required when bookmark_type is 'asset'.")
            if asset_id is None:
                raise ValueError("Argument 'asset_id' is required when bookmark_type is 'asset'.")

    def _build_bookmark_request_body(
        self,
        bookmark_type: str,
        title: Optional[str] = None,
        archived: Optional[bool] = None,
        favourited: Optional[bool] = None,
        note: Optional[str] = None,
        summary: Optional[str] = None,
        created_at: Optional[str] = None,
        url: Optional[str] = None,
        precrawled_archive_id: Optional[str] = None,
        text: Optional[str] = None,
        source_url: Optional[str] = None,
        asset_type: Optional[str] = None,
        asset_id: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build request body for bookmark creation.

        Returns:
            Request body dictionary.
        """
        request_body: Dict[str, Any] = {"type": bookmark_type}

        # Add common optional fields if provided
        if title is not None:
            request_body["title"] = title
        if archived is not None:
            request_body["archived"] = archived
        if favourited is not None:
            request_body["favourited"] = favourited
        if note is not None:
            request_body["note"] = note
        if summary is not None:
            request_body["summary"] = summary
        if created_at is not None:
            request_body["createdAt"] = created_at

        # Add type-specific fields
        if bookmark_type == "link":
            request_body["url"] = url
            if precrawled_archive_id is not None:
                request_body["precrawledArchiveId"] = precrawled_archive_id
        elif bookmark_type == "text":
            request_body["text"] = text
            if source_url is not None:
                request_body["sourceUrl"] = source_url
        elif bookmark_type == "asset":
            request_body["assetType"] = asset_type
            request_body["assetId"] = asset_id
            if file_name is not None:
                request_body["fileName"] = file_name
            if source_url is not None:
                request_body["sourceUrl"] = source_url

        return request_body

    async def create_bookmark(
        self,
        bookmark_type: Literal["link", "text", "asset"],
        # Common optional fields
        title: Optional[str] = None,
        archived: Optional[bool] = None,
        favourited: Optional[bool] = None,
        note: Optional[str] = None,
        summary: Optional[str] = None,
        created_at: Optional[str] = None,  # ISO 8601 format string
        # Link specific
        url: Optional[str] = None,
        precrawled_archive_id: Optional[str] = None,
        # Text specific
        text: Optional[str] = None,
        source_url: Optional[str] = None,  # Also used by asset
        # Asset specific
        asset_type: Optional[Literal["image", "pdf"]] = None,
        asset_id: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> Bookmark:
        """Create a new bookmark. Corresponds to POST /bookmarks.

        Args:
            bookmark_type: The type of bookmark ('link', 'text', 'asset'). Required.
            title: Optional title for the bookmark (max 1000 chars).
            archived: Optional boolean indicating if the bookmark is archived.
            favourited: Optional boolean indicating if the bookmark is favourited.
            note: Optional note content for the bookmark.
            summary: Optional summary content for the bookmark.
            created_at: Optional creation timestamp override (ISO 8601 format string).

            Link Type Specific:
            url: The URL for the link bookmark. Required if bookmark_type='link'.
            precrawled_archive_id: Optional ID of a pre-crawled archive.

            Text Type Specific:
            text: The text content for the text bookmark. Required if bookmark_type='text'.
            source_url: Optional source URL where the text originated.

            Asset Type Specific:
            asset_type: The type of asset ('image' or 'pdf'). Required if bookmark_type='asset'.
            asset_id: The ID of the uploaded asset. Required if bookmark_type='asset'.
            file_name: Optional filename for the asset.
            source_url: Optional source URL where the asset originated.

        Returns:
            Bookmark: The created bookmark.

        Raises:
            ValueError: If required arguments for the specified type are missing.
            APIError: If the API request fails.
        """
        # Validate arguments
        self._validate_bookmark_type_args(bookmark_type, url, text, asset_type, asset_id)

        # Build request body
        request_body = self._build_bookmark_request_body(
            bookmark_type=bookmark_type,
            title=title,
            archived=archived,
            favourited=favourited,
            note=note,
            summary=summary,
            created_at=created_at,
            url=url,
            precrawled_archive_id=precrawled_archive_id,
            text=text,
            source_url=source_url,
            asset_type=asset_type,
            asset_id=asset_id,
            file_name=file_name,
        )

        response_data = await self._call("POST", "bookmarks", data=request_body)

        try:
            return Bookmark.model_validate(response_data)
        except Exception:
            logger.exception("Failed to validate Bookmark response. Raw response: %s", response_data)
            raise

    async def delete_bookmark(self, bookmark_id: str) -> None:
        """Delete a bookmark by its ID. Corresponds to DELETE /bookmarks/{bookmarkId}.

        Args:
            bookmark_id: The ID of the bookmark to delete.

        Returns:
            None: Returns None upon successful deletion (204 No Content).

        Raises:
            APIError: If the API request fails (e.g., 404 bookmark not found).
        """
        endpoint = f"bookmarks/{bookmark_id}"
        await self._call("DELETE", endpoint)
        return None

    async def update_bookmark(
        self,
        bookmark_id: str,
        update_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update a bookmark by its ID. Corresponds to PATCH /bookmarks/{bookmarkId}.

        Args:
            bookmark_id: The ID of the bookmark to update.
            update_data: Dictionary containing the fields to update.

        Returns:
            dict: A dictionary representing the updated bookmark (partial representation).

        Raises:
            ValueError: If update_data is empty.
            APIError: If the API request fails.
        """
        if not update_data:
            raise ValueError("update_data must contain at least one field to update.")

        endpoint = f"bookmarks/{bookmark_id}"
        response_data = await self._call("PATCH", endpoint, data=update_data)
        return response_data

    async def add_bookmark_tags(
        self,
        bookmark_id: str,
        tag_ids: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Attach one or more tags to a bookmark. Corresponds to POST /bookmarks/{bookmarkId}/tags.

        Args:
            bookmark_id: The ID of the bookmark.
            tag_ids: List of existing tag IDs to attach (optional).
            tag_names: List of tag names to attach (will create tags if they don't exist) (optional).

        Returns:
            dict: A dictionary containing the list of attached tag IDs under the key "attached".

        Raises:
            ValueError: If no tags are provided or if arguments are invalid.
            APIError: If the API request fails.
        """
        # Validate that at least one tag source is provided
        if not tag_ids and not tag_names:
            raise ValueError("At least one of 'tag_ids' or 'tag_names' must be provided")

        # Validate input types
        if tag_ids is not None and not isinstance(tag_ids, list):
            raise ValueError("'tag_ids' must be a list of strings")

        if tag_names is not None and not isinstance(tag_names, list):
            raise ValueError("'tag_names' must be a list of strings")

        # Validate individual elements
        if tag_ids:
            for i, tag_id in enumerate(tag_ids):
                if not isinstance(tag_id, str) or not tag_id.strip():
                    raise ValueError(f"Tag ID at index {i} must be a non-empty string")

        if tag_names:
            for i, tag_name in enumerate(tag_names):
                if not isinstance(tag_name, str) or not tag_name.strip():
                    raise ValueError(f"Tag name at index {i} must be a non-empty string")

        # Construct the tags_data dict in the format expected by the API
        tags_list = []

        if tag_ids:
            for tag_id in tag_ids:
                tags_list.append({"tagId": tag_id.strip()})

        if tag_names:
            for tag_name in tag_names:
                tags_list.append({"tagName": tag_name.strip()})

        tags_data = {"tags": tags_list}

        endpoint = f"bookmarks/{bookmark_id}/tags"
        response_data = await self._call("POST", endpoint, data=tags_data)
        return response_data

    async def delete_bookmark_tags(
        self,
        bookmark_id: str,
        tag_ids: Optional[List[str]] = None,
        tag_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Detach one or more tags from a bookmark. Corresponds to DELETE /bookmarks/{bookmarkId}/tags.

        Args:
            bookmark_id: The ID of the bookmark.
            tag_ids: List of existing tag IDs to detach (optional).
            tag_names: List of tag names to detach (optional).

        Returns:
            dict: A dictionary containing the list of detached tag IDs under the key "detached".

        Raises:
            ValueError: If no tags are provided or if arguments are invalid.
            APIError: If the API request fails.
        """
        # Validate that at least one tag source is provided
        if not tag_ids and not tag_names:
            raise ValueError("At least one of 'tag_ids' or 'tag_names' must be provided")

        # Validate input types
        if tag_ids is not None and not isinstance(tag_ids, list):
            raise ValueError("'tag_ids' must be a list of strings")

        if tag_names is not None and not isinstance(tag_names, list):
            raise ValueError("'tag_names' must be a list of strings")

        # Validate individual elements
        if tag_ids:
            for i, tag_id in enumerate(tag_ids):
                if not isinstance(tag_id, str) or not tag_id.strip():
                    raise ValueError(f"Tag ID at index {i} must be a non-empty string")

        if tag_names:
            for i, tag_name in enumerate(tag_names):
                if not isinstance(tag_name, str) or not tag_name.strip():
                    raise ValueError(f"Tag name at index {i} must be a non-empty string")

        # Construct the tags_data dict in the format expected by the API
        tags_list = []

        if tag_ids:
            for tag_id in tag_ids:
                tags_list.append({"tagId": tag_id.strip()})

        if tag_names:
            for tag_name in tag_names:
                tags_list.append({"tagName": tag_name.strip()})

        tags_data = {"tags": tags_list}

        endpoint = f"bookmarks/{bookmark_id}/tags"
        response_data = await self._call("DELETE", endpoint, data=tags_data)
        return response_data

    async def attach_bookmark_asset(
        self,
        bookmark_id: str,
        asset_id: str,
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
        ],
    ) -> BookmarkAsset:
        """Attach a new asset to a bookmark. Corresponds to POST /bookmarks/{bookmarkId}/assets.

        Args:
            bookmark_id: The ID of the bookmark.
            asset_id: The ID of the asset to attach.
            asset_type: The type of asset being attached.

        Returns:
            BookmarkAsset: The attached asset object.

        Raises:
            APIError: If the API request fails.
        """
        # Construct the asset data dict as expected by the API
        asset_data = {"id": asset_id, "assetType": asset_type}

        endpoint = f"bookmarks/{bookmark_id}/assets"
        response_data = await self._call("POST", endpoint, data=asset_data)

        try:
            return BookmarkAsset.model_validate(response_data)
        except Exception:
            logger.exception("Failed to validate BookmarkAsset response. Raw response: %s", response_data)
            raise

    async def update_bookmark_asset(self, bookmark_id: str, asset_id: str, new_asset_id: str) -> None:
        """Replace an existing asset associated with a bookmark with a new one.

        Corresponds to PUT /bookmarks/{bookmarkId}/assets/{assetId}.

        Args:
            bookmark_id: The ID of the bookmark.
            asset_id: The ID of the asset to be replaced.
            new_asset_id: The ID of the new asset to replace with.

        Returns:
            None: Returns None upon successful replacement (204 No Content).

        Raises:
            APIError: If the API request fails.
        """
        # Construct the request body as expected by the API
        new_asset_data = {"assetId": new_asset_id}

        endpoint = f"bookmarks/{bookmark_id}/assets/{asset_id}"
        await self._call("PUT", endpoint, data=new_asset_data)
        return None

    async def delete_bookmark_asset(self, bookmark_id: str, asset_id: str) -> None:
        """Detach an asset from a bookmark. Corresponds to DELETE /bookmarks/{bookmarkId}/assets/{assetId}.

        Args:
            bookmark_id: The ID of the bookmark.
            asset_id: The ID of the asset to detach.

        Returns:
            None: Returns None upon successful detachment (204 No Content).

        Raises:
            APIError: If the API request fails.
        """
        endpoint = f"bookmarks/{bookmark_id}/assets/{asset_id}"
        await self._call("DELETE", endpoint)
        return None

    async def upload_new_asset(
        self,
        file_path: str,
    ) -> Asset:
        """Upload a new asset file. Corresponds to POST /assets.

        Args:
            file_path: Path to the file to upload.

        Returns:
            Asset: Details about the uploaded asset.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            APIError: If the API request fails.
        """
        import mimetypes

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = "application/octet-stream"

        if self.verbose:
            logger.debug("Uploading asset: %s (filename: %s, type: %s)", file_path, file_name, mime_type)

        try:
            with open(file_path, "rb") as f:
                file_content = f.read()
            files = {"file": (file_name, file_content, mime_type)}
            response_data = await self._call("POST", "assets", files=files)
        except IOError as e:
            raise APIError(f"Failed to read file {file_path}: {e}") from e

        try:
            return Asset.model_validate(response_data)
        except Exception:
            logger.exception("Failed to validate Asset response. Raw response: %s", response_data)
            raise

    async def get_asset(self, asset_id: str) -> bytes:
        """Get the raw content of an asset by its ID. Corresponds to GET /assets/{assetId}.

        Args:
            asset_id: The ID of the asset to retrieve.

        Returns:
            bytes: The raw asset content.

        Raises:
            ValueError: If asset_id is empty or invalid.
            APIError: If the API request fails.
        """
        if not asset_id or not asset_id.strip():
            raise ValueError("asset_id cannot be empty")

        asset_id = asset_id.strip()

        if len(asset_id) < 5:
            raise ValueError(f"asset_id appears to be invalid: {asset_id}")

        endpoint = f"assets/{asset_id}"
        extra_headers = {"Accept": "*/*"}

        if self.verbose:
            logger.debug("Retrieving asset: %s", asset_id)

        response_data = await self._call("GET", endpoint, extra_headers=extra_headers)

        if isinstance(response_data, bytes):
            if self.verbose:
                logger.debug("Retrieved asset %s: %d bytes", asset_id, len(response_data))
            return response_data
        elif response_data is None or response_data == {}:
            if self.verbose:
                logger.debug("Retrieved empty asset %s", asset_id)
            return b""
        else:
            error_msg = f"Expected bytes from asset endpoint for asset {asset_id}, got {type(response_data).__name__}"
            logger.error(error_msg)
            raise APIError(error_msg)


def _extract_url_from_bookmark(bookmark: Any, verbose: bool = False) -> Optional[str]:
    """Extract URL from a bookmark object.

    Args:
        bookmark: Bookmark object (Pydantic model).
        verbose: Enable verbose logging for error reporting.

    Returns:
        URL string if found, None otherwise.
    """
    try:
        if not hasattr(bookmark, "content"):
            return None
        content = bookmark.content

        # Get content type
        content_type = getattr(content, "type", None)

        # Extract URL based on content type
        if content_type == "link":
            return getattr(content, "url", None)
        elif content_type in ("asset", "text"):
            return getattr(content, "source_url", None)
        else:
            return None

    except Exception as e:
        if verbose:
            logger.warning("Error extracting URL from bookmark: %s", e)
        return None


async def get_all_urls(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: float = 30.0,
) -> Set[str]:
    """Get URLs of all bookmarks in Karakeep.

    This function creates a KarakeepClient internally and extracts URLs from all bookmarks.

    Args:
        api_key: Karakeep API key. If None, will use KARAKEEP_API_KEY environment variable.
        base_url: Base URL for Karakeep API. If None, will use KARAKEEP_BASEURL environment variable.
        timeout: Request timeout in seconds (default: 30.0).

    Returns:
        Set of URLs from all bookmarks.
    """
    client = KarakeepClient(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
    )

    all_urls = set()
    next_cursor = None

    while True:
        try:
            bookmarks_response = await client.get_bookmarks_paged(cursor=next_cursor, limit=100)

            bookmarks = bookmarks_response.bookmarks
            next_cursor = bookmarks_response.next_cursor

            # Extract URLs from current page
            for bookmark in bookmarks:
                url = _extract_url_from_bookmark(bookmark, client.verbose)
                if url:
                    all_urls.add(url)

            # Stop if no more pages
            if not next_cursor:
                break

        except Exception as e:
            if client.verbose:
                logger.warning("Error fetching page: %s", e)
            break

    return all_urls
