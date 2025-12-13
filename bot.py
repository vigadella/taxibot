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

    return (
        "📊 <b>Твоя статистика</b>\n\n"
        f"⏱ Онлайн: <b>{online:.2f}</b> / {LIMIT_HOURS} ч\n"
        f"⏳ Осталось: <b>{max(0, LIMIT_HOURS - online):.2f}</b> ч\n\n"
        f"💰 Заработано: <b>{u['earned']} ₸</b>\n"
        f"🚗 Аренда: <b>{RENT} ₸</b>\n"
        f"❗ До аренды: <b>{max(0, RENT - u['earned'])} ₸</b>"
    )


def stats_kb():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh"),
        telebot.types.InlineKeyboardButton("🛑 Закончить смену", callback_data="stop")
    )
    return kb


@bot.message_handler(commands=["start"])
def start(m):
    get_user(m.chat.id)
    bot.send_message(
        m.chat.id,
        "🚖 Бот готов к работе",
        reply_markup=main_menu()
    )


@bot.message_handler(func=lambda m: m.text == "🟢 Начать смену")
def start_shift(m):
    u = get_user(m.chat.id)

    if u["shift"]:
        bot.send_message(m.chat.id, "⚠️ Смена уже идёт")
        return

    u["shift"] = time.time()
    u["n1"] = u["n30"] = u["n10"] = 0
    update_user(m.chat.id, u)

    bot.send_message(m.chat.id, "🟢 Смена началась")


@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def show_stats(m):
    u = get_user(m.chat.id)
    bot.send_message(
        m.chat.id,
        stats_text(u),
        parse_mode="HTML",
        reply_markup=stats_kb()
    )


@bot.callback_query_handler(func=lambda c: c.data == "refresh")
def refresh(c):
    u = get_user(c.message.chat.id)
    bot.edit_message_text(
        stats_text(u),
        c.message.chat.id,
        c.message.message_id,
        parse_mode="HTML",
        reply_markup=stats_kb()
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