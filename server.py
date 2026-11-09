#!/usr/bin/env python3
import http.server
import socketserver
import json
import subprocess
import os

PORT = 8000
DOWNLOAD_DIR = "downloaded_shorts"
JSON_FILE = "shorts_list.json"

def mark_video_downloaded(video_id: str):
    """Update shorts_list.json to mark the video as downloaded."""
    if not os.path.exists(JSON_FILE):
        return
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        updated = False
        for v in data.get("videos", []):
            if v.get("id") == video_id:
                v["downloaded"] = True
                updated = True
                break
        
        if updated:
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"📝 Updated {JSON_FILE}: Marked [{video_id}] as downloaded")
    except Exception as e:
        print(f"⚠️ Failed to update {JSON_FILE}: {e}")

class ShortsManagerHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/download':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                video_id = data.get('id')
                title = data.get('title', video_id)
                
                if not video_id:
                    self.send_error(400, "Missing video ID")
                    return
                
                os.makedirs(DOWNLOAD_DIR, exist_ok=True)
                url = f"https://www.youtube.com/shorts/{video_id}"
                print(f"\n⬇️ Downloading: {title} [{video_id}]...")
                
                cmd = [
                    "yt-dlp",
                    "-o", f"{DOWNLOAD_DIR}/%(title)s [%(id)s].%(ext)s",
                    "--merge-output-format", "mp4",
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--no-warnings",
                    url,
                ]
                
                # Run yt-dlp to download directly to the folder
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Successfully downloaded: [{video_id}]")
                    mark_video_downloaded(video_id)
                else:
                    print(f"❌ Download failed for [{video_id}]: {result.stderr.strip()[:200]}")
                
                self.send_response(200 if result.returncode == 0 else 500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response_data = {
                    "success": result.returncode == 0,
                    "error": result.stderr if result.returncode != 0 else None
                }
                self.wfile.write(json.dumps(response_data).encode())
                
            except Exception as e:
                self.send_error(500, str(e))
        else:
            self.send_error(404)

if __name__ == "__main__":
    # Ensure we serve files from the current directory where the script is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), ShortsManagerHandler) as httpd:
        print(f"🚀 Shorts Manager Server started!")
        print(f"👉 Open http://localhost:{PORT}/shorts_manager.html in your browser")
        print(f"📁 Download destination: ./{DOWNLOAD_DIR}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
