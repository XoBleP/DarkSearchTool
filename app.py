from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_mail import Mail, Message
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import SendMessageRequest
import sqlite3
import hashlib
import os
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'ieysboaurgeoqwiqnzoruwifh'

# Конфигурация Telegram
TG_SESSION = "1ApWapzMBuzlg5kbC1qweYA5ZT3MSHLcQB5PioEv0svE5RXgmdYRJFOCucCd9Bes_iGkb7pjLsqroPbht67tP6AyluObcfvut7fGBCC__xcs3-2_AEFBC26QcPcCGr2X2NQ9dPIOD_n28NZiSDZq8OA8ICJn58UkFXvoWcW_M-OXRBQLni7cEMI5h90Oon5VcUHgevuI3mD_pOYaNCajgdR1iRejeaRRhmRHlwEqisJ5y7FTEslJYpHgTiX_QQSJspTc1FNb8-XHIwAsmnGko_ZmHFqogMQkEoxILSZUhw4ux7VM1D4loFgGElqk0hNY9Su4xHL4RsLkKZ5VKAj5kFs0KmfSqG9Y="
TG_API_ID = 28745328
TG_API_HASH = "99b7d5e0faedd6ddae2ebb8d792a763c"
BOT_USERNAME = "EnergyGram_robot"

# Конфигурация почты
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'swoolwh@gmail.com'
app.config['MAIL_PASSWORD'] = '22012013Dfd'
mail = Mail(app)

# Инициализация БД
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  email TEXT UNIQUE,
                  username TEXT UNIQUE,
                  password_hash TEXT,
                  verified INTEGER DEFAULT 0,
                  verification_code TEXT,
                  code_expires DATETIME)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return redirect(url_for('login'))

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
            return redirect(url_for('dashboard')
        flash('Неверные данные')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        code = str(random.randint(100000, 999999))
        expires = datetime.now() + timedelta(minutes=30)

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (email, username, password_hash, verification_code, code_expires) VALUES (?, ?, ?, ?, ?)",
                      (email, username, password, code, expires))
            conn.commit()
            
            # Отправка кода на почту
            msg = Message('Код подтверждения', sender='swoolwh@gmail.com', recipients=[email])
            msg.body = f'Ваш код подтверждения: {code}'
            mail.send(msg)
            
            session['temp_user'] = username
            return redirect(url_for('verify'))
        except sqlite3.IntegrityError:
            flash('Пользователь уже существует')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'temp_user' not in session:
        return redirect(url_for('register'))

    if request.method == 'POST':
        user_code = request.form['code']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("UPDATE users SET verified=1 WHERE username=? AND verification_code=? AND code_expires > datetime('now')",
                  (session['temp_user'], user_code))
        conn.commit()
        
        if c.rowcount > 0:
            session['user'] = session.pop('temp_user')
            conn.close()
            return redirect(url_for('dashboard'))
        
        flash('Неверный код')
        conn.close()
    return render_template('verify.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['user']))

@app.route('/api/search', methods=['POST'])
def api_search():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    search_type = data.get('type')
    query = data.get('query')

    if not all([search_type, query]):
        return jsonify({"error": "Missing parameters"}), 400

    try:
        with TelegramClient(StringSession(TG_SESSION), TG_API_ID, TG_API_HASH) as client:
            # Отправляем запрос боту
            await client.send_message(BOT_USERNAME, f"/{search_type} {query}")
            
            # Получаем последнее сообщение от бота
            messages = await client.get_messages(BOT_USERNAME, limit=1)
            result = messages[0].message
            
            return jsonify({
                "status": "success",
                "result": result
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
