#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Complete Working Version
"""

import json
import requests
from datetime import datetime

BASE_URL = "https://www.plus.fifa.com"

def register_device():
    """ডিভাইস রেজিস্ট্রেশন করে নতুন টোকেন জেনারেট করে"""
    url = f"{BASE_URL}/api/v2/devices"
    headers = {
        "x-chili-api-version": "1.0",
        "x-chili-app-version": "8.6.12+8818",
        "accept-language": "en , en; q=0.8",
        "x-chili-authenticated": "false",
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/4.12.0"
    }
    payload = {
        "appVersion": "8.6.12",
        "architecture": "aarch64",
        "profile": "MOBILE",
        "store": "GOOGLE_PLAY",
        "manufacturer": "google",
        "model": "Pixel 4",
        "osName": "Android",
        "osVersion": "28",
        "platform": BASE_URL,
        "platformVersion": "28",
        "screenHeight": 1504,
        "screenWidth": 720
    }
    
    print("🔄 Registering new device...")
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"📡 Register Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("device_token")
        print(f"✅ New device token obtained: {token[:50]}...")
        return token
    else:
        print(f"❌ Registration failed: {resp.text}")
        return None

def get_live_events(device_token):
    """লাইভ ইভেন্টের তালিকা"""
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30"
    headers = {
        "x-chili-device-id": device_token,
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "user-agent": "okhttp/4.12.0"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    return resp.json()

def create_streaming_session(device_token, video_id):
    """স্ট্রিমিং সেশন তৈরি"""
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
        "x-chili-device-id": device_token,
        "accept-language": "en , en; q=0.8",
        "x-chili-authenticated": "false",
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/4.12.0"
    }
    
    payload = {"autoPlay": False, "videoAssetId": video_id}
    
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if resp.status_code == 201:
        return resp.json().get("id")
    else:
        print(f"❌ Session failed: {resp.status_code} - {resp.text}")
        return None

def get_mpd_url(device_token, session_id):
    """MPD URL পাওয়া"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls"
    headers = {
        "x-chili-streaming-session": session_id,
        "x-chili-device-id": device_token,
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
    
    # Step 1: Register new device
    print("\n📱 Step 1: Registering device...")
    device_token = register_device()
    if not device_token:
        print("❌ Cannot proceed without device token")
        return
    
    # Step 2: Get live events
    print("\n📡 Step 2: Fetching events...")
    events = get_live_events(device_token)
    print(f"✅ Found {len(events)} events")
    
    # Step 3: Process events
    print("\n🎬 Step 3: Processing events...")
    results = []
    
    for ev in events[:10]:
        title = ev.get("title", "Unknown")[:50]
        video_id = ev.get("id")
        print(f"\n📺 {title}...")
        
        session_id = create_streaming_session(device_token, video_id)
        if not session_id:
            continue
        
        mpd_url = get_mpd_url(device_token, session_id)
        if mpd_url:
            results.append({
                "title": ev.get("title"),
                "mpd_link": mpd_url,
                "wideCoverUrl": ev.get("wideCoverUrl", "")
            })
            print(f"   ✅ MPD obtained")
    
    # Step 4: Save outputs
    print("\n💾 Step 4: Saving files...")
    
    with open("fifaplus.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("fifaplus.m3u", "w") as f:
        f.write("#EXTM3U\n\n")
        for r in results:
            f.write(f'#EXTINF:-1 tvg-logo="{r["wideCoverUrl"]}", {r["title"]}\n')
            f.write(f'{r["mpd_link"]}\n\n')
    
    print(f"\n✅ Done! {len(results)} events processed")

if __name__ == "__main__":
    main()
