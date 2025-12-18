# Python Image Downloader

Python program to read an Excel file with session IDs, fetch verification decisions from Didit API, and download verification images.

## Setup

1. Install Python dependencies:
```bash
cd python
pip install -r requirements.txt
```

Or install individually:
```bash
pip install pandas openpyxl requests
```

## Usage

From the `python` directory:
```bash
python download_images.py <excel_file> [output_directory]
```

Or from the project root:
```bash
python python/download_images.py client-session.xlsx ./downloads
```

### Examples

```bash
# From python directory - use relative paths to parent
cd python
python download_images.py ../client-session.xlsx ../downloads

# From project root
python python/download_images.py client-session.xlsx ./downloads
```

## Excel File Format

The Excel file should contain at least one of these columns:
- `session_id` or column containing "session" and "id" (required)
- `client_id` or `crm_client_id` or column containing "client" and "id" (optional, uses session_id if not found)

### Example Excel Structure

| session_id | client_id | email |
|------------|-----------|-------|
| 6b62bcb6-868a-4e97-9d38-3a81577695d0 | 273341 | user@example.com |
| b33f7e9b-8aa4-46d6-9b61-4eb0a510a1b6 | 271602 | another@example.com |

## What It Does

1. Reads the Excel file
2. For each row:
   - Extracts `session_id` and `client_id`
   - Calls Didit API to get verification decision (equivalent to `getVerificationDecision` function in `src/index.ts`)
   - Creates a folder named with the `client_id`
   - Downloads the following files:
     - `front_image` - from `id_verification.front_image`
     - `portrait_image` - from `id_verification.portrait_image`
     - `full_front_image` - from `id_verification.full_front_image`
     - `reference_image` - from `liveness.reference_image`
     - `video_url` - from `liveness.video_url`
   - Saves files with their field names as filenames (e.g., `front_image.jpg`, `video_url.mp4`)

## Output Structure

```
downloads/
├── 273341/
│   ├── front_image.jpg
│   ├── portrait_image.jpg
│   ├── full_front_image.pdf
│   ├── reference_image.jpg
│   └── video_url.mp4
├── 271602/
│   ├── front_image.jpg
│   ├── portrait_image.jpg
│   └── ...
```

## Configuration

The API key can be set via environment variable or uses the hardcoded fallback value:

1. Set environment variable:
```bash
export DIDIT_API_KEY="your_api_key_here"
```

2. Or the script will use the hardcoded fallback value (already configured)

## Error Handling

- Skips rows with empty session_id
- Continues processing even if one row fails
- Shows detailed error messages for failed downloads
- Provides summary at the end

## Notes

- The program includes a 0.5 second delay between requests to avoid rate limiting
- File extensions are automatically detected from URLs or inferred from content
- Missing files (null URLs) are skipped with a warning

