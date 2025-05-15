from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import logging
from urllib.parse import urlparse, urljoin

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量中读取 Facebook 登录后的 Cookie
FB_COOKIE = os.getenv("FB_COOKIE")

@app.route("/fb-thumbnail")
def get_fb_thumbnail():
    url = request.args.get("url")
    if not url:
        logger.error("Missing URL parameter")
        return jsonify({"error": "Missing URL"}), 400

    if not FB_COOKIE:
        logger.error("FB_COOKIE environment variable not set")
        return jsonify({"error": "FB_COOKIE not set"}), 500

    # Validate URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            logger.error(f"Invalid URL: {url}")
            return jsonify({"error": "Invalid URL"}), 400
    except Exception as e:
        logger.error(f"URL parsing error: {str(e)}")
        return jsonify({"error": "Invalid URL format"}), 400

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Cookie": FB_COOKIE,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.facebook.com/",
        "Connection": "keep-alive"
    }

    try:
        logger.info(f"Fetching URL: {url}")
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        resp.raise_for_status()

        # Log response for debugging
        logger.debug(f"Response status: {resp.status_code}")
        logger.debug(f"Response snippet: {resp.text[:500]}")

        soup = BeautifulSoup(resp.text, "html.parser")
        og_image = soup.find("meta", property="og:image")

        if og_image and og_image.get("content"):
            # Ensure the image URL is absolute
            image_url = og_image["content"]
            if not urlparse(image_url).netloc:
                image_url = urljoin(url, image_url)
            logger.info(f"Found og:image: {image_url}")
            return jsonify({"thumbnail": image_url})
        else:
            logger.warning(f"No og:image found for URL: {url}")
            return jsonify({"error": "og:image not found. Page may require JavaScript rendering or valid authentication."}), 404

    except requests.HTTPError as e:
        logger.error(f"HTTP error for URL: {url} - {str(e)}")
        if resp.status_code == 400:
            return jsonify({"error": "Bad Request. Invalid or expired cookie, or Reel may be restricted."}), 400
        elif resp.status_code == 403:
            return jsonify({"error": "Access denied. Invalid or expired cookie, or page requires further authentication."}), 403
        return jsonify({"error": f"HTTP error: {str(e)}"}), resp.status_code
    except requests.Timeout:
        logger.error(f"Request timed out for URL: {url}")
        return jsonify({"error": "Request timed out"}), 504
    except requests.ConnectionError:
        logger.error(f"Connection error for URL: {url}")
        return jsonify({"error": "Failed to connect to the server"}), 502
    except Exception as e:
        logger.error(f"Unexpected error for URL: {url} - {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route("/")
def home():
    return "✅ FB Thumbnail Scraper is running on Render."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
