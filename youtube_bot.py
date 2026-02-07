import requests
import json
import os
import subprocess

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

CHANNEL_ID = "UCz8I98K4RO_Yrj1LKNmqUVA"
DATA_FILE = "data.json"


# -------------------- TELEGRAM --------------------

def send_message(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Telegram env missing, skip message")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    try:
        requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=20)
    except Exception as e:
        print("Telegram error:", e)


# -------------------- DATA STORAGE --------------------

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            print("data.json broken, recreate")
            return {}
    return {}


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# -------------------- GIT PUSH --------------------

def push_if_changed():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )

    if result.stdout.strip() == "":
        print("No git changes")
        return

    subprocess.run(["git", "config", "--global", "user.email", "action@github.com"])
    subprocess.run(["git", "config", "--global", "user.name", "github-actions"])
    subprocess.run(["git", "add", DATA_FILE])
    subprocess.run(["git", "commit", "-m", "update data.json"], check=False)
    subprocess.run(["git", "push"])


# -------------------- YOUTUBE API --------------------

def get_channel_data(channel_id):
    url = "https://www.googleapis.com/youtube/v3/channels"

    params = {
        "part": "statistics,contentDetails",
        "id": channel_id,
        "key": YOUTUBE_API_KEY
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        print("YT STATUS:", r.status_code)
        print("YT RAW:", r.text)

        data = r.json()
    except Exception as e:
        print("YouTube request failed:", e)
        return None, None

    if "items" not in data or len(data["items"]) == 0:
        print("YouTube empty items")
        return None, None

    try:
        item = data["items"][0]

        subs = int(item["statistics"].get("subscriberCount", 0))
        uploads_playlist = item["contentDetails"]["relatedPlaylists"]["uploads"]

        return subs, uploads_playlist

    except Exception as e:
        print("Parse error:", e)
        return None, None


# -------------------- MAIN LOGIC --------------------

def main():
    print("INIT CHECK")

    data = load_data()
    changed = False

    subs, uploads_playlist = get_channel_data(CHANNEL_ID)

    # 🚨 API fail-safe — главный фикс твоей ошибки
    if subs is None:
        print("API returned None — skip run")
        return

    print("Current subs:", subs)
    print("Stored subs:", data.get("subs"))

    # ⭐ Первый запуск
    if data.get("subs") is None:
        data["subs"] = subs
        changed = True
        print("Initial data.json created")

    # 🔔 Новый подписчик
    elif subs > data["subs"]:
        send_message(f"🎉 Новый подписчик! Всего: {subs}")
        data["subs"] = subs
        changed = True
        print("Subs increased")

    else:
        print("No subs change")

    if changed:
        save_data(data)
        push_if_changed()


# -------------------- ENTRY --------------------

if __name__ == "__main__":
    main()
