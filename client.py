import requests
import getpass
import json

SERVER_URL = "http://DarkSearchTool.onrender.com/api"  # Или ваш Render URL

def login():
    """Аутентификация в системе"""
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    # В реальном проекте используйте HTTPS!
    response = requests.post(
        f"{SERVER_URL}/login",
        json={"username": username, "password": password}
    )
    
    return response.json().get('token')

def search_phone(token):
    """Поиск по номеру телефона"""
    phone = input("Введите номер (+79991234567): ").strip()
    response = requests.post(
        f"{SERVER_URL}/search",
        json={"type": "phone", "query": phone},
        headers={"X-Auth-Token": token}
    )
    print(json.dumps(response.json(), indent=2))

def search_username(token):
    """Поиск по юзернейму"""
    username = input("Введите username (@ или без): ").strip()
    response = requests.post(
        f"{SERVER_URL}/search",
        json={"type": "username", "query": username},
        headers={"X-Auth-Token": token}
    )
    print(json.dumps(response.json(), indent=2))

def main():
    print("DarkSearchTool Console Client")
    token = login()
    
    while True:
        print("\n1. Поиск по номеру")
        print("2. Поиск по username")
        print("3. Выход")
        choice = input("> ")
        
        if choice == "1":
            search_phone(token)
        elif choice == "2":
            search_username(token)
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
