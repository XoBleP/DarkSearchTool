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
app.secret_key = os.environ.get('SECRET_KEY', 'DarkSearch')

# Конфиг Telegram с ВАШЕЙ сессией
TG_SESSION = "1ApWapzMBuzlg5kbC1qweYA5ZT3MSHLcQB5PioEv0svE5RXgmdYRJFOCucCd9Bes_iGkb7pjLsqroPbht67tP6AyluObcfvut7fGBCC__xcs3-2_AEFBC26QcPcCGr2X2NQ9dPIOD_n28NZiSDZq8OA8ICJn58UkFXvoWcW_M-OXRBQLni7cEMI5h90Oon5VcUHgevuI3mD_pOYaNCajgdR1iRejeaRRhmRHlwEqisJ5y7FTEslJYpHgTiX_QQSJspTc1FNb8-XHIwAsmnGko_ZmHFqogMQkEoxILSZUhw4ux7VM1D4loFgGElqk0hNY9Su4xHL4RsLkKZ5VKAj5kFs0KmfSqG9Y="
TG_API_ID = 28745328
TG_API_HASH = "99b7d5e0faedd6ddae2ebb8d792a763c"
BOT_USERNAME = "EnergyGram_robot"

# Конфиг почты
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'swoolwh@gmail.com'
app.config['MAIL_PASSWORD'] = '22012013Dfd'
mail = Mail(app)

# Исправленная инициализация БД
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  email TEXT UNIQUE NOT NULL,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
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
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Заполните все поля')
            return redirect(url_for('login'))

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and user[3] == hashlib.sha256(password.encode()).hexdigest():
            if user[4]:  # Проверка verified
                session['user'] = username
                return redirect(url_for('dashboard'))
            flash('Подтвердите email')
        else:
            flash('Неверные данные')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not all([email, username, password]):
            flash('Заполните все поля')
            return redirect(url_for('register'))

        code = str(random.randint(100000, 999999))
        expires = datetime.now() + timedelta(minutes=30)
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute(
                "INSERT INTO users (email, username, password_hash, verification_code, code_expires) VALUES (?, ?, ?, ?, ?)",
                (email, username, password_hash, code, expires)
            )
            conn.commit()
            
            # Отправка письма
            msg = Message(
                subject="Подтверждение DarkSearchTool",
                recipients=[email],
                body=f"Ваш код: {code}"
            )
            mail.send(msg)
            
            session['temp_user'] = username
            return redirect(url_for('verify'))
        except sqlite3.IntegrityError:
            flash('Email/username уже заняты')
        except Exception as e:
            flash('Ошибка сервера')
            app.logger.error(f"Ошибка регистрации: {str(e)}")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'temp_user' not in session:
        return redirect(url_for('register'))

    if request.method == 'POST':
        code = request.form.get('code')
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            "UPDATE users SET verified = 1 WHERE username = ? AND verification_code = ? AND code_expires > datetime('now')",
            (session['temp_user'], code)
        )
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
    return render_template('dashboard.html', username=session['user'])

@app.route('/api/search', methods=['POST'])
def api_search():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    if not data or 'type' not in data or 'query' not in data:
        return jsonify({"error": "Invalid request"}), 400

    try:
        with TelegramClient(StringSession(TG_SESSION), TG_API_ID, TG_API_HASH) as client:
            # Отправка команды боту
            if data['type'] == 'phone':
                message = f"/search_phone {data['query']}"
            elif data['type'] == 'username':
                message = f"/search_username {data['query']}"
            else:
                return jsonify({"error": "Invalid type"}), 400

            client(SendMessageRequest(
                peer=BOT_USERNAME,
                message=message
            ))
            
            # Получение ответа
            messages = client.get_messages(BOT_USERNAME, limit=1)
            return jsonify({
                "status": "success",
                "result": messages[0].message
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
