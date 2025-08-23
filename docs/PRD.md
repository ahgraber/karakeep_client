# Product Requirements Document (PRD): Karakeep Python Client

## 1. Purpose and Goals

The goal of this project is to provide a robust, asynchronous Python client library for interacting with the Karakeep API. The client should enable developers to programmatically manage bookmarks, assets, and tags, as well as perform search and pagination operations, with a focus on ease of use, reliability, and extensibility.

## 2. Target Users

- Python developers integrating Karakeep functionality into their applications or workflows.
- Power users and automation engineers who need to interact with Karakeep programmatically.

## 3. Features and Requirements

### Functional Requirements

- Asynchronous client built on `httpx`.
- Authentication via API key and configurable base URL.
- Fetch, search, create, update, and delete bookmarks.
- Upload and retrieve assets (e.g., files, images, PDFs).
- Attach and detach assets and tags from bookmarks.
- Support for pagination and search with sorting.
- Pydantic response validation for type safety.
- Utility to collect all bookmark URLs.
- Demo script for common usage patterns.

### Non-Functional Requirements

- Code must be clean, modular, and well-documented.
- All operations must be asynchronous.
- Configuration via environment variables or constructor arguments.
- Logging for debugging and traceability.
- Error handling for API and authentication failures.

## 4. User Stories

- As a developer, I want to fetch and search bookmarks so I can display or process them in my application.
- As a user, I want to upload assets and associate them with bookmarks.
- As a developer, I want to create, update, and delete bookmarks and tags programmatically.
- As a user, I want to retrieve all bookmark URLs for analysis or export.

## 5. Success Metrics

- The client can perform all supported API operations without errors.
- Response validation can be enabled or disabled as needed.
- The demo script runs successfully and demonstrates all major features.
- Documentation is clear and sufficient for new users to get started.

## 6. Out of Scope

- Building a user interface or CLI.
- Supporting APIs outside the documented Karakeep API subset.
- Synchronous (blocking) client operations.

## 7. Acceptance Criteria

- All major features are implemented and tested.
- The client is installable via pip.
- The README provides clear setup and usage instructions.
- The codebase follows Python best practices and is maintainable.

## 8. References

- [Karakeep API Documentation](https://docs.karakeep.app/)
- Example usage in `notebooks/karakeep_client_demo.py`
