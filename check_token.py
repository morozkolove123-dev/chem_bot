# check_token.py
try:
    from config import BOT_TOKEN
    print(f"✅ Токен загружен: {BOT_TOKEN[:10]}...")
    print(f"Длина токена: {len(BOT_TOKEN)} символов")
    
    if len(BOT_TOKEN) < 30:
        print("❌ Токен слишком короткий!")
    else:
        print("✅ Длина токена нормальная")
        
except ImportError:
    print("❌ Ошибка: файл config.py не найден!")
except Exception as e:
    print(f"❌ Ошибка: {e}")