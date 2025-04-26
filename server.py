from flask import Flask, request, jsonify
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
import os
import hashlib

app = Flask(__name__)

# Конфиг Telegram (замените на свои данные)
TG_SESSION = "1ApWapzMBuzlg5kbC1qweYA5ZT3MSHLcQB5PioEv0svE5RXgmdYRJFOCucCd9Bes_iGkb7pjLsqroPbht67tP6AyluObcfvut7fGBCC__xcs3-2_AEFBC26QcPcCGr2X2NQ9dPIOD_n28NZiSDZq8OA8ICJn58UkFXvoWcW_M-OXRBQLni7cEMI5h90Oon5VcUHgevuI3mD_pOYaNCajgdR1iRejeaRRhmRHlwEqisJ5y7FTEslJYpHgTiX_QQSJspTc1FNb8-XHIwAsmnGko_ZmHFqogMQkEoxILSZUhw4ux7VM1D4loFgGElqk0hNY9Su4xHL4RsLkKZ5VKAj5kFs0KmfSqG9Y="  # Ваша строка сессии
TG_API_ID = 28745328            # Ваш API ID
TG_API_HASH = "99b7d5e0faedd6ddae2ebb8d792a763c"   # Ваш API HASH

# Простая "база данных" пользователей
USERS = {
    "admin": hashlib.sha256(b"password123").hexdigest()  # Логин: хеш пароля
}

def telegram_search(search_type, query):
    """Поиск через Telegram UserBot"""
    with TelegramClient(StringSession(TG_SESSION), TG_API_ID, TG_API_HASH) as client:
        try:
            if search_type == "phone":
                # Логика поиска по номеру
                result = client.get_entity(query)
                return {
                    "id": result.id,
                    "username": result.username,
                    "phone": result.phone
                }
            elif search_type == "username":
                # Логика поиска по юзернейму
                result = client.get_entity(query)
                return {
                    "id": result.id,
                    "username": result.username,
                    "phone": getattr(result, 'phone', None)
                }
        except Exception as e:
            print(f"Ошибка поиска: {str(e)}")
            return None

@app.route('/api/search', methods=['POST'])
def search():
    # Проверка авторизации
    auth_token = request.headers.get('X-Auth-Token')
    if auth_token not in USERS.values():
        return jsonify({"error": "Unauthorized"}), 403
    
    # Обработка запроса
    data = request.json
    result = telegram_search(data['type'], data['query'])
    
    if result:
        return jsonify({"status": "success", "data": result})
    return jsonify({"status": "not_found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
