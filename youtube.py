import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def extract_video_id(url: str) -> str | None:
    patterns = [
        r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})",
        r"(?:embed/)([a-zA-Z0-9_-]{11})",
        r"(?:shorts/)([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(url: str) -> dict | None:
    video_id = extract_video_id(url)
    if not video_id:
        return None

    api_url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    try:
        resp = requests.get(api_url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return None
        snippet = items[0]["snippet"]
        return {
            "title": snippet.get("title", "Без названия"),
            "author": snippet.get("channelTitle", "Неизвестный канал"),
        }
    except Exception as e:
        print(f"YouTube API error: {e}")
        return None
