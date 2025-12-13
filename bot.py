import telebot
import time
import os

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# ===== ХРАНИЛИЩЕ (пока в памяти) =====
users = {}

RENT = 22190          # аренда в тенге
LIMIT_HOURS = 12     # лимит часов


def get_user(uid):
    if uid not in users:
        users[uid] = {
            "shift_start": None,
            "earned": 0
        }
    return users[uid]


def main_menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🟢 Начать смену")
    kb.add("🛑 Закончить смену")
    kb.add("💰 Добавить доход")
    kb.add("📊 Моя статистика")
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    get_user(message.chat.id)
    bot.send_message(
        message.chat.id,
        "🚖 Привет! Я твой помощник таксиста.\n\nВыбери действие 👇",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🟢 Начать смену")
def start_shift(message):
    user = get_user(message.chat.id)

    if user["shift_start"]:
        bot.send_message(message.chat.id, "⚠️ Смена уже идёт")
        return

    user["shift_start"] = time.time()
    bot.send_message(message.chat.id, "🟢 Смена началась! Удачной дороги 🚗")


@bot.message_handler(func=lambda m: m.text == "🛑 Закончить смену")
def stop_shift(message):
    user = get_user(message.chat.id)

    if not user["shift_start"]:
        bot.send_message(message.chat.id, "⚠️ Смена ещё не начата")
        return

    hours = (time.time() - user["shift_start"]) / 3600
    user["shift_start"] = None

    bot.send_message(
        message.chat.id,
        f"🛑 Смена завершена\n⏱ Отработано: {hours:.2f} ч"
    )


@bot.message_handler(func=lambda m: m.text == "💰 Добавить доход")
def ask_income(message):
    msg = bot.send_message(message.chat.id, "Введи сумму дохода в ₸:")
    bot.register_next_step_handler(msg, save_income)


def save_income(message):
    user = get_user(message.chat.id)

    try:
        amount = int(message.text)
        user["earned"] += amount
        bot.send_message(message.chat.id, f"✅ Добавлено {amount} ₸")
    except:
        bot.send_message(message.chat.id, "❌ Введи число")


@bot.message_handler(func=lambda m: m.text == "📊 Моя статистика")
def stats(message):
    user = get_user(message.chat.id)

    if user["shift_start"]:
        online = (time.time() - user["shift_start"]) / 3600
    else:
        online = 0

    left_hours = max(0, LIMIT_HOURS - online)
    left_rent = max(0, RENT - user["earned"])

    text = (
        "📊 Твоя статистика:\n\n"
        f"⏱ Онлайн: {online:.2f} ч / {LIMIT_HOURS} ч\n"
        f"⏳ Осталось: {left_hours:.2f} ч\n\n"
        f"💰 Заработано: {user['earned']} ₸\n"
        f"🚗 Аренда: {RENT} ₸\n"
        f"❗ До аренды осталось: {left_rent} ₸"
    )

    bot.send_message(message.chat.id, text)


bot.polling(none_stop=True)