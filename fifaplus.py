#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Complete Working Version
"""

import json
import requests
from datetime import datetime

# ========== CONFIGURATION ==========
BASE_URL = "https://www.plus.fifa.com"
DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjU5NWUyMGJkLWFmMDMtNDVjYi1iMDY1LWVhOTAxYmQwYTU2YiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0xMlQwODozNzoyNi40Mzk3MjYyMDhaIiwiZGlzcGxheV9uYW1lIjoiZ29vZ2xlIC0gUGl4ZWwgNCIsImlkIjoiODg1ZmZkOTUtN2E4NC00NTk5LWI2M2ItNjA2NjBiMmI1YTU5IiwibWFudWZhY3R1cmVyIjoiZ29vZ2xlIiwibW9kZWwiOiJQaXhlbCA0IiwicHJvZmlsZSI6Ik1PQklMRSIsInN0b3JlIjoiR09PR0xFX1BMQVkiLCJ1cGRhdGVkX2F0IjoiMjAyNi0wNS0xMlQwOTo0NzoyMy40MTk0NDAyMDZaIn0.RPto2B9eDE8xrnntPx0bOVx6ooHJpM44NymVSNfMd-c"

def get_live_events():
    """লাইভ ইভেন্টের তালিকা"""
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30"
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "user-agent": "okhttp/4.12.0"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    return resp.json()

def create_streaming_session(video_id):
    """সেশন তৈরি - সম্পূর্ণ হেডারসহ"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/session"
    
    headers = {
        "x-chili-avod-compatibility": "free,free-ads",
        "x-chili-streaming-proto": "https",
        "x-chili-accept-subtitle": "text/vtt;q=0.9",
        "x-chili-streaming-capability": "true",
        "x-chili-accept-stream-mode": "multi/codec-compatibility;q=0.8, mono/strict;q=0.7",
        "x-chili-accept-stream": "mpd/cenc+h264;q=0.4, mpd/clear+h264;q=0.2, mpd/cenc;q=0.3",
        "x-chili-max-width": "1600",
        "x-chili-max-height": "720",
        "x-chili-manifest-properties": "subtitles",
        "x-chili-api-version": "1.0",
        "x-chili-app-version": "8.6.12+8818",
        "x-chili-device-id": DEVICE_TOKEN,
        "accept-language": "en , en; q=0.8",
        "x-chili-authenticated": "false",
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/4.12.0"
    }
    
    payload = {"autoPlay": False, "videoAssetId": video_id}
    
    print(f"🔄 Creating session for: {video_id}")
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"📡 Session Status: {resp.status_code}")
    
    if resp.status_code == 201:
        return resp.json().get("id")
    
    # যদি 404 আসে, তাহলে API version পরিবর্তন করে চেষ্টা
    if resp.status_code == 404:
        print("⚠️ Trying alternative endpoint...")
        alt_url = f"{BASE_URL}/api/v1/streaming/session"
        resp = requests.post(alt_url, json=payload, headers=headers, timeout=30)
        print(f"📡 Alternative Status: {resp.status_code}")
        if resp.status_code == 201:
            return resp.json().get("id")
    
    return None

def get_mpd_url(session_id):
    """MPD URL পাওয়া"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls"
    headers = {
        "x-chili-streaming-session": session_id,
        "x-chili-device-id": DEVICE_TOKEN,
        "user-agent": "okhttp/4.12.0"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        streams = resp.json()
        return streams[0]["url"] if streams else None
    return None

def main():
    print("=" * 50)
    print("🚀 FIFA+ Live Stream Fetcher")
    print("=" * 50)
    
    events = get_live_events()
    print(f"📡 Found {len(events)} events")
    
    results = []
    for ev in events[:10]:
        print(f"\n📺 {ev.get('title', 'Unknown')[:50]}...")
        
        video_id = ev.get("id")
        if not video_id:
            continue
        
        session_id = create_streaming_session(video_id)
        if not session_id:
            continue
        
        mpd_url = get_mpd_url(session_id)
        if mpd_url:
            results.append({
                "id": video_id,
                "title": ev.get("title"),
                "mpd_link": mpd_url,
                "wideCoverUrl": ev.get("wideCoverUrl", "")
            })
            print(f"✅ MPD obtained")
    
    # JSON and M3U output
    with open("fifaplus.json", "w") as f:
        json.dump({"metadata": {"total_live": len(results)}, "matches": results}, f, indent=2)
    
    with open("fifaplus.m3u", "w") as f:
        f.write("#EXTM3U\n\n")
        for r in results:
            f.write(f'#EXTINF:-1, {r["title"]}\n')
            f.write(f'{r["mpd_link"]}\n\n')
    
    print(f"\n✅ Done! {len(results)} events")

if __name__ == "__main__":
    main()
