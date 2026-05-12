#!/usr/bin/env python3
"""
FIFA+ Endpoint Tester - প্রতিটি এন্ডপয়েন্ট চেক করবে
"""

import requests
import json

# আপনার স্থায়ী ডিভাইস টোকেন
DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjU5NWUyMGJkLWFmMDMtNDVjYi1iMDY1LWVhOTAxYmQwYTU2YiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0xMlQwODozNzoyNi40Mzk3MjYyMDhaIiwiZGlzcGxheV9uYW1lIjoiZ29vZ2xlIC0gUGl4ZWwgNCIsImlkIjoiODg1ZmZkOTUtN2E4NC00NTk5LWI2M2ItNjA2NjBiMmI1YTU5IiwibWFudWZhY3R1cmVyIjoiZ29vZ2xlIiwibW9kZWwiOiJQaXhlbCA0IiwicHJvZmlsZSI6Ik1PQklMRSIsInN0b3JlIjoiR09PR0xFX1BMQVkiLCJ1cGRhdGVkX2F0IjoiMjAyNi0wNS0xMlQwOTo0NzoyMy40MTk0NDAyMDZaIn0.RPto2B9eDE8xrnntPx0bOVx6ooHJpM44NymVSNfMd-c"

# একটি টেস্ট ইভেন্ট আইডি (যা আপনার লিস্টে ছিল)
TEST_EVENT_ID = "10e1e627-bbb9-442d-9c33-650c95f078fa"

BASE_URL = "https://android.plus.fifa.com"

# সব সম্ভাব্য এন্ডপয়েন্ট
endpoints = [
    # Flux Capacitor versions
    "/flux-capacitor/api/v1/streaming/session",
    "/flux-capacitor/api/v2/streaming/session",
    "/flux-capacitor/v1/streaming/session",
    "/flux-capacitor/streaming/session",
    
    # API versions
    "/api/v3/streaming/session",
    "/api/v2/streaming/session",
    "/api/v1/streaming/session",
    "/v1/streaming/session",
    
    # Entertainment API
    "/entertainment/api/v1/session",
    "/entertainment/api/v1/streaming/session",
    
    # Room of Requirement
    "/room-of-requirement/api/v1/session",
    "/room-of-requirement/api/v1/streaming/session",
    
    # Playback API
    "/playback/api/v1/session",
    "/playback/session",
    
    # Other possibilities
    "/session",
    "/streaming/session"
]

def test_endpoint(url, method="POST", payload=None, extra_headers=None):
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "content-type": "application/json",
        "user-agent": "okhttp/4.12.0",
        "accept-language": "en , en; q=0.8"
    }
    if extra_headers:
        headers.update(extra_headers)
    
    if payload is None:
        payload = {"autoPlay": False, "videoAssetId": TEST_EVENT_ID}
    
    try:
        if method == "POST":
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
        else:
            resp = requests.get(url, headers=headers, timeout=10)
        
        return {
            "status": resp.status_code,
            "success": resp.status_code in [200, 201],
            "body": resp.text[:200] if resp.text else ""
        }
    except Exception as e:
        return {
            "status": "error",
            "success": False,
            "body": str(e)[:100]
        }

def main():
    print("=" * 60)
    print("🔍 FIFA+ Endpoint Tester")
    print("=" * 60)
    print(f"\n🔑 Device Token: {DEVICE_TOKEN[:50]}...")
    print(f"📺 Test Event ID: {TEST_EVENT_ID}")
    print(f"\n🔄 Testing {len(endpoints)} endpoints...\n")
    
    working_endpoints = []
    
    for ep in endpoints:
        url = f"{BASE_URL}{ep}"
        print(f"📡 Testing: {ep}")
        
        result = test_endpoint(url)
        
        status = result["status"]
        if result["success"]:
            print(f"   ✅ SUCCESS! Status: {status}")
            working_endpoints.append({"url": url, "response": result["body"]})
        else:
            print(f"   ❌ Failed: {status}")
    
    print("\n" + "=" * 60)
    if working_endpoints:
        print("✅ WORKING ENDPOINTS FOUND:")
        for we in working_endpoints:
            print(f"   → {we['url']}")
            print(f"   Response: {we['response'][:150]}")
    else:
        print("❌ No working endpoint found!")
        print("\n💡 Suggestion: Try adding more headers or check if IP is blocked.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
