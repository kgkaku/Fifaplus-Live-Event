#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Complete Working Version
Based on captured API requests from 12 May 2026
"""

import os
import json
import random
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from pywidevine.device import Device
from pywidevine.cdm import Cdm
from pywidevine.pssh import PSSH

# ========== CONFIGURATION ==========
BASE_URL = "https://android.plus.fifa.com"
DEVICE_PROFILE = "MOBILE"
DEVICE_STORE = "GOOGLE_PLAY"
USER_COUNTRY = "BD"
APP_VERSION = "8.6.12"

# GitHub Secret থেকে Token নিবে
GITHUB_TOKEN = os.environ.get("PAT_TOKEN_CDM")
if not GITHUB_TOKEN:
    raise Exception("❌ PAT_TOKEN_CDM secret not found! Add it to GitHub Actions secrets.")

# ========== CDM LOAD FROM PRIVATE REPO ==========
def get_cdm_folders():
    """GitHub API ব্যবহার করে সব CDM ফোল্ডারের নাম বের করা"""
    url = "https://api.github.com/repos/kgkaku/Widevine-CDM-L3/contents/"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    
    folders = []
    for item in resp.json():
        if item["type"] == "dir":
            folders.append(item["name"])
    return folders

def download_cdm_file(folder, filename, output_path):
    """প্রাইভেট রেপো থেকে CDM ফাইল ডাউনলোড"""
    url = f"https://raw.githubusercontent.com/kgkaku/Widevine-CDM-L3/main/{folder}/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    
    with open(output_path, "wb") as f:
        f.write(resp.content)

def load_random_cdm():
    """সব CDM থেকে র‍্যান্ডম একটি বেছে নিয়ে ডাউনলোড করে Device লোড করে"""
    folders = get_cdm_folders()
    if not folders:
        raise Exception("❌ কোনো CDM ফোল্ডার পাওয়া যায়নি!")
    
    selected = random.choice(folders)
    print(f"🔄 নির্বাচিত CDM: {selected}")
    
    download_cdm_file(selected, "client_id.bin", "client_id.bin")
    download_cdm_file(selected, "private_key.pem", "private_key.pem")
    
    with open("client_id.bin", "rb") as f:
        client_id = f.read()
    with open("private_key.pem", "rb") as f:
        private_key = f.read()
    
    # pywidevine 1.8.0-এর জন্য সঠিক সিনট্যাক্স
    return Device(
        client_id=client_id,
        private_key=private_key,
        type_="ANDROID",
        security_level=3,
        flags={}
    )

# ========== FIFA+ API FUNCTIONS ==========
def register_device():
    """ডিভাইস রেজিস্ট্রেশন - exact captured format"""
    url = f"{BASE_URL}/api/v2/devices"
    headers = {
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
    payload = {
        "appVersion": APP_VERSION,
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
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    print(f"✅ Device registered: {data['device_id']}")
    return data["device_token"]

def get_live_events(device_token):
    """লাইভ ইভেন্টের তালিকা আনে"""
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30"
    headers = {
        "x-chili-device-id": device_token,
        "x-chili-device-profile": DEVICE_PROFILE,
        "x-chili-device-store": DEVICE_STORE,
        "x-chili-user-country": USER_COUNTRY,
        "accept-language": "en , en; q=0.8",
        "user-agent": "okhttp/4.12.0",
        "x-chili-api-version": "1.0",
        "x-chili-app-version": "8.6.12+8818"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    events = resp.json()
    print(f"📡 Found {len(events)} live events")
    return events

def create_streaming_session(device_token, video_asset_id):
    """স্ট্রিমিং সেশন তৈরি - exact captured headers format"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/session"
    
    # আপনার ক্যাপচার করা হেডারস - হুবহু
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
        "x-chili-device-profile": DEVICE_PROFILE,
        "x-chili-device-store": DEVICE_STORE,
        "x-chili-user-country": USER_COUNTRY,
        "content-type": "application/json; charset=UTF-8",
        "user-agent": "okhttp/4.12.0"
    }
    
    payload = {"autoPlay": False, "videoAssetId": video_asset_id}
    
    # ডিবাগ: হেডারস প্রিন্ট করুন
    print(f"🔑 Sending session request for: {video_asset_id}")
    
    resp = requests.post(url, json=payload, headers=headers)
    
    # ডিবাগ: রেসপন্স স্ট্যাটাস ও বডি
    print(f"📡 Session Response Status: {resp.status_code}")
    if resp.status_code != 201:
        print(f"❌ Response Body: {resp.text}")
    
    resp.raise_for_status()
    session_data = resp.json()
    print(f"✅ Session created: {session_data['id'][:40]}...")
    return session_data["id"]

def get_mpd_urls(device_token, session_id):
    """সেশন আইডি ব্যবহার করে MPD URLs আনে"""
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls"
    headers = {
        "x-chili-streaming-session": session_id,
        "x-chili-device-id": device_token,
        "x-chili-api-version": "1.0",
        "x-chili-app-version": "8.6.12+8818",
        "user-agent": "okhttp/4.12.0"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    streams = resp.json()
    
    if not streams:
        return None, None
    
    # HD এবং SD quality সেপারেট
    hd_url = None
    sd_url = None
    for stream in streams:
        if stream.get("quality") == "HD":
            hd_url = stream.get("url")
        elif stream.get("quality") == "SD":
            sd_url = stream.get("url")
    
    return hd_url or sd_url, streams

def extract_pssh_and_kid(mpd_url):
    """MPD ডাউনলোড করে PSSH ও KID বের করে"""
    try:
        resp = requests.get(mpd_url, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        
        pssh = None
        kid = None
        
        for cp in root.findall(".//{urn:mpeg:dash:schema:mpd:2011}ContentProtection"):
            kid_attr = cp.get("{urn:mpeg:cenc:2013}default_KID")
            if kid_attr:
                kid = kid_attr.replace("-", "")
            
            pssh_elem = cp.find(".//{urn:mpeg:cenc:2013}pssh")
            if pssh_elem is not None and pssh_elem.text:
                pssh = pssh_elem.text
            
            if pssh and kid:
                break
        
        return pssh, kid
    except Exception as e:
        print(f"⚠️ Error extracting PSSH: {e}")
        return None, None

def get_clearkey(device, pssh_b64, license_url):
    """CDM ব্যবহার করে লাইসেন্স সার্ভার থেকে ClearKey বের করা"""
    try:
        pssh = PSSH(pssh_b64)
        session_id = device.cdm.open()
        
        challenge = device.cdm.get_license_challenge(session_id, pssh)
        headers = {"Content-Type": "application/octet-stream"}
        resp = requests.post(license_url, data=challenge, headers=headers, timeout=15)
        
        if resp.status_code != 200:
            print(f"⚠️ License server returned {resp.status_code}")
            return None
        
        device.cdm.parse_license(session_id, resp.content)
        keys = device.cdm.get_keys(session_id)
        device.cdm.close(session_id)
        
        for key in keys:
            if key.type == "CONTENT":
                return f"{key.kid.hex()}:{key.key.hex()}"
        return None
    except Exception as e:
        print(f"❌ Error getting clearkey: {e}")
        return None

# ========== MAIN FUNCTION ==========
def main():
    print("=" * 50)
    print("🚀 FIFA+ Live Stream Fetcher Starting...")
    print("=" * 50)
    
    # Step 1: Load CDM
    print("\n📀 Step 1: Loading Widevine CDM...")
    try:
        device = load_random_cdm()
        print("✅ CDM loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load CDM: {e}")
        return
    
    # Step 2: Register device with FIFA+
    print("\n📱 Step 2: Registering device...")
    try:
        device_token = register_device()
        print(f"✅ Device token obtained")
    except Exception as e:
        print(f"❌ Failed to register device: {e}")
        return
    
    # Step 3: Get live events
    print("\n📡 Step 3: Fetching live events...")
    try:
        events = get_live_events(device_token)
        if not events:
            print("❌ No live events found")
            return
        print(f"✅ Found {len(events)} events")
    except Exception as e:
        print(f"❌ Failed to get events: {e}")
        return
    
    # Step 4: Process each event
    print("\n🎬 Step 4: Processing events...")
    results = []
    
    # সব ইভেন্ট প্রসেস করতে চাইলে events ব্যবহার করুন
    for idx, event in enumerate(events[:5], 1):
        print(f"\n--- [{idx}/{min(5, len(events))}] ---")
        title = event.get("title", "Unknown")[:60]
        print(f"📺 Event: {title}")
        
        try:
            # Create streaming session
            session_id = create_streaming_session(device_token, event["id"])
            
            # Get MPD URL
            mpd_url, all_streams = get_mpd_urls(device_token, session_id)
            if not mpd_url:
                print("⚠️ No MPD URL found, skipping...")
                continue
            print(f"📡 MPD URL: {mpd_url[:80]}...")
            
            # Extract PSSH and KID from MPD
            pssh, kid = extract_pssh_and_kid(mpd_url)
            if not pssh:
                print("⚠️ No PSSH found in MPD, skipping...")
                continue
            print(f"🔑 KID: {kid}")
            
            # Get ClearKey from license server
            license_url = f"{BASE_URL}/flux-capacitor/api/v1/licensing/widevine/modular?sessionId={session_id}"
            clearkey = get_clearkey(device, pssh, license_url)
            
            if clearkey:
                print(f"✅ ClearKey obtained: {clearkey[:30]}...")
            else:
                print("⚠️ No ClearKey retrieved")
            
            # Store result
            result = {
                "id": event["id"],
                "title": event.get("title", ""),
                "subtitle": event.get("subtitle", ""),
                "broadcast_type": event.get("broadcastType", ""),
                "start_time": event.get("contentStartDate", ""),
                "end_time": event.get("contentEndDate", ""),
                "wide_cover_url": event.get("wideCoverUrl", ""),
                "backdrop_url": event.get("backdropUri", ""),
                "mpd_url": mpd_url,
                "decryption_keys": [clearkey] if clearkey else [],
                "kid": kid,
                "pssh": pssh,
                "session_id": session_id
            }
            results.append(result)
            
        except Exception as e:
            print(f"❌ Failed to process event: {e}")
            continue
    
    # Step 5: Save output files
    print("\n💾 Step 5: Saving output files...")
    
    # JSON output
    output_data = {
        "metadata": {
            "name": "FIFA+ Live Events",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_events": len(results),
            "source": "GitHub Action + Widevine L3 CDM"
        },
        "events": results
    }
    
    with open("fifaplus.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print("✅ Saved fifaplus.json")
    
    # M3U output (Kodi format)
    with open("fifaplus.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# FIFA+ Live Streams - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# https://github.com/kgkaku/Fifaplus-Live-Event\n\n")
        
        for event in results:
            if event["decryption_keys"]:
                key = event["decryption_keys"][0]
                title = event["title"]
                logo = event["wide_cover_url"] or event["backdrop_url"] or ""
                
                f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="FIFA+ LIVE", {title}\n')
                f.write('#KODIPROP:inputstream.adaptive.manifest_type=mpd\n')
                f.write('#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                f.write(f'#KODIPROP:inputstream.adaptive.license_key={key}\n')
                f.write(f'{event["mpd_url"]}\n\n')
    
    print("✅ Saved fifaplus.m3u")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"✅ COMPLETED! Processed {len(results)} events")
    print(f"📁 Output files: fifaplus.json, fifaplus.m3u")
    print("=" * 50)

if __name__ == "__main__":
    main()
