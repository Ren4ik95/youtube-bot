import requests
import json
import os
import subprocess

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

CHANNEL_ID = "UCz8I98K4RO_Yrj1LKNmqUVA"
DATA_FILE = "data.json"

def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def push_if_changed():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip() == "":
        return

    subprocess.run(["git", "config", "--global", "user.email", "action@github.com"])
    subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
    subprocess.run(["git", "add", DATA_FILE])
    subprocess.run(["git", "commit", "-m", "init/update data.json"], check=False)
    subprocess.run(["git", "push"])

def get_channel_data(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get(url, params=params).json()

    if "items" not in r or len(r["items"]) == 0:
        return None, None

    item = r["items"][0]

    subs = int(item["statistics"]["subscriberCount"])
    uploads_playlist = item["contentDetails"]["relatedPlaylists"]["uploads"]

    return subs, uploads_playlist

def main():
    print("INIT CHECK")

    data = load_data()
    changed = False

    subs, uploads_playlist = get_channel_data(CHANNEL_ID)

    # ⭐ ПЕРВЫЙ ЗАПУСК — создаём память
    if data.get("subs") is None:
        data["subs"] = subs
        changed = True
        print("Создан initial data.json")

    elif subs > data["subs"]:
        send_message(f"🎉 Новый подписчик! Всего: {subs}")
        data["subs"] = subs
        changed = True

    if changed:
        save_data(data)
        push_if_changed()
    else:
        print("Нет изменений")

if __name__ == "__main__":
    main()
