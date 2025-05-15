from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# 从环境变量中读取 Facebook 登录后的 Cookie
FB_COOKIE = os.getenv("FB_COOKIE")

@app.route("/fb-thumbnail")
def get_fb_thumbnail():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Missing URL"}), 400

    if not FB_COOKIE:
        return jsonify({"error": "FB_COOKIE not set"}), 500

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": FB_COOKIE
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return jsonify({"error": f"HTTP error {resp.status_code}"}), resp.status_code

        soup = BeautifulSoup(resp.text, "html.parser")
        og_image = soup.find("meta", property="og:image")
        if og_image:
            return jsonify({"thumbnail": og_image["content"]})
        else:
            return jsonify({"error": "og:image not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return "✅ FB Thumbnail Scraper is running on Render."
