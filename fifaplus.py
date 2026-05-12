#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Universal Endpoint Detector
"""

import os, json, random, requests, xml.etree.ElementTree as ET
from datetime import datetime
from pywidevine.device import Device
from pywidevine.pssh import PSSH

BASE_URL = "https://android.plus.fifa.com"
GITHUB_TOKEN = os.environ.get("PAT_TOKEN_CDM")
if not GITHUB_TOKEN:
    raise Exception("❌ PAT_TOKEN_CDM secret not found!")

def load_random_cdm():
    folders = requests.get(f"https://api.github.com/repos/kgkaku/Widevine-CDM-L3/contents/",
                          headers={"Authorization": f"token {GITHUB_TOKEN}"}).json()
    folders = [f["name"] for f in folders if f["type"] == "dir"]
    selected = random.choice(folders)
    print(f"🔄 CDM: {selected}")
    
    for file in ["client_id.bin", "private_key.pem"]:
        url = f"https://raw.githubusercontent.com/kgkaku/Widevine-CDM-L3/main/{selected}/{file}"
        r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        with open(file, "wb") as f: f.write(r.content)
    
    with open("client_id.bin", "rb") as f: cid = f.read()
    with open("private_key.pem", "rb") as f: pk = f.read()
    return Device(client_id=cid, private_key=pk, type_="ANDROID", security_level=3, flags={})

def register_device():
    endpoints = ["/api/v3/devices", "/api/v2/devices", "/api/v1/devices", "/v2/devices"]
    payload = {"appVersion": "8.6.12", "architecture": "aarch64", "profile": "MOBILE",
               "store": "GOOGLE_PLAY", "manufacturer": "google", "model": "Pixel 4",
               "osName": "Android", "osVersion": "28", "platform": BASE_URL,
               "platformVersion": "28", "screenHeight": 1504, "screenWidth": 720}
    
    for ep in endpoints:
        try:
            resp = requests.post(f"{BASE_URL}{ep}", json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("device_token") or data.get("token")
        except: continue
    raise Exception("❌ Register failed")

def get_live_events(token):
    headers = {"x-chili-device-id": token}
    urls = [f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30",
            f"{BASE_URL}/api/v1/calendar/live", f"{BASE_URL}/api/v2/schedule"]
    
    for url in urls:
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list): return data
                if "results" in data: return data["results"]
                if "items" in data: return data["items"]
        except: continue
    raise Exception("❌ Events failed")

def create_session(token, video_id):
    headers = {"x-chili-device-id": token, "Content-Type": "application/json"}
    payload = {"autoPlay": False, "videoAssetId": video_id}
    endpoints = ["/api/v3/streaming/session", "/api/v2/streaming/session", 
                 "/flux-capacitor/api/v1/streaming/session", "/playback/api/v1/session"]
    
    for ep in endpoints:
        try:
            resp = requests.post(f"{BASE_URL}{ep}", json=payload, headers=headers, timeout=10)
            if resp.status_code in [200, 201]:
                return resp.json()["id"]
        except: continue
    raise Exception("❌ Session failed")

def get_mpd(token, session_id):
    headers = {"x-chili-device-id": token, "x-chili-streaming-session": session_id}
    streams = requests.get(f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls", headers=headers).json()
    return streams[0]["url"] if streams else None

def get_keys(device, pssh, lic_url):
    session_id = device.cdm.open()
    challenge = device.cdm.get_license_challenge(session_id, PSSH(pssh))
    resp = requests.post(lic_url, data=challenge, headers={"Content-Type": "application/octet-stream"})
    if resp.status_code != 200: return None
    device.cdm.parse_license(session_id, resp.content)
    keys = device.cdm.get_keys(session_id)
    device.cdm.close(session_id)
    for key in keys:
        if key.type == "CONTENT":
            return f"{key.kid.hex()}:{key.key.hex()}"
    return None

def main():
    print("🚀 Starting...")
    device = load_random_cdm()
    token = register_device()
    events = get_live_events(token)
    print(f"📡 {len(events)} events")
    
    results = []
    for ev in events[:3]:
        try:
            print(f"🔄 {ev.get('title', ev.get('id'))[:50]}...")
            sid = create_session(token, ev["id"])
            mpd = get_mpd(token, sid)
            if not mpd: continue
            
            # MPD থেকে PSSH বের করুন (আপনার আগের পদ্ধতি)
            # ... (এক্সট্রাক্ট PSSH)
            
            # lic_url = f"{BASE_URL}/licensing/widevine?sessionId={sid}"
            # clearkey = get_keys(device, pssh, lic_url)
            
            results.append({"title": ev.get("title"), "mpd": mpd})
        except Exception as e:
            print(f"❌ {e}")
    
    print(f"✅ Done: {len(results)}")

if __name__ == "__main__":
    main()
