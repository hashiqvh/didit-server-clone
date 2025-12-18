# Didit Verification Image Downloader

Python script to download verification images and videos from Didit API based on session IDs in a CSV file.

## Features

- ✅ Reads CSV files with session IDs and client IDs
- ✅ Parallel processing with configurable workers (default: 4)
- ✅ Built-in rate limiting (100 requests/minute)
- ✅ Automatic retry on rate limit errors (429)
- ✅ Tracks download status in CSV (`downloaded` field)
- ✅ Skips already completed downloads
- ✅ Batch CSV updates for performance

## Setup

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python download_images.py <csv_file> [output_directory] [workers]
```

### Arguments

- `csv_file` (required): Path to CSV file containing session IDs
- `output_directory` (optional): Directory to save downloads (default: `downloads`)
- `workers` (optional): Number of parallel workers (default: 4)

### Examples

```bash
# Basic usage with defaults
python download_images.py result.csv

# Specify output directory
python download_images.py result.csv downloads

# Custom number of workers
python download_images.py result.csv downloads 4

# With virtual environment activated
source venv/bin/activate
python download_images.py result.csv downloads 4
```

## CSV File Format

The CSV file must contain the following columns:

- `id` (required): Session ID from Didit
- `client_id` (required): Client ID for organizing downloads
- `downloaded` (optional): Status field that will be updated to "completed" after successful download

### Example CSV Structure

```csv
id,client_id,workflow_id,status,downloaded
00087142-d938-4ebc-b90d-d16fba9c0ded,253432,2d365ee0-465a-4fe0-9876-e11c58f01283,Approved,
0008bae3-f817-4417-9283-e3c2777ae017,253616,2d365ee0-465a-4fe0-9876-e11c58f01283,Approved,
```

## What It Does

1. Reads the CSV file and filters rows that aren't already marked as "completed"
2. For each row:
   - Extracts `session_id` from the `id` column
   - Extracts `client_id` from the `client_id` column
   - Calls Didit API to get verification decision (with rate limiting)
   - Creates a folder named with the `client_id`
   - Downloads the following files:
     - `front_image` - from `id_verification.front_image`
     - `portrait_image` - from `id_verification.portrait_image`
     - `full_front_image` - from `id_verification.full_front_image`
     - `reference_image` - from `liveness.reference_image`
     - `video` - from `liveness.video_url`
   - Updates the `downloaded` field to "completed" in the CSV

## Output Structure

```
downloads/
├── 253432/
│   ├── front_image.jpg
│   ├── portrait_image.jpg
│   ├── full_front_image.jpg
│   ├── reference_image.jpg
│   └── video.mp4
├── 253616/
│   ├── front_image.jpg
│   ├── portrait_image.jpg
│   └── ...
```

## Configuration

### API Key

The API key can be set via environment variable:

```bash
export DIDIT_API_KEY="your_api_key_here"
```

Or it will use the hardcoded fallback value in the script.

### Rate Limiting

- **API Limit**: 100 requests per minute
- **Rate Limit Interval**: 0.6 seconds between requests (enforced globally)
- **Automatic Retry**: If rate limit (429) is hit, waits 60 seconds and retries

### Parallel Processing

- Default: 4 workers
- Each worker processes one session at a time
- CSV updates are batched (every 25 completed downloads) for performance
- Thread-safe operations ensure data integrity

## Progress Tracking

The script:
- Shows progress every 25 processed rows
- Updates the CSV file periodically to prevent data loss
- Skips rows already marked as "completed"
- Provides a summary at the end with success/failure counts

## Error Handling

- Skips rows with empty `session_id` or `client_id`
- Continues processing even if one row fails
- Handles API errors gracefully
- Automatically retries on rate limit errors (429)
- Shows detailed error messages for debugging

## Notes

- The script automatically detects file extensions from URLs
- Missing files (null URLs) are skipped
- The CSV file is updated in-place with download status
- Files are organized by `client_id` in separate folders
- The `downloads/` directory is excluded from git (see `.gitignore`)

## Requirements

- Python 3.7+
- pandas >= 2.0.0
- requests >= 2.31.0

## License

This project is for internal use only.
