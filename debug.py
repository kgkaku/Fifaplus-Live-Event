#!/usr/bin/env python3
"""
FIFA+ Debug Script - Saves output to file
"""

import json
import requests
from datetime import datetime

BASE_URL = "https://www.plus.fifa.com"
DEVICE_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6IjU5NWUyMGJkLWFmMDMtNDVjYi1iMDY1LWVhOTAxYmQwYTU2YiIsInR5cCI6IkpXVCJ9.eyJjcmVhdGVkX2F0IjoiMjAyNi0wNS0xMlQwODozNzoyNi40Mzk3MjYyMDhaIiwiZGlzcGxheV9uYW1lIjoiZ29vZ2xlIC0gUGl4ZWwgNCIsImlkIjoiODg1ZmZkOTUtN2E4NC00NTk5LWI2M2ItNjA2NjBiMmI1YTU5IiwibWFudWZhY3R1cmVyIjoiZ29vZ2xlIiwibW9kZWwiOiJQaXhlbCA0IiwicHJvZmlsZSI6Ik1PQklMRSIsInN0b3JlIjoiR09PR0xFX1BMQVkiLCJ1cGRhdGVkX2F0IjoiMjAyNi0wNS0xMlQwOTo0NzoyMy40MTk0NDAyMDZaIn0.RPto2B9eDE8xrnntPx0bOVx6ooHJpM44NymVSNfMd-c"

def get_live_events():
    url = f"{BASE_URL}/api/v2/rails/calendar?date={datetime.now().strftime('%Y-%m-%dT%H%%3A%M%%3A%S%%2B06%%3A00')}&limit=50&category=livestream"
    
    headers = {
        "x-chili-device-id": DEVICE_TOKEN,
        "x-chili-device-profile": "MOBILE",
        "x-chili-device-store": "GOOGLE_PLAY",
        "x-chili-user-country": "BD",
        "user-agent": "Mozilla/5.0 (Linux; Android 9; Pixel 4) AppleWebKit/537.36"
    }
    
    print("📡 Fetching live events...")
    resp = requests.get(url, headers=headers, timeout=30)
    print(f"📡 Status: {resp.status_code}")
    
    # Save raw response to file
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        f.write(f"URL: {url}\n")
        f.write(f"Status: {resp.status_code}\n")
        f.write(f"Headers: {dict(resp.headers)}\n\n")
        f.write("RAW RESPONSE:\n")
        f.write(resp.text)
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"\n✅ Response Type: {type(data)}")
        if isinstance(data, dict):
            print(f"✅ Keys: {list(data.keys())}")
        
        # Save formatted JSON
        with open("fifaplus.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return data
    else:
        print(f"❌ Failed")
        return None

def main():
    print("=" * 50)
    print("🔍 DEBUG - Checking API Response")
    print("=" * 50)
    
    data = get_live_events()
    
    if data:
        print("\n✅ API response saved to debug_output.txt and fifaplus.json")
    else:
        print("\n❌ API call failed. Check debug_output.txt")

if __name__ == "__main__":
    main()
