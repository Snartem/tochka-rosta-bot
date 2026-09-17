# Установка библиотек: python3 -m pip install -r requirements.txt
# Запуск: python3 bot.py

import os

import telebot
from dotenv import load_dotenv
from telebot import types

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "")

# Русский, профильная математика, информатика.
# Примеры из ВШЭ — Нижний Новгород. Бюджет, общий конкурс.
# Баллы 2025: https://nnov.hse.ru/bacnn/statist
# Минимумы 2026: https://nnov.hse.ru/bacnn/minpoints
programs = [
    {"name": "Фундаментальная и прикладная математика", "score": 193, "minimum": [55, 65, 50]},
    {"name": "Компьютерные науки и технологии — ПМИ", "score": 256, "minimum": [55, 65, 55]},
    {"name": "Компьютерные науки и технологии — программная инженерия", "score": 265, "minimum": [55, 65, 55]},
    {"name": "Технологии искусственного и дополненного интеллекта", "score": 290, "minimum": [55, 70, 70]},
]
subjects = ["Русский язык", "Профильная математика", "Информатика"]
users = {}
bot = None


def menu():
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons.row("✏️ Мои баллы", "🎓 Подбор")
    buttons.row("➡️ Другой вариант", "💡 Если улучшить баллы")
    buttons.row("📋 Что делать дальше", "ℹ️ О боте")
    return buttons


def send(chat_id, text):
    bot.send_message(chat_id, text, reply_markup=menu())


def new_user():
    # Данные разных людей хранятся отдельно по номеру чата.
    return {"scores": [], "draft": [], "step": -1, "program": 0}


def recommendation(scores, program):
    for i in range(3):
        if scores[i] < program["minimum"][i]:
            return f"Не выполнен минимум: {subjects[i]} — нужно хотя бы {program['minimum'][i]}."
    difference = sum(scores) - program["score"]
    if difference < 0:
        return f"🚀 Амбициозный вариант. До прошлогоднего уровня не хватает {-difference} баллов."
    elif difference < 10:
        return f"🎯 Реалистичный вариант. Ты выше или на уровне прошлого года: запас {difference} баллов."
    else:
        return f"🛟 Вариант с запасом. Твоя сумма выше прошлогодней на {difference} баллов."


def show_program(chat_id, improve=False):
    user = users[chat_id]
    if not user["scores"]:
        send(chat_id, "Сначала нажми «Мои баллы» и заполни три предмета.")
        return
    program = programs[user["program"]]
    scores = user["scores"].copy()
    text = f"🎓 {program['name']}\nВШЭ — Нижний Новгород\n\n"
    if improve:
        # Меняем копию списка, чтобы эксперимент не испортил анкету.
        i = scores.index(min(scores))
        extra = min(10, 100 - scores[i])
        scores[i] += extra
        text += f"Если улучшить {subjects[i].lower()} на {extra} баллов:\n\n"
    text += f"Твоя сумма: {sum(scores)}\nПроходной на бюджет в 2025: {program['score']}\n\n"
    text += recommendation(scores, program)
    text += "\n\nЭто ориентир, а не гарантия поступления.\nНажми «Другой вариант», чтобы посмотреть следующую программу."
    send(chat_id, text)


def handle_message(message):
    if message.chat.type != "private":
        return
    chat_id = message.chat.id
    text = (message.text or "").strip()
    if chat_id not in users:
        users[chat_id] = new_user()
    user = users[chat_id]

    if text in ("/start", "/cancel"):
        user["step"] = -1
        send(chat_id, "Привет! Это «Точка роста».\n\nЯ помогу сравнить баллы для ИТ и математики в нижегородской ВШЭ.\n\nНачни с кнопки «Мои баллы».")
    elif text == "/delete":
        users.pop(chat_id)
        send(chat_id, "Твои данные удалены.")
    elif text == "✏️ Мои баллы":
        user["draft"] = []
        user["step"] = 0
        send(chat_id, "Какой у тебя балл по русскому языку?\n\nВведи число от 0 до 100. Для отмены — /cancel.")
    elif text in ("🎓 Подбор", "➡️ Другой вариант", "💡 Если улучшить баллы"):
        user["step"] = -1
        if text == "🎓 Подбор":
            user["program"] = 0
        elif text == "➡️ Другой вариант":
            user["program"] = (user["program"] + 1) % len(programs)
        show_program(chat_id, improve=text == "💡 Если улучшить баллы")
    elif text == "📋 Что делать дальше":
        user["step"] = -1
        if not user["scores"]:
            first = "Сначала заполни баллы, чтобы сравнить варианты."
        else:
            i = user["scores"].index(min(user["scores"]))
            first = f"Из трёх предметов самый низкий балл: {subjects[i].lower()}. Проверь, поможет ли его улучшение, кнопкой «Если улучшить баллы»."
        send(chat_id, first + "\n\nЗатем выбери программы и проверь документы и сроки своей траектории:\nhttps://nnov.hse.ru/bacnn/information")
    elif text == "ℹ️ О боте":
        user["step"] = -1
        send(chat_id, "Учебный бот для четырёх вариантов обучения в нижегородской ВШЭ.\n\n"
             "Сравнивает три ЕГЭ с баллами 2025. Проверяет минимумы 2026. Для нового года данные нужно обновить.\n\n"
             "Категории: ниже прошлогоднего балла, запас 0–9, запас от 10. Достижения, олимпиады и квоты здесь не учитываются.\n\n"
             "Источник баллов:\nhttps://nnov.hse.ru/bacnn/statist\n\n"
             "Анкета хранится до выключения бота. /delete — удалить её сейчас.")
    elif user["step"] >= 0:
        if not text.isascii() or not text.isdigit() or not 0 <= int(text) <= 100:
            send(chat_id, "Нужно целое число от 0 до 100. Попробуй ещё раз.")
            return
        user["draft"].append(int(text))
        user["step"] += 1
        if user["step"] < 3:
            send(chat_id, f"Теперь предмет: {subjects[user['step']]}.\nКакой балл?")
        else:
            user["scores"] = user["draft"].copy()
            user["step"] = -1
            user["program"] = 0
            send(chat_id, f"Готово! Твоя сумма — {sum(user['scores'])}.\n\nНажми «Подбор», чтобы посмотреть варианты.")
    else:
        send(chat_id, "Выбери действие кнопкой внизу 👇")


if __name__ == "__main__":
    if not TOKEN.strip():
        print("Не найдена переменная BOT_TOKEN. Добавь токен в .env или настройки запуска.")
    else:
        try:
            bot = telebot.TeleBot(TOKEN.strip(), threaded=False)
            bot.register_message_handler(handle_message, content_types=["text"])
            info = bot.get_me()
            if bot.get_webhook_info().url:
                print("У бота настроен webhook. Для этой версии нужен токен бота без webhook.")
            else:
                print(f"Бот @{info.username} запущен. Отправь ему /start.", flush=True)
                bot.polling(non_stop=False)
        except KeyboardInterrupt:
            print("Бот остановлен.")
        except Exception as error:
            print("Не удалось запустить бота. Проверь токен, интернет и закрой старую копию.")
            print("Тип ошибки:", type(error).__name__)
