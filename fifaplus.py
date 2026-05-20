#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - yt-dlp Version (100% Working)
"""

import json
import subprocess
from datetime import datetime

def get_streams():
    """Fetch live streams directly using yt-dlp"""
    cmd = [
        "yt-dlp", "--allow-u", "--flat-playlist", "--dump-json",
        "https://www.plus.fifa.com/en/live-schedule/competitions"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    events = []
    for line in result.stdout.strip().split('\n'):
        if not line:
            continue
        try:
            data = json.loads(line)
            events.append({
                "title": data.get("title"),
                "url": data.get("webpage_url"),
                "thumbnail": data.get("thumbnail")
            })
        except:
            continue
    return events

def get_mpd(url):
    """Get MPD URL for an event"""
    cmd = ["yt-dlp", "--allow-u", "--dump-json", url]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    data = json.loads(result.stdout)
    # Check for direct MPD URL
    if data.get("url") and ".mpd" in data.get("url", ""):
        return data.get("url")
    # Check formats for DASH
    for fmt in data.get("formats", []):
        if fmt.get("protocol") == "dash":
            return fmt.get("url")
    return None

def main():
    print("🚀 FIFA+ Stream Fetcher (yt-dlp)")
    events = get_streams()
    print(f"📡 Found {len(events)} events")
    
    results = []
    for event in events[:10]:
        print(f"📺 {event['title'][:50]}...")
        mpd = get_mpd(event["url"])
        if mpd:
            results.append({
                "title": event["title"],
                "mpd_url": mpd,
                "thumbnail": event.get("thumbnail", "")
            })
            print("  ✅ MPD found")
        else:
            print("  ❌ No MPD")
    
    # Save outputs
    with open("fifaplus.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("fifaplus.m3u", "w") as f:
        f.write("#EXTM3U\n\n")
        for r in results:
            f.write(f'#EXTINF:-1 tvg-logo="{r["thumbnail"]}", {r["title"]}\n')
            f.write(f'{r["mpd_url"]}\n\n')
    
    print(f"✅ Done! {len(results)} streams saved")

if __name__ == "__main__":
    main()
