import telebot
import time
import os
import sqlite3
import threading

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

RENT = 22190
LIMIT_HOURS = 0.1

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    shift_start REAL,
    earned INTEGER,
    notified_1h INTEGER DEFAULT 0,
    notified_30m INTEGER DEFAULT 0,
    notified_10m INTEGER DEFAULT 0
)
""")
conn.commit()


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, 0, 0, 0)",
            (user_id, None, 0)
        )
        conn.commit()
        return {
            "shift_start": None,
            "earned": 0,
            "n1": 0, "n30": 0, "n10": 0
        }

    return {
        "shift_start": user[1],
        "earned": user[2],
        "n1": user[3],
        "n30": user[4],
        "n10": user[5]
    }


def update_user(user_id, user):
    cursor.execute("""
        UPDATE users
        SET shift_start=?, earned=?, notified_1h=?, notified_30m=?, notified_10m=?
        WHERE user_id=?
    """, (
        user["shift_start"], user["earned"],
        user["n1"], user["n30"], user["n10"],
        user_id
    ))
    conn.commit()


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
        "🚖 Бот активен.\n🔔 Уведомления по времени включены.",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🟢 Начать смену")
def start_shift(message):
    user = get_user(message.chat.id)

    if user["shift_start"]:
        bot.send_message(message.chat.id, "⚠️ Смена уже идёт")
        return

    user["shift_start"] = time.time()
    user["n1"] = user["n30"] = user["n10"] = 0
    update_user(message.chat.id, user)

    bot.send_message(message.chat.id, "🟢 Смена началась!")


@bot.message_handler(func=lambda m: m.text == "🛑 Закончить смену")
def stop_shift(message):
    user = get_user(message.chat.id)

    if not user["shift_start"]:
        bot.send_message(message.chat.id, "⚠️ Смена не начата")
        return

    hours = (time.time() - user["shift_start"]) / 3600
    user["shift_start"] = None
    update_user(message.chat.id, user)

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
        update_user(message.chat.id, user)
        bot.send_message(message.chat.id, f"✅ Добавлено {amount} ₸")
    except:
        bot.send_message(message.chat.id, "❌ Введи число")


@bot.message_handler(func=lambda m: m.text == "📊 Моя статистика")
def stats(message):
    user = get_user(message.chat.id)

    online = 0
    if user["shift_start"]:
        online = (time.time() - user["shift_start"]) / 3600

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


# ===== ФОНОВАЯ ПРОВЕРКА ВРЕМЕНИ =====
def notifier():
    while True:
        cursor.execute("SELECT user_id FROM users WHERE shift_start IS NOT NULL")
        users_ids = cursor.fetchall()

        for (uid,) in users_ids:
            user = get_user(uid)
            online = (time.time() - user["shift_start"]) / 3600
            left = LIMIT_HOURS - online

            if left <= 1 and not user["n1"]:
                bot.send_message(uid, "🔔 Остался 1 час до лимита!")
                user["n1"] = 1

            if left <= 0.5 and not user["n30"]:
                bot.send_message(uid, "⚠️ Осталось 30 минут!")
                user["n30"] = 1

            if left <= 0.17 and not user["n10"]:
                bot.send_message(uid, "🚨 Осталось 10 минут! Срочно заверши смену.")
                user["n10"] = 1

            update_user(uid, user)

        time.sleep(60)


threading.Thread(target=notifier, daemon=True).start()

bot.polling(none_stop=True)