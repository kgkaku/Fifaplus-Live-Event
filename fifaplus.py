#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher with Widevine L3 CDM from Private GitHub Repo
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

# ========== কনফিগারেশন ==========
CDM_REPO = "kgkaku/Widevine-CDM-L3"
CDM_BRANCH = "main"
GITHUB_TOKEN = os.environ.get("PAT_TOKEN_CDM")

if not GITHUB_TOKEN:
    raise Exception("❌ PAT_TOKEN_CDM secret not found!")

BASE_URL = "https://android.plus.fifa.com"
DEVICE_PROFILE = "MOBILE"
DEVICE_STORE = "GOOGLE_PLAY"
USER_COUNTRY = "BD"
APP_VERSION = "8.6.12"

# ========== ১. CDM ফোল্ডার লিস্ট ==========
def get_cdm_folders():
    url = f"https://api.github.com/repos/{CDM_REPO}/contents/?ref={CDM_BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return [item["name"] for item in resp.json() if item["type"] == "dir"]

# ========== ২. CDM ফাইল ডাউনলোড ==========
def download_cdm_file(folder, filename, output_path):
    url = f"https://raw.githubusercontent.com/{CDM_REPO}/{CDM_BRANCH}/{folder}/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(resp.content)

# ========== ৩. CDM লোড ==========
def load_random_cdm():
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
    
    return Device(
        client_id=client_id,
        private_key=private_key,
        type_="ANDROID",
        security_level=3,
        flags={}
    )

# ========== ৪. ডিভাইস রেজিস্ট্রেশন ==========
def register_device():
    url = f"{BASE_URL}/api/v2/devices"
    payload = {
        "appVersion": APP_VERSION, "architecture": "aarch64",
        "profile": DEVICE_PROFILE, "store": DEVICE_STORE,
        "manufacturer": "google", "model": "Pixel 4",
        "osName": "Android", "osVersion": "28",
        "platform": BASE_URL, "platformVersion": "28",
        "screenHeight": 1504, "screenWidth": 720
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()["device_token"]

# ========== ৫. লাইভ ইভেন্ট লিস্ট ==========
def get_live_events(device_token):
    headers = {
        "x-chili-device-id": device_token,
        "x-chili-device-profile": DEVICE_PROFILE,
        "x-chili-device-store": DEVICE_STORE,
        "x-chili-user-country": USER_COUNTRY,
        "Accept": "application/json"
    }
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

# ========== ৬. স্ট্রিমিং সেশন ==========
def create_streaming_session(device_token, video_asset_id):
    headers = {
        "x-chili-device-id": device_token,
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/session"
    payload = {"autoPlay": False, "videoAssetId": video_asset_id}
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json()["id"]

# ========== ৭. MPD URL ==========
def get_mpd_url(device_token, session_id):
    headers = {
        "x-chili-device-id": device_token,
        "x-chili-streaming-session": session_id
    }
    url = f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls"
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    streams = resp.json()
    return streams[0]["url"] if streams else None

# ========== ৮. PSSH ও KID বের করা ==========
def extract_pssh_and_kid(mpd_url):
    resp = requests.get(mpd_url)
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

# ========== ৯. ClearKey বের করা ==========
def get_clearkey(device, pssh_b64, license_url):
    try:
        pssh = PSSH(pssh_b64)
        session_id = device.cdm.open()
        challenge = device.cdm.get_license_challenge(session_id, pssh)
        headers = {"Content-Type": "application/octet-stream"}
        resp = requests.post(license_url, data=challenge, headers=headers)
        
        if resp.status_code != 200:
            return None
            
        device.cdm.parse_license(session_id, resp.content)
        keys = device.cdm.get_keys(session_id)
        device.cdm.close(session_id)
        
        for key in keys:
            if key.type == "CONTENT":
                return f"{key.kid.hex()}:{key.key.hex()}"
        return None
    except Exception as e:
        print(f"❌ License error: {e}")
        return None

# ========== ১০. মেইন ==========
def main():
    print("🚀 FIFA+ Scraper starting...")
    
    device = load_random_cdm()
    print("✅ CDM loaded")
    
    device_token = register_device()
    print("✅ Device token obtained")
    
    events = get_live_events(device_token)
    print(f"📡 Found {len(events)} events")
    
    results = []
    for event in events[:3]:  # প্রথম 3টি টেস্ট (সব চাইলে 3 সরিয়ে দিন)
        try:
            title = event.get("title", "Unknown")[:60]
            print(f"🔄 Processing: {title}")
            
            session_id = create_streaming_session(device_token, event["id"])
            mpd_url = get_mpd_url(device_token, session_id)
            if not mpd_url:
                continue
            
            pssh, kid = extract_pssh_and_kid(mpd_url)
            if not pssh:
                continue
            
            license_url = f"{BASE_URL}/flux-capacitor/api/v1/licensing/widevine/modular?sessionId={session_id}"
            clearkey = get_clearkey(device, pssh, license_url)
            
            event_data = {
                "id": event["id"],
                "title": event.get("title", ""),
                "mpd_link": mpd_url,
                "decryption_keys": [clearkey] if clearkey else [],
                "wideCoverUrl": event.get("wideCoverUrl", "")
            }
            results.append(event_data)
            print(f"✅ {'Got key' if clearkey else 'No key'}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # JSON আউটপুট
    output = {
        "metadata": {
            "name": "Fifa Plus Live Events",
            "last_update_time": datetime.now().strftime("%I:%M:%S %p %d-%m-%Y"),
            "total_live": len(results)
        },
        "matches": results
    }
    
    with open("fifaplus.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    # M3U আউটপুট
    with open("fifaplus.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        for item in results:
            if item["decryption_keys"]:
                key = item["decryption_keys"][0]
                f.write(f'#EXTINF:-1 tvg-logo="{item["wideCoverUrl"]}", {item["title"]}\n')
                f.write('#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                f.write(f'#KODIPROP:inputstream.adaptive.license_key={key}\n')
                f.write(f'{item["mpd_link"]}\n\n')
    
    print(f"✅ Done! Processed {len(results)} events")

if __name__ == "__main__":
    main()
