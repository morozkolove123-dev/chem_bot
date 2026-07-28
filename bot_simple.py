# bot_simple.py - Версия с pytelegrambotapi (без компиляции!)

import telebot
from telebot import apihelper
import easyocr
import re
import logging
from config import BOT_TOKEN
# ===== ПРОВЕРКА ТОКЕНА =====
print(f"🔍 Проверяем токен: {BOT_TOKEN[:10]}...")
if not BOT_TOKEN or len(BOT_TOKEN) < 30:
    print("❌ ОШИБКА: Токен слишком короткий или пустой!")
    print("Проверьте config.py")
    exit()
# ============================

# Если используете Cloudflare Worker (раскомментируйте если нужно)
# apihelper.API_URL = "https://ваш-worker.workers.dev"

bot = telebot.TeleBot(BOT_TOKEN)


# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализируем EasyOCR
print("⏳ Загрузка OCR моделей... Это может занять 1-2 минуты")
reader = easyocr.Reader(['ru', 'en'], gpu=False)
print("✅ OCR модели загружены!")

# ========== БАЗА ДЛЯ АНАЛИЗА ==========

PLAGIARISM_PATTERNS = [
    r"рассмотрим реакцию.*на примере",
    r"как видно из уравнения",
    r"согласно закону сохранения массы",
    r"википедия сообщает",
    r"моль.*атомов",
    r"в интернете можно найти",
    r"готовое домашнее задание",
]

TOPICS = {
    "Кислоты и основания": ["H2SO4", "HCl", "HNO3", "PH", "нейтрализация", "щелочь"],
    "Органическая химия": ["CH4", "C2H5OH", "бензол", "алканы", "алкины", "спирты"],
    "ОВР (окисление-восстановление)": ["степень окисления", "ОВР", "электроны", "восстановитель", "окислитель"],
    "Химическая кинетика": ["скорость реакции", "катализатор", "концентрация"],
    "Растворы": ["молярность", "нормальность", "растворимость", "массовая доля"],
}

STUDY_LINKS = {
    "Кислоты и основания": "📘 https://foxford.ru/wiki/himiya/kisloty-i-osnovaniya",
    "Органическая химия": "🧪 https://www.youtube.com/watch?v=uFjRI8AtgXk",
    "ОВР (окисление-восстановление)": "⚡ https://chemege.ru/ovr/",
    "Химическая кинетика": "⏱️ https://chemistry.ru/kinetics/",
    "Растворы": "💧 https://ru.wikipedia.org/wiki/Раствор",
}

# ========== ФУНКЦИИ ==========

def analyze_text(text):
    """Анализирует текст на списывание и определяет темы"""
    text_lower = text.lower()
    
    # Проверка на списывание
    plag_score = 0
    for pattern in PLAGIARISM_PATTERNS:
        if re.search(pattern, text_lower):
            plag_score += 1
    
    is_plagiarized = plag_score >= 2
    
    # Определение тем
    strong_topics = []
    weak_topics = []
    
    for topic, keywords in TOPICS.items():
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        total = len(keywords)
        
        if found >= total * 0.5:
            strong_topics.append(topic)
        elif found > 0:
            weak_topics.append(topic)
    
    if len(text.split()) < 15:
        weak_topics = ["Недостаточно данных для анализа"]
    
    if not strong_topics and not weak_topics:
        weak_topics = ["Требуется более детальный текст"]
    
    return {
        "plagiarism": is_plagiarized,
        "strong": strong_topics if strong_topics else ["Темы не определены"],
        "weak": weak_topics if weak_topics else ["Отличная работа!"]
    }

def get_study_materials(weak_topics):
    """Генерирует рекомендации по слабым темам"""
    if weak_topics == ["Отличная работа!"]:
        return "🎉 Отлично! Продолжайте в том же духе!"
    
    result = "📚 **Рекомендую повторить:**\n\n"
    for topic in weak_topics:
        found = False
        for key, link in STUDY_LINKS.items():
            if key.lower() in topic.lower() or topic.lower() in key.lower():
                result += f"• **{key}**: {link}\n"
                found = True
                break
        if not found:
            result += f"• **{topic}**: Повторите в учебнике химии (Рудзитис, 8-9 класс)\n"
    
    result += "\n🔍 **Полезные ресурсы:**\n"
    result += "• YouTube: канал 'Химия просто'\n"
    result += "• Сайт: chemport.ru"
    return result

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 
        "🧪 **Хим-Репетитор**\n\n"
        "Я помогу вам разобраться с домашней работой по химии.\n\n"
        "**Что я умею:**\n"
        "📸 Анализировать фото ваших работ\n"
        "🔍 Проверять на списывание\n"
        "📊 Определять сильные и слабые темы\n"
        "📚 Давать материалы для изучения\n\n"
        "**Как использовать:**\n"
        "Просто отправьте мне **фото** вашей контрольной, теста или ДЗ.\n\n"
        "⚠️ Четкость фото влияет на качество распознавания!"
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Отправляем сообщение о начале
    msg = bot.reply_to(message, "🔬 Анализирую вашу работу...\n⏳ Распознаю текст (это займет 10-20 секунд)")
    
    try:
        # 1. Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # 2. Распознаем текст
        result = reader.readtext(downloaded_file, detail=0, paragraph=True)
        recognized_text = " ".join(result)
        
        if not recognized_text or len(recognized_text.strip()) < 5:
            bot.edit_message_text(
                "❌ Не удалось распознать текст на фото.\n\n"
                "📸 **Советы:**\n"
                "• Сделайте фото при хорошем освещении\n"
                "• Сфотографируйте текст крупным планом\n"
                "• Убедитесь, что текст написан разборчиво",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
            return
        
        # 3. Показываем распознанный текст
        preview = recognized_text[:500] + "..." if len(recognized_text) > 500 else recognized_text
        bot.edit_message_text(
            f"📝 **Распознанный текст:**\n```\n{preview}\n```",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode='Markdown'
        )
        
        # 4. Анализируем текст
        analysis = analyze_text(recognized_text)
        
        # 5. Формируем отчет
        plag_status = "🚨 **ВНИМАНИЕ: Обнаружены признаки списывания!**" if analysis["plagiarism"] else "✅ **Оригинальная работа.**"
        
        strong_text = "💪 **Сильные темы:**\n" + "\n".join([f"• {t}" for t in analysis["strong"]])
        weak_text = "⚠️ **Нужно подтянуть:**\n" + "\n".join([f"• {t}" for t in analysis["weak"]])
        
        full_report = f"{plag_status}\n\n{strong_text}\n\n{weak_text}"
        
        # Добавляем материалы
        if analysis["weak"] and "Недостаточно" not in str(analysis["weak"]):
            materials = get_study_materials(analysis["weak"])
            full_report += f"\n\n{materials}"
        
        # Отправляем отчет
        bot.send_message(message.chat.id, full_report, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        bot.edit_message_text(
            f"❌ Произошла ошибка: {str(e)[:150]}",
            chat_id=message.chat.id,
            message_id=msg.message_id
        )

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    bot.reply_to(message, 
        "📸 Отправьте мне **фото** вашей работы по химии.\n"
        "Я умею анализировать только изображения."
    )

# ========== ЗАПУСК БОТА ==========

print("🚀 Бот запускается...")
print("✅ Бот готов к работе!")
bot.infinity_polling()