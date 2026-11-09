#!/usr/bin/env python3
"""
YouTube Shorts Fetcher & Downloader
------------------------------------
Step 1: Fetch all Shorts from a channel → saves shorts_list.json
Step 2: Open shorts_manager.html in your browser to select & manage downloads
Step 3: Run downloader with selected video IDs

Requirements:
    pip install yt-dlp

Usage:
    python fetch_shorts.py --channel <CHANNEL_URL_OR_ID>
    python fetch_shorts.py --channel https://www.youtube.com/@YourChannel
    python fetch_shorts.py --channel UCxxxxxxxxxxxxxxxxxxxx
    python fetch_shorts.py --download <VIDEO_ID1> <VIDEO_ID2> ...
"""

import json
import os
import sys
import argparse
import subprocess
from datetime import datetime

OUTPUT_JSON = "shorts_list.json"
DOWNLOAD_DIR = "downloaded_shorts"


def fetch_shorts(channel_url: str):
    """Fetch all Shorts metadata from a YouTube channel using yt-dlp."""
    print(f"\n🔍 Fetching Shorts from: {channel_url}")
    print("   This may take a moment...\n")

    # Normalize channel URL to /shorts tab
    if channel_url.startswith("UC") and "/" not in channel_url:
        channel_url = f"https://www.youtube.com/channel/{channel_url}/shorts"
    elif not channel_url.endswith("/shorts"):
        channel_url = channel_url.rstrip("/") + "/shorts"

    cmd = [
        "yt-dlp",
        "--flat-playlist",          # Don't download, just list
        "--dump-single-json",       # Output full JSON
        "--no-warnings",
        channel_url,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"❌ Error fetching channel:\n{result.stderr}")
            sys.exit(1)

        data = json.loads(result.stdout)
        entries = data.get("entries", [])

        if not entries:
            print("⚠️  No Shorts found. Check the channel URL.")
            sys.exit(0)

        shorts = []
        for entry in entries:
            if entry is None:
                continue
            video_id = entry.get("id", "")
            title = entry.get("title", "Unknown Title")
            duration = entry.get("duration")
            thumbnail = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            url = entry.get("url") or f"https://www.youtube.com/shorts/{video_id}"
            upload_date = entry.get("upload_date", "")

            # Format date
            if upload_date and len(upload_date) == 8:
                try:
                    dt = datetime.strptime(upload_date, "%Y%m%d")
                    upload_date = dt.strftime("%b %d, %Y")
                except:
                    pass

            shorts.append({
                "id": video_id,
                "title": title,
                "duration": duration,
                "thumbnail": thumbnail,
                "url": url,
                "upload_date": upload_date,
                "downloaded": False,
            })

        # Load existing state if available (preserve downloaded flags)
        if os.path.exists(OUTPUT_JSON):
            try:
                with open(OUTPUT_JSON, "r") as f:
                    existing = json.load(f)
                existing_map = {v["id"]: v for v in existing.get("videos", [])}
                for s in shorts:
                    if s["id"] in existing_map:
                        s["downloaded"] = existing_map[s["id"]].get("downloaded", False)
            except:
                pass

        output = {
            "channel": data.get("channel") or data.get("uploader", "Unknown Channel"),
            "channel_url": channel_url,
            "fetched_at": datetime.now().isoformat(),
            "total": len(shorts),
            "videos": shorts,
        }

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"✅ Found {len(shorts)} Shorts!")
        print(f"📄 Saved to: {OUTPUT_JSON}")
        print(f"\n➡️  Now open  shorts_manager.html  in your browser to select videos.\n")

    except subprocess.TimeoutExpired:
        print("❌ Timed out fetching channel. Try again.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse response: {e}")
        sys.exit(1)


def download_videos(video_ids: list):
    """Download selected video IDs using yt-dlp."""
    if not os.path.exists(OUTPUT_JSON):
        print(f"❌ {OUTPUT_JSON} not found. Run fetch first.")
        sys.exit(1)

    with open(OUTPUT_JSON, "r") as f:
        data = json.load(f)

    video_map = {v["id"]: v for v in data["videos"]}
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print(f"\n⬇️  Downloading {len(video_ids)} video(s) to ./{DOWNLOAD_DIR}/\n")

    for vid_id in video_ids:
        info = video_map.get(vid_id)
        title = info["title"] if info else vid_id
        url = f"https://www.youtube.com/shorts/{vid_id}"

        print(f"  ↓ {title}")

        cmd = [
            "yt-dlp",
            "-o", f"{DOWNLOAD_DIR}/%(title)s [%(id)s].%(ext)s",
            "--merge-output-format", "mp4",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--no-warnings",
            url,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    ✅ Done")
            if info:
                info["downloaded"] = True
        else:
            print(f"    ❌ Failed: {result.stderr.strip()[:100]}")

    # Save updated state
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Download complete! Files in ./{DOWNLOAD_DIR}/\n")


def sync_downloaded():
    """Sync shorts_list.json against downloaded files in downloaded_shorts/."""
    if not os.path.exists(OUTPUT_JSON):
        print(f"❌ {OUTPUT_JSON} not found. Run fetch first.")
        sys.exit(1)

    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not os.path.exists(DOWNLOAD_DIR):
        existing_files = []
    else:
        existing_files = os.listdir(DOWNLOAD_DIR)

    updated_count = 0
    for v in data.get("videos", []):
        vid_id = v.get("id")
        file_exists = any(f"[{vid_id}]" in f for f in existing_files)
        if file_exists and not v.get("downloaded"):
            v["downloaded"] = True
            updated_count += 1

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    total_downloaded = sum(1 for v in data.get("videos", []) if v.get("downloaded"))
    total = len(data.get("videos", []))
    print(f"🔄 Sync complete! Found {len(existing_files)} file(s) in ./{DOWNLOAD_DIR}/.")
    if updated_count > 0:
        print(f"   Updated {updated_count} video(s) as downloaded.")
    print(f"   Status: {total_downloaded}/{total} marked downloaded in {OUTPUT_JSON}.")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Shorts Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--channel", "-c", help="Channel URL or ID to fetch Shorts from")
    parser.add_argument("--download", "-d", nargs="+", metavar="VIDEO_ID",
                        help="Download specific video IDs")
    parser.add_argument("--download-pending", action="store_true",
                        help="Download all videos that are marked as not downloaded in the JSON file")
    parser.add_argument("--sync", action="store_true",
                        help="Sync shorts_list.json downloaded status with files in downloaded_shorts/")

    args = parser.parse_args()

    if args.channel:
        fetch_shorts(args.channel)
    elif args.download:
        download_videos(args.download)
    elif args.download_pending:
        if not os.path.exists(OUTPUT_JSON):
            print(f"❌ {OUTPUT_JSON} not found. Run fetch first.")
            sys.exit(1)
        with open(OUTPUT_JSON, "r") as f:
            data = json.load(f)
        pending_ids = [v["id"] for v in data.get("videos", []) if not v.get("downloaded")]
        if not pending_ids:
            print("✅ All videos have already been downloaded!")
        else:
            download_videos(pending_ids)
    elif args.sync:
        sync_downloaded()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
