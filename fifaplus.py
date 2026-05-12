#!/usr/bin/env python3
"""
FIFA+ Live Stream Fetcher - Universal Version
"""

import os, json, random, requests, xml.etree.ElementTree as ET
from datetime import datetime
from pywidevine.device import Device
from pywidevine.pssh import PSSH

# ========== SETUP ==========
BASE_URL = "https://android.plus.fifa.com"
GITHUB_TOKEN = os.environ.get("PAT_TOKEN_CDM")
if not GITHUB_TOKEN:
    raise Exception("❌ PAT_TOKEN_CDM secret not found!")

# ========== CDM LOAD FROM PRIVATE REPO ==========
def load_random_cdm():
    folders = requests.get(f"https://api.github.com/repos/kgkaku/Widevine-CDM-L3/contents/",
                          headers={"Authorization": f"token {GITHUB_TOKEN}"}).json()
    folders = [f["name"] for f in folders if f["type"] == "dir"]
    selected = random.choice(folders)
    print(f"🔄 নির্বাচিত CDM: {selected}")
    
    for file in ["client_id.bin", "private_key.pem"]:
        url = f"https://raw.githubusercontent.com/kgkaku/Widevine-CDM-L3/main/{selected}/{file}"
        r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
        with open(file, "wb") as f: f.write(r.content)
    
    with open("client_id.bin", "rb") as f: cid = f.read()
    with open("private_key.pem", "rb") as f: pk = f.read()
    return Device(client_id=cid, private_key=pk, type_="ANDROID", security_level=3, flags={})

# ========== FIFA API ==========
def register_device():
    payload = {"appVersion": "8.6.12", "architecture": "aarch64", "profile": "MOBILE",
               "store": "GOOGLE_PLAY", "manufacturer": "google", "model": "Pixel 4",
               "osName": "Android", "osVersion": "28", "platform": BASE_URL,
               "platformVersion": "28", "screenHeight": 1504, "screenWidth": 720}
    return requests.post(f"{BASE_URL}/api/v2/devices", json=payload).json()["device_token"]

def get_live_events(token):
    headers = {"x-chili-device-id": token, "x-chili-device-profile": "MOBILE"}
    url = f"{BASE_URL}/entertainment/api/v1/showcases/12959509-fd03-47a5-8f0d-53708908881b/child?limit=30"
    return requests.get(url, headers=headers).json()

def create_streaming_session(token, video_id):
    # Auto-detect working endpoint
    endpoints = [
        f"{BASE_URL}/api/v3/streaming/session",
        f"{BASE_URL}/api/v2/streaming/session",
        f"{BASE_URL}/flux-capacitor/api/v1/streaming/session",
        f"{BASE_URL}/entertainment/api/v1/session",
    ]
    headers = {"x-chili-device-id": token, "Content-Type": "application/json"}
    payload = {"autoPlay": False, "videoAssetId": video_id}
    
    for url in endpoints:
        try:
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code in [200, 201]:
                print(f"✅ সেশন URL: {url}")
                return resp.json()["id"]
        except: continue
    raise Exception("❌ কোনো সেশন এন্ডপয়েন্ট কাজ করেনি")

def get_mpd_url(token, session_id):
    headers = {"x-chili-device-id": token, "x-chili-streaming-session": session_id}
    streams = requests.get(f"{BASE_URL}/flux-capacitor/api/v1/streaming/urls", headers=headers).json()
    return streams[0]["url"] if streams else None

def extract_pssh_kid(mpd_url):
    root = ET.fromstring(requests.get(mpd_url).content)
    for cp in root.findall(".//{urn:mpeg:dash:schema:mpd:2011}ContentProtection"):
        kid = cp.get("{urn:mpeg:cenc:2013}default_KID")
        pssh_elem = cp.find(".//{urn:mpeg:cenc:2013}pssh")
        if kid and pssh_elem is not None:
            return pssh_elem.text, kid.replace("-", "")
    return None, None

def get_clearkey(device, pssh_b64, license_url):
    pssh = PSSH(pssh_b64)
    session_id = device.cdm.open()
    challenge = device.cdm.get_license_challenge(session_id, pssh)
    resp = requests.post(license_url, data=challenge, headers={"Content-Type": "application/octet-stream"})
    if resp.status_code != 200: return None
    device.cdm.parse_license(session_id, resp.content)
    keys = device.cdm.get_keys(session_id)
    device.cdm.close(session_id)
    for key in keys:
        if key.type == "CONTENT":
            return f"{key.kid.hex()}:{key.key.hex()}"
    return None

# ========== MAIN ==========
def main():
    print("🚀 শুরু হচ্ছে...")
    device = load_random_cdm()
    token = register_device()
    events = get_live_events(token)
    print(f"📡 {len(events)} টি ইভেন্ট পেয়েছি")
    
    results = []
    for ev in events[:3]:
        try:
            print(f"🔄 {ev['title'][:50]}...")
            sess_id = create_streaming_session(token, ev["id"])
            mpd_url = get_mpd_url(token, sess_id)
            if not mpd_url: continue
            pssh, kid = extract_pssh_kid(mpd_url)
            if not pssh: continue
            lic_url = f"{BASE_URL}/flux-capacitor/api/v1/licensing/widevine/modular?sessionId={sess_id}"
            clearkey = get_clearkey(device, pssh, lic_url)
            results.append({
                "id": ev["id"],
                "title": ev["title"],
                "mpd_link": mpd_url,
                "decryption_keys": [clearkey] if clearkey else [],
                "wideCoverUrl": ev.get("wideCoverUrl", "")
            })
            print(f"✅ {'কী পাওয়া গেছে' if clearkey else 'কী নেই'}")
        except Exception as e:
            print(f"❌ ব্যর্থ: {e}")
    
    # JSON ও M3U আউটপুট
    with open("fifaplus.json", "w") as f:
        json.dump({"metadata": {"name": "FIFA+ Live", "total_live": len(results)}, "matches": results}, f, indent=2)
    with open("fifaplus.m3u", "w") as f:
        f.write("#EXTM3U\n\n")
        for m in results:
            if m["decryption_keys"]:
                f.write(f'#EXTINF:-1 tvg-logo="{m["wideCoverUrl"]}", {m["title"]}\n')
                f.write('#KODIPROP:inputstream.adaptive.license_type=clearkey\n')
                f.write(f'#KODIPROP:inputstream.adaptive.license_key={m["decryption_keys"][0]}\n')
                f.write(f'{m["mpd_link"]}\n\n')
    print(f"✅ সম্পন্ন! {len(results)} টি ইভেন্ট প্রসেস করা হয়েছে")

if __name__ == "__main__":
    main()
