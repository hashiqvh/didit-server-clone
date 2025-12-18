import os
import sys
import requests
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# =======================
# CONFIGURATION
# =======================

DIDIT_API_KEY = os.getenv(
    "DIDIT_API_KEY",
    "IpXrxiS83l14LCTv4kJH_HZ4IfQVX3raDTbxebXW4Qo"
)

API_BASE_URL = "https://verification.didit.me/v2/session"

# Didit rate limit: 100 requests / minute
RATE_LIMIT_INTERVAL = 0.6  # seconds (1 request every 0.6s)

rate_lock = Lock()
last_api_call = 0

# =======================
# RATE-LIMITED API CALL
# =======================

def get_verification_decision(session_id: str) -> dict:
    """
    Fetch verification decision with strict rate limiting.
    """
    global last_api_call

    with rate_lock:
        now = time.time()
        elapsed = now - last_api_call
        if elapsed < RATE_LIMIT_INTERVAL:
            time.sleep(RATE_LIMIT_INTERVAL - elapsed)
        last_api_call = time.time()

    url = f"{API_BASE_URL}/{session_id}/decision/"
    headers = {"X-Api-Key": DIDIT_API_KEY}

    response = requests.get(url, headers=headers, timeout=30)

    if response.status_code == 429:
        print("⚠️ Rate limit hit (429). Sleeping 60 seconds...")
        time.sleep(60)
        return get_verification_decision(session_id)

    response.raise_for_status()
    return response.json()

# =======================
# FILE DOWNLOAD HELPERS
# =======================

def get_file_extension(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()

    for ext in ["jpg", "jpeg", "png", "pdf", "mp4"]:
        if path.endswith(ext):
            return ext

    if "video" in path:
        return "mp4"

    return "jpg"


def download_file(url: str, filepath: Path) -> bool:
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(8192):
                f.write(chunk)

        return True
    except Exception as e:
        print(f"❌ Download failed: {url} | {e}")
        return False

# =======================
# SESSION PROCESSOR
# =======================

def download_verification_assets(session_id: str, client_id: str, output_dir: Path) -> bool:
    try:
        decision = get_verification_decision(session_id)
    except Exception as e:
        print(f"❌ API error for session {session_id}: {e}")
        return False

    client_folder = output_dir / str(client_id)
    client_folder.mkdir(parents=True, exist_ok=True)

    files = {}

    if decision.get("id_verification"):
        iv = decision["id_verification"]
        files.update({
            "front_image": iv.get("front_image"),
            "portrait_image": iv.get("portrait_image"),
            "full_front_image": iv.get("full_front_image"),
        })

    if decision.get("liveness"):
        lv = decision["liveness"]
        files.update({
            "reference_image": lv.get("reference_image"),
            "video": lv.get("video_url"),
        })

    success = False

    for name, url in files.items():
        if not url:
            continue

        ext = get_file_extension(url)
        path = client_folder / f"{name}.{ext}"

        if download_file(url, path):
            success = True

    return success

# =======================
# WORKER
# =======================

def process_row(args):
    index, row, output_dir = args

    session_id = str(row["id"]).strip()
    client_id = str(row["client_id"]).strip()

    if not session_id or session_id == "nan":
        return index, "skipped"

    try:
        if download_verification_assets(session_id, client_id, output_dir):
            return index, "completed"
        return index, "failed"
    except Exception as e:
        print(f"❌ Error on row {index}: {e}")
        return index, "failed"

# =======================
# MAIN
# =======================

def main():
    if len(sys.argv) < 2:
        print("Usage: python download_images.py <csv_file> [output_dir] [workers]")
        sys.exit(1)

    csv_file = sys.argv[1]
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("downloads")
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    if not os.path.exists(csv_file):
        print("CSV file not found")
        sys.exit(1)

    df = pd.read_csv(csv_file)

    if "downloaded" not in df.columns:
        df["downloaded"] = ""

    rows = [
        (idx, row, output_dir)
        for idx, row in df.iterrows()
        if str(row.get("downloaded")).lower() != "completed"
    ]

    print(f"📄 Total rows: {len(df)}")
    print(f"🚀 To process: {len(rows)}")
    print(f"⚙️ Workers: {workers}")
    print(f"⏱️ Rate limit: 100 requests/min")

    processed = 0
    completed = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(process_row, r) for r in rows]

        for future in as_completed(futures):
            idx, status = future.result()
            processed += 1

            if status == "completed":
                df.at[idx, "downloaded"] = "completed"
                completed += 1
            elif status == "failed":
                df.at[idx, "downloaded"] = "failed"
                failed += 1

            if processed % 25 == 0:
                df.to_csv(csv_file, index=False)
                print(f"Progress: {processed}/{len(rows)} | OK: {completed} | Fail: {failed}")

    df.to_csv(csv_file, index=False)

    print("\n======================")
    print("✅ DONE")
    print(f"✔ Completed: {completed}")
    print(f"❌ Failed: {failed}")
    print(f"📂 Output: {output_dir.resolve()}")
    print("======================")

if __name__ == "__main__":
    main()
