#!/usr/bin/env python3
"""
FIFA+ Debug Script - প্রতিটি স্টেপ বিস্তারিত লগ করবে
"""

import requests
import json

BASE_URL = "https://android.plus.fifa.com"
DEVICE_PROFILE = "MOBILE"
DEVICE_STORE = "GOOGLE_PLAY"
USER_COUNTRY = "BD"

def debug_request(title, url, method="POST", headers=None, payload=None):
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"📡 URL: {url}")
    print(f"📡 Method: {method}")
    print(f"📡 Headers: {json.dumps(headers, indent=2) if headers else 'None'}")
    print(f"📡 Payload: {json.dumps(payload, indent=2) if payload else 'None'}")
    
    try:
        if method.upper() == "POST":
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
        else:
            resp = requests.get(url, headers=headers, timeout=30)
        
        print(f"📡 Response Status: {resp.status_code}")
        print(f"📡 Response Headers: {dict(resp.headers)}")
        print(f"📡 Response Body: {resp.text[:500]}")
        return resp
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

# Step 1: ডিভাইস রেজিস্ট্রেশন
print("🚀 Starting Debug...")

headers1 = {
    "x-chili-api-version": "1.0",
    "x-chili-app-version": "8.6.12+8818",
    "accept-language": "en , en; q=0.8",
    "x-chili-authenticated": "false",
    "x-chili-device-profile": DEVICE_PROFILE,
    "x-chili-device-store": DEVICE_STORE,
    "x-chili-user-country": USER_COUNTRY,
    "content-type": "application/json; charset=UTF-8",
    "user-agent": "okhttp/4.12.0"
}

payload1 = {
    "appVersion": "8.6.12",
    "architecture": "aarch64",
    "profile": DEVICE_PROFILE,
    "store": DEVICE_STORE,
    "manufacturer": "google",
    "model": "Pixel 4",
    "osName": "Android",
    "osVersion": "28",
    "platform": BASE_URL,
    "platformVersion": "28",
    "screenHeight": 1504,
    "screenWidth": 720
}

resp1 = debug_request("Device Registration", f"{BASE_URL}/api/v2/devices", "POST", headers1, payload1)
if not resp1 or resp1.status_code != 200:
    print("❌ Device registration failed. Stopping.")
    exit()

device_token = resp1.json()["device_token"]
print(f"\n✅ Device Token: {device_token[:50]}...")

# Step 2: ইভেন্ট লিস্ট
headers2 = {
    "x-chili-device-id": device_token,
    "x-chili-device-profile": DEVICE_PROFILE,
    "x-chili-device-store": DEVICE_STORE,
    "x-chili-user-country": USER_COUNTRY,
    "accept-language": "en , en; q=0.8",
    "user-agent": "okhttp/4.12.0",
    "x-chili-api-version": "1.0"
}

resp2 = debug_request("Events List", f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=5", "GET", headers2)
if not resp2 or resp2.status_code != 200:
    print("❌ Events fetch failed. Stopping.")
    exit()

events = resp2.json()
if not events:
    print("❌ No events found")
    exit()

event_id = events[0]["id"]
print(f"\n✅ Using Event ID: {event_id}")

# Step 3: স্ট্রিমিং সেশন - সব হেডার সহ
headers3 = {
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
    "x-chili-device-profile": DEVICE_PROFILE,
    "x-chili-device-store": DEVICE_STORE,
    "x-chili-user-country": USER_COUNTRY,
    "content-type": "application/json; charset=UTF-8",
    "user-agent": "okhttp/4.12.0"
}

payload3 = {"autoPlay": False, "videoAssetId": event_id}

resp3 = debug_request("Streaming Session", f"{BASE_URL}/flux-capacitor/api/v1/streaming/session", "POST", headers3, payload3)

print("\n" + "="*50)
print("🔬 Debug Complete. Check the output above.")
