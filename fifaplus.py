#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Using Permanent Device Token
"""

import os
import json
import requests
from datetime import datetime

# ========== CONFIGURATION ==========
BASE_URL = "https://android.plus.fifa.com"
DEVICE_PROFILE = "MOBILE"
DEVICE_STORE = "GOOGLE_PLAY"
USER_COUNTRY = "BD"

# আপনার স্থায়ী ডিভাইস টোকেন (সরাসরি এখানে যোগ করা হয়েছে)
DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjU5NWUyMGJkLWFmMDMtNDVjYi1iMDY1LWVhOTAxYmQwYTU2YiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0xMlQwODozNzoyNi40Mzk3MjYyMDhaIiwiZGlzcGxheV9uYW1lIjoiZ29vZ2xlIC0gUGl4ZWwgNCIsImlkIjoiODg1ZmZkOTUtN2E4NC00NTk5LWI2M2ItNjA2NjBiMmI1YTU5IiwibWFudWZhY3R1cmVyIjoiZ29vZ2xlIiwibW9kZWwiOiJQaXhlbCA0IiwicHJvZmlsZSI6Ik1PQklMRSIsInN0b3JlIjoiR09PR0xFX1BMQVkiLCJ1cGRhdGVkX2F0IjoiMjAyNi0wNS0xMlQwOTo0NzoyMy40MTk0NDAyMDZaIn0.RPto2B9eDE8xrnntPx0bOVx6ooHJpM44NymVSNfMd-c"

# GitHub Secret থেকে নিতে চাইলে নিচের লাইনটি আনকমেন্ট করুন
# DEVICE_TOKEN = os.environ.get("FIFA_DEVICE_TOKEN")
if not DEVICE_TOKEN:
    raise Exception("❌ DEVICE_TOKEN not found!")

def get_live_events():
    """লাইভ ইভেন্টের তালিকা আনে - স্থায়ী টোকেন ব্যবহার করে"""
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30"
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-device-profile": DEVICE_PROFILE,
        "x-chili-device-store": DEVICE_STORE,
        "x-chili-user-country": USER_COUNTRY,
        "accept-language": "en , en; q=0.8",
        "user-agent": "okhttp/4.12.0",
        "x-chili-api-version": "1.0"
    }
    
    print("📡 Fetching live events...")
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    events = resp.json()
    print(f"✅ Found {len(events)} events")
    return events

def create_streaming_session(video_asset_id):
    """স্ট্রিমিং সেশন তৈরি - স্থায়ী টোকেন ব্যবহার করে"""
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
        "x-chili-device-profile": DEVICE_PROFILE,
        "x-chili-device-store": DEVICE_STORE,
        "x-chili-user-country": USER_COUNTRY,
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/4.12.0"
    }
    
    payload = {"autoPlay": False, "videoAssetId": video_asset_id}
    
    print(f"🔄 Creating session for: {video_asset_id}")
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if resp.status_code != 201:
        print(f"❌ Status: {resp.status_code}, Response: {resp.text}")
        resp.raise_for_status()
    
    session_data = resp.json()
    print(f"✅ Session created: {session_data['id'][:40]}...")
    return session_data["id"]

def get_mpd_url(session_id):
    """সেশন আইডি ব্যবহার করে MPD URL আনে"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls"
    headers = {
        "x-chili-streaming-session": session_id,
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-api-version": "1.0",
        "x-chili-app-version": "8.6.12+8818",
        "user-agent": "okhttp/4.12.0"
    }
    
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    streams = resp.json()
    
    if streams:
        return streams[0].get("url")
    return None

def main():
    print("=" * 50)
    print("🚀 FIFA+ Live Stream Fetcher (Permanent Token)")
    print("=" * 50)
    
    # Get events
    print("\n📡 Step 1: Fetching events...")
    try:
        events = get_live_events()
        if not events:
            print("❌ No events found")
            return
    except Exception as e:
        print(f"❌ Failed: {e}")
        return
    
    # Process events
    print("\n🎬 Step 2: Processing events...")
    results = []
    
    for i, ev in enumerate(events[:10], 1):
        print(f"\n--- [{i}/{min(10, len(events))}] ---")
        print(f"📺 {ev.get('title', 'Unknown')[:50]}...")
        
        try:
            session_id = create_streaming_session(ev["id"])
            mpd_url = get_mpd_url(session_id)
            
            if mpd_url:
                results.append({
                    "id": ev["id"],
                    "title": ev.get("title"),
                    "mpd_link": mpd_url,
                    "wideCoverUrl": ev.get("wideCoverUrl", "")
                })
                print(f"✅ MPD: {mpd_url[:60]}...")
            else:
                print("❌ No MPD URL")
        except Exception as e:
            print(f"❌ Error: {e}")
    
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
