from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact
import sqlite3
import hashlib
import os
import random

app = Flask(__name__)
app.secret_key = 'b3_5#y2L284624Q8znxec733'  # Замените на случайную строку

# Telegram конфиг (встроенный прямо в код)
TG_SESSION = "1ApWapzMBuzlg5kbC1qweYA5ZT3MSHLcQB5PioEv0svE5RXgmdYRJFOCucCd9Bes_iGkb7pjLsqroPbht67tP6AyluObcfvut7fGBCC__xcs3-2_AEFBC26QcPcCGr2X2NQ9dPIOD_n28NZiSDZq8OA8ICJn58UkFXvoWcW_M-OXRBQLni7cEMI5h90Oon5VcUHgevuI3mD_pOYaNCajgdR1iRejeaRRhmRHlwEqisJ5y7FTEslJYpHgTiX_QQSJspTc1FNb8-XHIwAsmnGko_ZmHFqogMQkEoxILSZUhw4ux7VM1D4loFgGElqk0hNY9Su4xHL4RsLkKZ5VKAj5kFs0KmfSqG9Y="
TG_API_ID = 28745328
TG_API_HASH = "99b7d5e0faedd6ddae2ebb8d792a763c"

# Инициализация БД
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE,
                  password_hash TEXT)''')
    conn.commit()
    conn.close()

init_db()

# HTML страницы
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Неверные данные")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password))
            conn.commit()
            session['user'] = username
            return redirect(url_for('dashboard'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Пользователь уже существует")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    with TelegramClient(StringSession(TG_SESSION), TG_API_ID, TG_API_HASH) as client:
        try:
            if data['type'] == 'phone':
                contact = InputPhoneContact(
                    client_id=random.randint(0, 9999),
                    phone=data['query'],
                    first_name="TempSearch",
                    last_name=""
                )
                result = client(ImportContactsRequest([contact]))
                if result.users:
                    user = result.users[0]
                    return jsonify({
                        "id": user.id,
                        "username": user.username,
                        "phone": user.phone
                    })

            elif data['type'] == 'username':
                entity = client.get_entity(data['query'])
                return jsonify({
                    "id": entity.id,
                    "username": entity.username,
                    "phone": getattr(entity, 'phone', None)
                })

            return jsonify({"error": "Not found"}), 404
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
