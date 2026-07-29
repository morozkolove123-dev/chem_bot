import telebot
import logging
import os
import re
import io
from PIL import Image
import pytesseract

# Настройка
logging.basicConfig(level=logging.INFO)

# Токен из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# Ваша база для проверки на списывание (можно оставить как есть)
PLAGIARISM_PATTERNS = [
    r"рассмотрим реакцию.*на примере",
    r"как видно из уравнения",
    r"согласно закону сохранения массы",
    r"википедия сообщает",
    r"моль.*атомов",
]

TOPICS = {
    "Кислоты и основания": ["H2SO4", "HCl", "HNO3", "PH", "нейтрализация"],
    "Органическая химия": ["CH4", "C2H5OH", "бензол", "алканы"],
    "ОВР": ["степень окисления", "ОВР", "электроны", "восстановитель"],
}

def analyze_text(text):
    text_lower = text.lower()
    plag_score = 0
    for pattern in PLAGIARISM_PATTERNS:
        if re.search(pattern, text_lower):
            plag_score += 1
    is_plagiarized = plag_score >= 2

    strong_topics = []
    weak_topics = []
    for topic, keywords in TOPICS.items():
        found = sum(1 for kw in keywords if kw.lower() in text_lower)
        if found >= len(keywords) * 0.5:
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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message,
        "🧪 Хим-Репетитор!\n\nОтправьте фото вашей работы по химии, и я проанализирую её."
    )

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    msg = bot.reply_to(message, "🔬 Анализирую... Распознаю текст...")
    try:
        # Скачиваем фото
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Распознаем текст через Tesseract
        image = Image.open(io.BytesIO(downloaded_file))
        recognized_text = pytesseract.image_to_string(image, lang='rus+eng')

        if not recognized_text or len(recognized_text.strip()) < 5:
            bot.edit_message_text("❌ Не удалось распознать текст. Сделайте фото четче.",
                chat_id=message.chat.id, message_id=msg.message_id)
            return

        # Анализируем текст
        analysis = analyze_text(recognized_text)
        plag_status = "🚨 Обнаружены признаки списывания!" if analysis["plagiarism"] else "✅ Оригинальная работа."
        strong_text = "💪 Сильные темы:\n" + "\n".join([f"• {t}" for t in analysis["strong"]])
        weak_text = "⚠️ Нужно подтянуть:\n" + "\n".join([f"• {t}" for t in analysis["weak"]])

        report = f"{plag_status}\n\n{strong_text}\n\n{weak_text}"
        bot.send_message(message.chat.id, report)

    except Exception as e:
        bot.edit_message_text(f"❌ Ошибка: {str(e)[:100]}",
            chat_id=message.chat.id, message_id=msg.message_id)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    bot.reply_to(message, "📸 Отправьте фото вашей работы.")

print("🚀 Бот запущен!")
bot.infinity_polling()