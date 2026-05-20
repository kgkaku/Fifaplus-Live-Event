#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Fixed Version
"""

import os
import json
import requests
from datetime import datetime

# ========== CONFIGURATION ==========
BASE_URL = "https://www.plus.fifa.com"
DEVICE_PROFILE = "MOBILE"
DEVICE_STORE = "GOOGLE_PLAY"
USER_COUNTRY = "BD"

# আপনার স্থায়ী ডিভাইস টোকেন
DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjU5NWUyMGJkLWFmMDMtNDVjYi1iMDY1LWVhOTAxYmQwYTU2YiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0xMlQwODozNzoyNi40Mzk3MjYyMDhaIiwiZGlzcGxheV9uYW1lIjoiZ29vZ2xlIC0gUGl4ZWwgNCIsImlkIjoiODg1ZmZkOTUtN2E4NC00NTk5LWI2M2ItNjA2NjBiMmI1YTU5IiwibWFudWZhY3R1cmVyIjoiZ29vZ2xlIiwibW9kZWwiOiJQaXhlbCA0IiwicHJvZmlsZSI6Ik1PQklMRSIsInN0b3JlIjoiR09PR0xFX1BMQVkiLCJ1cGRhdGVkX2F0IjoiMjAyNi0wNS0xMlQwOTo0NzoyMy40MTk0NDAyMDZaIn0.RPto2B9eDE8xrnntPx0bOVx6ooHJpM44NymVSNfMd-c"

def get_live_events():
    """লাইভ ইভেন্টের তালিকা আনে"""
    url = f"{BASE_URL}/api/v2/rails/calendar?date={datetime.now().strftime('%Y-%m-%dT%H%%3A%M%%3A%S%%2B06%%3A00')}&limit=50&category=livestream"
    
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-device-profile": DEVICE_PROFILE,
        "x-chili-device-store": DEVICE_STORE,
        "x-chili-user-country": USER_COUNTRY,
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (Linux; Android 9; Pixel 4) AppleWebKit/537.36"
    }
    
    print("📡 Fetching live events...")
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"📡 Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"📡 Response type: {type(data)}")
        
        # বিভিন্ন ফরম্যাট হ্যান্ডেল করা
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            if "results" in data:
                events = data["results"]
            elif "items" in data:
                events = data["items"]
            else:
                events = []
        else:
            events = []
        
        print(f"✅ Found {len(events)} events")
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
    
    print(f"🔄 Creating session for: {video_asset_id}")
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"📡 Session Status: {resp.status_code}")
    
    if resp.status_code in [200, 201]:
        session_data = resp.json()
        print(f"✅ Session created: {session_data['id'][:40]}...")
        return session_data["id"]
    else:
        print(f"❌ Session failed: {resp.text[:100]}")
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
    print("🚀 FIFA+ Live Stream Fetcher (Correct Base URL)")
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
        
        # এখানে টাইপ চেক করা জরুরি
        if isinstance(ev, str):
            print(f"⚠️ Skipping string item: {ev[:50]}")
            continue
        
        title = ev.get('title', 'Unknown') if isinstance(ev, dict) else str(ev)
        print(f"📺 {title[:50]}...")
        
        # Get video asset id
        video_id = ev.get("catalogRedirectId") or ev.get("id") if isinstance(ev, dict) else None
        if not video_id:
            print("❌ No video ID found")
            continue
        
        # Create session and get MPD
        session_id = create_streaming_session(video_id)
        if not session_id:
            continue
        
        mpd_url = get_mpd_url(session_id)
        if mpd_url:
            results.append({
                "id": video_id,
                "title": title,
                "mpd_link": mpd_url,
                "wideCoverUrl": ev.get("wideCoverUrl", "") if isinstance(ev, dict) else ""
            })
            print(f"✅ MPD: {mpd_url[:60]}...")
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
