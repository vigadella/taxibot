import telebot
import time
import os
import sqlite3
import threading

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

RENT = 22190
LIMIT_HOURS = 12

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    shift_start REAL,
    earned INTEGER,
    notified_1h INTEGER,
    notified_30m INTEGER,
    notified_10m INTEGER
)
""")
conn.commit()


def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cursor.fetchone()

    if not u:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, 0, 0, 0)",
            (uid, None, 0)
        )
        conn.commit()
        return {"shift": None, "earned": 0, "n1": 0, "n30": 0, "n10": 0}

    return {
        "shift": u[1],
        "earned": u[2],
        "n1": u[3],
        "n30": u[4],
        "n10": u[5]
    }


def update_user(uid, u):
    cursor.execute("""
        UPDATE users
        SET shift_start=?, earned=?, notified_1h=?, notified_30m=?, notified_10m=?
        WHERE user_id=?
    """, (u["shift"], u["earned"], u["n1"], u["n30"], u["n10"], uid))
    conn.commit()


def main_menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🟢 Начать смену", "📊 Статистика")
    kb.add("💰 Добавить доход")
    return kb


def stats_text(u):
    online = 0
    if u["shift"]:
        online = (time.time() - u["shift"]) / 3600

    earned = u["earned"]
    left_hours = max(0, LIMIT_HOURS - online)

    income_per_hour = earned / online if online > 0 else 0
    forecast = earned + income_per_hour * left_hours

    net_income = earned - RENT
    forecast_net = forecast - RENT

    окупился = "✅ Да" if earned >= RENT else "❌ Нет"

    return (
        "📊 <b>Финансовая статистика</b>\n\n"

        f"⏱ Онлайн: <b>{online:.2f}</b> ч / {LIMIT_HOURS}\n"
        f"⏳ Осталось: <b>{left_hours:.2f}</b> ч\n\n"

        f"💰 Заработано: <b>{earned} ₸</b>\n"
        f"💵 В час: <b>{income_per_hour:.0f} ₸</b>\n\n"

        f"🚗 Аренда: <b>{RENT} ₸</b>\n"
        f"📉 Чистыми сейчас: <b>{net_income} ₸</b>\n"
        f"📈 Прогноз чистыми: <b>{forecast_net:.0f} ₸</b>\n\n"

        f"🔮 Прогноз до конца смены: <b>{forecast:.0f} ₸</b>\n"
        f"🏁 Аренда отбита: <b>{окупился}</b>"
    )

@bot.callback_query_handler(func=lambda c: c.data == "stop")
def stop(c):
    u = get_user(c.message.chat.id)

    if not u["shift"]:
        bot.answer_callback_query(c.id, "Смена не идёт")
        return

    hours = (time.time() - u["shift"]) / 3600
    u["shift"] = None
    update_user(c.message.chat.id, u)

    bot.edit_message_text(
        f"🛑 Смена завершена\n⏱ {hours:.2f} ч",
        c.message.chat.id,
        c.message.message_id
    )


@bot.message_handler(func=lambda m: m.text == "💰 Добавить доход")
def income(m):
    msg = bot.send_message(m.chat.id, "Введи сумму в ₸:")
    bot.register_next_step_handler(msg, save_income)


def save_income(m):
    u = get_user(m.chat.id)
    try:
        u["earned"] += int(m.text)
        update_user(m.chat.id, u)
        bot.send_message(m.chat.id, "✅ Доход добавлен")
    except:
        bot.send_message(m.chat.id, "❌ Введи число")


def notifier():
    while True:
        cursor.execute("SELECT user_id FROM users WHERE shift_start IS NOT NULL")
        for (uid,) in cursor.fetchall():
            u = get_user(uid)
            online = (time.time() - u["shift"]) / 3600
            left = LIMIT_HOURS - online

            if left <= 1 and not u["n1"]:
                bot.send_message(uid, "🔔 Остался 1 час")
                u["n1"] = 1

            if left <= 0.5 and not u["n30"]:
                bot.send_message(uid, "⚠️ Осталось 30 минут")
                u["n30"] = 1

            if left <= 0.17 and not u["n10"]:
                bot.send_message(uid, "🚨 Осталось 10 минут!")
                u["n10"] = 1

            update_user(uid, u)

        time.sleep(60)


threading.Thread(target=notifier, daemon=True).start()
bot.polling(none_stop=True)

# === ДОБАВЛЕНО: ЯНДЕКС-ПОДГОТОВКА ===
# ❗ Без логинов и паролей

import telebot
import time
import os
import sqlite3
import threading

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

RENT = 22190
LIMIT_HOURS = 12

conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    shift_start REAL,
    earned INTEGER,
    yandex_id TEXT,
    notified_1h INTEGER,
    notified_30m INTEGER,
    notified_10m INTEGER
)
""")
conn.commit()


def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cursor.fetchone()

    if not u:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, 0, 0, 0)",
            (uid, None, 0, None)
        )
        conn.commit()
        return {"shift": None, "earned": 0, "yandex": None, "n1": 0, "n30": 0, "n10": 0}

    return {
        "shift": u[1],
        "earned": u[2],
        "yandex": u[3],
        "n1": u[4],
        "n30": u[5],
        "n10": u[6]
    }


def update_user(uid, u):
    cursor.execute("""
        UPDATE users
        SET shift_start=?, earned=?, yandex_id=?,
            notified_1h=?, notified_30m=?, notified_10m=?
        WHERE user_id=?
    """, (u["shift"], u["earned"], u["yandex"], u["n1"], u["n30"], u["n10"], uid))
    conn.commit()