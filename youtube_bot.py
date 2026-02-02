import requests
import time
import json
import os

# ================= НАСТРОЙКИ =================

TELEGRAM_TOKEN = "ТВОЙ_TELEGRAM_TOKEN"
CHAT_ID = "ТВОЙ_CHAT_ID"
YOUTUBE_API_KEY = "ТВОЙ_YOUTUBE_API_KEY"

# Твой канал
CHANNEL_ID = "UCz8I98K4RO_Yrj1LKNmqUVA"

DATA_FILE = "data.json"

# ================= TELEGRAM =================

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

# ================= DATA =================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ================= YOUTUBE =================

def get_subscribers(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get(url, params=params).json()

    if "items" not in r or len(r["items"]) == 0:
        return None

    return int(r["items"][0]["statistics"]["subscriberCount"])


def get_latest_comment(channel_id):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "allThreadsRelatedToChannelId": channel_id,
        "order": "time",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get(url, params=params).json()

    if "items" not in r or len(r["items"]) == 0:
        return None

    snippet = r["items"][0]["snippet"]["topLevelComment"]["snippet"]

    return {
        "id": r["items"][0]["id"],
        "author": snippet["authorDisplayName"],
        "text": snippet["textDisplay"]
    }

# ================= MAIN =================

data = load_data()

print("🤖 Бот запущен")

while True:
    # --- подписчики ---
    subs = get_subscribers(CHANNEL_ID)

    if subs is not None:
        if data.get("subs") is None:
            data["subs"] = subs
        elif subs > data["subs"]:
            send_message(
                f"🎉 Новый подписчик!\n"
                f"Всего подписчиков: {subs}"
            )
            data["subs"] = subs

    # --- комментарии ---
    comment = get_latest_comment(CHANNEL_ID)

    if comment and data.get("last_comment_id") != comment["id"]:
        send_message(
            f"💬 Новый комментарий\n"
            f"Автор: {comment['author']}\n"
            f"Текст: {comment['text']}"
        )
        data["last_comment_id"] = comment["id"]

    save_data(data)
    time.sleep(180)  # 10 минут
