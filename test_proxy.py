# test_proxy.py — обновленная версия с несколькими прокси

import requests
from config import BOT_TOKEN

# Список прокси для проверки (попробуйте каждый)
PROXY_LIST = [
    "45.15.158.42:8080",
    "185.217.1.53:3128",
    "194.67.213.213:8080",
    "188.166.24.77:3128",
    "45.140.146.209:8080",
    "45.155.68.129:8080",
]

def test_proxy(proxy_address):
    """Проверяет один прокси"""
    proxies = {
        'http': f'http://{proxy_address}',
        'https': f'http://{proxy_address}',
    }
    
    try:
        print(f"🔍 Проверяем: {proxy_address}")
        
        # Проверяем подключение к Telegram
        response = requests.get(
            'https://api.telegram.org',
            proxies=proxies,
            timeout=10
        )
        
        if response.status_code == 200:
            # Проверяем бота
            test_url = f'https://api.telegram.org/bot{BOT_TOKEN}/getMe'
            response2 = requests.get(test_url, proxies=proxies, timeout=10)
            
            if response2.status_code == 200:
                print(f"✅✅✅ ПРОКСИ РАБОТАЕТ! Используйте: {proxy_address}")
                print(f"Ответ бота: {response2.json()}")
                return True, proxy_address
            else:
                print(f"❌ Бот не отвечает: {response2.status_code}")
                return False, None
        else:
            print(f"❌ Статус: {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectTimeout:
        print(f"❌ Таймаут подключения")
        return False, None
    except requests.exceptions.ProxyError as e:
        print(f"❌ Ошибка прокси: {str(e)[:80]}")
        return False, None
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:80]}")
        return False, None

# Проверяем все прокси
print("=" * 50)
print("🔍 НАЧИНАЕМ ПОИСК РАБОЧЕГО ПРОКСИ...")
print("=" * 50)

for proxy in PROXY_LIST:
    success, working_proxy = test_proxy(proxy)
    if success:
        print("\n" + "=" * 50)
        print(f"🎉 НАЙДЕН РАБОЧИЙ ПРОКСИ: {working_proxy}")
        print("=" * 50)
        break
else:
    print("\n❌ Ни один прокси не работает. Нужно найти другие.")