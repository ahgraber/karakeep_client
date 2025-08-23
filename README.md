# karakeep_client

A small, focused Python client for a subset of the Karakeep API (https://docs.karakeep.app/).

This package provides an async client to interact with Karakeep programmatically, including bookmarking, asset uploads, tagging, and simple search/pagination helpers.

Features

- Async KarakeepClient built on httpx
- Get, search, create, update and delete bookmarks
- Upload and retrieve assets
- Attach/detach assets and tags from bookmarks
- Optional Pydantic response validation (models are provided)
- Utility to collect all bookmark URLs

Quick overview of supported operations

- get_bookmarks_paged: fetch a single page of bookmarks (supports pagination via cursor)
- get_bookmark: fetch a specific bookmark by id
- search_bookmarks: search bookmarks with query, pagination and sorting
- create_bookmark / update_bookmark / delete_bookmark
- upload_new_asset / get_asset
- add_bookmark_tags / delete_bookmark_tags
- attach_bookmark_asset / update_bookmark_asset / delete_bookmark_asset
- get_all_urls: convenience function to collect all bookmark URLs

Installation

From source (recommended for development):

1. Clone the repository

2. Install in editable mode:

   ```bash
   uv sync --dev
   ```

Or, for a plain install:

```bash
uv sync
```

Configuration

The client expects two environment variables (or you can pass them to the KarakeepClient constructor):

- KARAKEEP_API_KEY — your API key
- KARAKEEP_BASEURL — base URL of your Karakeep instance (for example: https://selfhosted.example.com)

Usage (quick start)

All client operations are asynchronous. Typical usage with Python 3.8+:

```python
import asyncio
from karakeep_client.karakeep import KarakeepClient


async def main():
    client = KarakeepClient(api_key="YOUR_KEY", base_url="https://your.karakeep.instance", verbose=True)

    # Fetch first page
    page = await client.get_bookmarks_paged(limit=10)
    for b in page.bookmarks:
        print(b.id, getattr(b.content, "url", None))

    # Create a link bookmark
    new = await client.create_bookmark(bookmark_type="link", url="https://example.com", title="Example")
    print("created:", new.id)


asyncio.run(main())
```

Demo

A demonstration script is included at `notebooks/karakeep_client_demo.py`. It shows example flows for:

- Listing bookmarks
- Searching
- Creating link/text/asset bookmarks
- Uploading and retrieving assets

Notes

- Response validation: by default, responses are validated using Pydantic models defined in karakeep_client.karakeep. You can disable validation by passing `disable_response_validation=True` to the KarakeepClient constructor or to individual methods.
- Asset retrieval returns raw bytes (Accept: */*). Bookmark content types include link, text, asset, and unknown; helper functions attempt to extract canonical URLs.
- The client is asynchronous and built on httpx; ensure you run it from an async context.

Contributing

Contributions and fixes are welcome. Please open issues or pull requests with clear descriptions and tests where appropriate.

License

[AGPL-3.0](https://github.com/ahgraber/karakeep-client/blob/main/LICENSE)
