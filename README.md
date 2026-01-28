# SRADI Metadata to Schema.org

This project extracts dataset metadata from a CKAN instances and converts it into the Schema.org JSON-LD format.

## Setup

This project uses `uv` for dependency management.

1. **Install dependencies**:

   ```bash
   uv sync
   ```

## Running the Script

To fetch the metadata and generate the `schema_org_metadata.json` file:

```bash
uv run mapping.py
```

The script will:

1. Fetch all package names from the CKAN API.
2. Fetch detailed metadata for each package.
3. Clean up descriptions (strip HTML, remove line breaks).
4. Split person names into `givenName` and `familyName`.
5. Map the metadata to Schema.org `Dataset` objects.
6. Save the result to `outputschema_org_metadata.json`.

## Running Tests

To run the automated test suite:

```bash
$env:PYTHONPATH="."; uv run pytest tests/test_mapping.py
```

## Features

- **Automated Extraction**: Processes the entire CKAN catalog.
- **Data Sanitization**: Robust cleaning of HTML and formatting from descriptions.
- **Rich Mapping**: Detailed mapping to Schema.org properties including Publication dates, People (Creators/Maintainers), and Distributions.
- **Validated Results**: 12+ unit tests covering all core mapping logic.
