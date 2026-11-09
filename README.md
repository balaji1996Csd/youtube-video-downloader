# YouTube Shorts Manager

A tool to fetch, manage, and download YouTube Shorts from any channel. It comes with a command-line script to fetch data and web-based UIs to manage and download videos.

---

## Key Differences: `shorts_manager.html` vs `shorts_manager_1.html`

| Feature | `shorts_manager.html` (Current / Recommended) | `shorts_manager_1.html` (Legacy / Prototype) |
|---|---|---|
| **Server Requirement** | Runs with `server.py` on port `8000` (or standalone with file drop). | Expects an API server on port `8765` (`http://localhost:8765`). |
| **Data Loading** | **Auto-loads** `shorts_list.json` when served via HTTP; also supports drag-and-drop / file picker. | Strictly fetches `GET http://localhost:8765/api/shorts`. No file drop support. |
| **Download Endpoint** | Calls `POST /download` with `{ id, title }` on the local `server.py`. | Calls `POST /api/download/<id>`. |
| **Progress Tracking** | Status indicators (`Downloading…`, `✓ Downloaded`, error toasts). | Uses Server-Sent Events (SSE) on `/api/stream/<id>` to display live percentage circles, speed, ETA, and a live yt-dlp terminal log drawer. |
| **State Persistence** | Server automatically marks downloaded videos in `shorts_list.json` on disk upon completion. Also has a manual **"Save Progress"** export button. | Server marks downloaded state in backend session. |

---

## Prerequisites
- Python 3.7+
- `yt-dlp` (Install via `pip install yt-dlp`)

---

## Step-by-Step Usage

### 1. Fetch Shorts Metadata
Fetch all shorts metadata from a target YouTube channel into `shorts_list.json`:
```bash
python3 fetch_shorts.py --channel https://www.youtube.com/@YourChannel
# OR using Channel ID
python3 fetch_shorts.py --channel UCxxxxxxxxxxxxxxxxxxxx
```

### 2. Manage & Download via Web UI (`shorts_manager.html`)
To download videos directly through the UI, start the local server:
```bash
python3 server.py
```
Then open in your browser:
```
http://localhost:8000/shorts_manager.html
```
- **Auto-load**: When opened via the server, `shorts_list.json` is loaded automatically. (If opening via `file://`, simply drag and drop `shorts_list.json` onto the page).
- **Download**: Click **Download** on any video card or click **Download All Pending**. `server.py` invokes `yt-dlp` in the background, downloads the highest-quality MP4 into `./downloaded_shorts/`, and updates `shorts_list.json` on disk automatically.
- **Filter & Search**: Search titles or filter by "All", "Pending", or "Downloaded".

### 3. Alternative: Command-Line Downloads
You can also download directly from the terminal without the web browser:

- **Download all pending videos**:
  ```bash
  python3 fetch_shorts.py --download-pending
  ```

- **Download specific video IDs**:
  ```bash
  python3 fetch_shorts.py --download <VIDEO_ID_1> <VIDEO_ID_2>
  ```

- **Sync downloaded status with existing files in folder**:
  ```bash
  python3 fetch_shorts.py --sync
  ```

All downloaded videos are saved to `./downloaded_shorts/%(title)s [%(id)s].mp4`.
