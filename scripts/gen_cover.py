#!/usr/bin/env python3
import urllib.request, json, ssl, os, base64, sys

API_KEY = "sk-2a22f55c918e47e79b37c57ca0e67525"
SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "cover_fable5.png")

prompt = "dramatic sci-fi: massive glowing AI neural network entity held on chains by human silhouette, dark blue purple cyberpunk atmosphere, electric sparks, cinematic lighting, futuristic, high contrast"

data = json.dumps({"model": "gpt-image-2", "prompt": prompt, "n": 1, "size": "1024x1024"}).encode("utf-8")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request("https://api.grsai.com/v1/images/generations", data=data, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})

print("Generating...")
resp = urllib.request.urlopen(req, context=ctx, timeout=60)
result = json.loads(resp.read().decode("utf-8"))

if "data" in result and result["data"]:
    item = result["data"][0]
    if "url" in item:
        urllib.request.urlretrieve(item["url"], SAVE_PATH)
    elif "b64_json" in item:
        with open(SAVE_PATH, "wb") as f:
            f.write(base64.b64decode(item["b64_json"]))
    print(f"SAVED:{SAVE_PATH}")
else:
    print(f"ERR:{json.dumps(result)[:300]}")
