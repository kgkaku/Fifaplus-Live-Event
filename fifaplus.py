#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Working Final Version
"""

import json
import requests
from datetime import datetime

# ========== CONFIGURATION ==========
BASE_URL = "https://www.plus.fifa.com"
DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjU5NWUyMGJkLWFmMDMtNDVjYi1iMDY1LWVhOTAxYmQwYTU2YiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0xMlQwODozNzoyNi40Mzk3MjYyMDhaIiwiZGlzcGxheV9uYW1lIjoiZ29vZ2xlIC0gUGl4ZWwgNCIsImlkIjoiODg1ZmZkOTUtN2E4NC00NTk5LWI2M2ItNjA2NjBiMmI1YTU5IiwibWFudWZhY3R1cmVyIjoiZ29vZ2xlIiwibW9kZWwiOiJQaXhlbCA0IiwicHJvZmlsZSI6Ik1PQklMRSIsInN0b3JlIjoiR09PR0xFX1BMQVkiLCJ1cGRhdGVkX2F0IjoiMjAyNi0wNS0xMlQwOTo0NzoyMy40MTk0NDAyMDZaIn0.RPto2B9eDE8xrnntPx0bOVx6ooHJpM44NymVSNfMd-c"

def get_live_events():
    """লাইভ ইভেন্টের তালিকা আনে - সঠিক এন্ডপয়েন্ট ব্যবহার করে"""
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=50"
    
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Linux; Android 9; Pixel 4) AppleWebKit/537.36"
    }
    
    print("📡 Fetching live events...")
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"📡 Status: {resp.status_code}")
    
    if resp.status_code == 200:
        events = resp.json()
        print(f"✅ Found {len(events)} live events")
        return events
    else:
        print(f"❌ Failed: {resp.text[:200]}")
        return []

def create_streaming_session(video_asset_id):
    """স্ট্রিমিং সেশন তৈরি"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/session"
    
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-avod-compatibility": "free,free-ads",
        "x-chili-streaming-proto": "https",
        "x-chili-accept-stream": "mpd/cenc+h264;q=0.4",
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Linux; Android 9; Pixel 4) AppleWebKit/537.36"
    }
    
    payload = {"autoPlay": False, "videoAssetId": video_asset_id}
    
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if resp.status_code in [200, 201]:
        session_data = resp.json()
        return session_data.get("id")
    return None

def get_mpd_url(session_id):
    """সেশন আইডি ব্যবহার করে MPD URL আনে"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls"
    headers = {
        "x-chili-streaming-session": session_id,
        "x-chili-device-id": DEVICE_TOKEN,
        "user-agent": "Mozilla/5.0 (Linux; Android 9; Pixel 4) AppleWebKit/537.36"
    }
    
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        streams = resp.json()
        if streams and isinstance(streams, list):
            return streams[0].get("url")
    return None

def main():
    print("=" * 50)
    print("🚀 FIFA+ Live Stream Fetcher")
    print("=" * 50)
    
    # Get events
    print("\n📡 Step 1: Fetching events...")
    events = get_live_events()
    if not events:
        print("❌ No events found")
        return
    
    # Process events
    print("\n🎬 Step 2: Processing events...")
    results = []
    
    for i, ev in enumerate(events[:10], 1):
        print(f"\n--- [{i}/{min(10, len(events))}] ---")
        title = ev.get('title', 'Unknown')[:50]
        print(f"📺 {title}...")
        
        video_id = ev.get("id")
        if not video_id:
            print("❌ No video ID")
            continue
        
        session_id = create_streaming_session(video_id)
        if not session_id:
            print("❌ Session failed")
            continue
        
        mpd_url = get_mpd_url(session_id)
        if mpd_url:
            results.append({
                "id": video_id,
                "title": ev.get("title"),
                "mpd_link": mpd_url,
                "wideCoverUrl": ev.get("wideCoverUrl", "")
            })
            print(f"✅ Got MPD URL")
        else:
            print("❌ No MPD URL")
    
    # Save output
    print("\n💾 Step 3: Saving files...")
    
    output = {
        "metadata": {
            "name": "FIFA+ Live Events",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_live": len(results)
        },
        "matches": results
    }
    
    with open("fifaplus.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    with open("fifaplus.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for r in results:
            f.write(f'#EXTINF:-1 tvg-logo="{r["wideCoverUrl"]}", {r["title"]}\n')
            f.write(f'{r["mpd_link"]}\n\n')
    
    print(f"\n✅ Done! {len(results)} events saved")

if __name__ == "__main__":
    main()
