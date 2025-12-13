import telebot
import time
import os
import sqlite3
import threading

# ================== НАСТРОЙКИ ==================
TOKEN = os.getenv("BOT_TOKEN")

RENT = 22190          # аренда
LIMIT_HOURS = 12     # лимит часов

bot = telebot.TeleBot(TOKEN)

# ================== БАЗА ДАННЫХ ==================
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


# ================== ВСПОМОГАТЕЛЬНОЕ ==================
def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, 0, 0, 0)",
            (uid, None, 0)
        )
        conn.commit()
        return {
            "shift": None,
            "earned": 0,
            "n1": 0,
            "n30": 0,
            "n10": 0
        }

    return {
        "shift": row[1],
        "earned": row[2],
        "n1": row[3],
        "n30": row[4],
        "n10": row[5]
    }


def save_user(uid, u):
    cursor.execute("""
        UPDATE users
        SET shift_start = ?, earned = ?, 
            notified_1h = ?, notified_30m = ?, notified_10m = ?
        WHERE user_id = ?
    """, (u["shift"], u["earned"], u["n1"], u["n30"], u["n10"], uid))
    conn.commit()


# ================== МЕНЮ ==================
def main_menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🟢 Начать смену", "📊 Статистика")
    kb.add("💰 Добавить доход")
    return kb


def stats_keyboard():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(
        telebot.types.InlineKeyboardButton("🔄 Обновить", callback_data="refresh"),
        telebot.types.InlineKeyboardButton("🛑 Закончить смену", callback_data="stop")
    )
    return kb


# ================== ТЕКСТ СТАТИСТИКИ ==================
def stats_text(u):
    online = 0
    if u["shift"]:
        online = (time.time() - u["shift"]) / 3600

    left_hours = max(0, LIMIT_HOURS - online)
    earned = u["earned"]

    income_per_hour = earned / online if online > 0 else 0
    forecast = earned + income_per_hour * left_hours

    net_now = earned - RENT
    net_forecast = forecast - RENT

    paid = "✅ Да" if earned >= RENT else "❌ Нет"

    return (
        "📊 <b>Финансовая статистика</b>\n\n"
        f"⏱ Онлайн: <b>{online:.2f}</b> ч / {LIMIT_HOURS}\n"
        f"⏳ Осталось: <b>{left_hours:.2f}</b> ч\n\n"
        f"💰 Заработано: <b>{earned} ₸</b>\n"
        f"💵 В час: <b>{income_per_hour:.0f} ₸</b>\n\n"
        f"🚗 Аренда: <b>{RENT} ₸</b>\n"
        f"📉 Чистыми сейчас: <b>{net_now} ₸</b>\n"
        f"📈 Прогноз чистыми: <b>{net_forecast:.0f} ₸</b>\n\n"
        f"🔮 Прогноз до конца смены: <b>{forecast:.0f} ₸</b>\n"
        f"🏁 Аренда отбита: <b>{paid}</b>"
    )


# ================== ХЭНДЛЕРЫ ==================
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
    u = get_user(message.chat.id)

    if u["shift"]:
        bot.send_message(message.chat.id, "⚠️ Смена уже идёт")
        return

    u["shift"] = time.time()
    u["n1"] = u["n30"] = u["n10"] = 0
    save_user(message.chat.id, u)

    bot.send_message(message.chat.id, "🟢 Смена началась!")


@bot.message_handler(func=lambda m: m.text == "💰 Добавить доход")
def add_income(message):
    msg = bot.send_message(message.chat.id, "Введи сумму дохода в ₸:")
    bot.register_next_step_handler(msg, save_income)


def save_income(message):
    u = get_user(message.chat.id)
    try:
        amount = int(message.text)
        u["earned"] += amount
        save_user(message.chat.id, u)
        bot.send_message(message.chat.id, "✅ Доход добавлен")
    except:
        bot.send_message(message.chat.id, "❌ Введи число")


@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def show_stats(message):
    u = get_user(message.chat.id)
    bot.send_message(
        message.chat.id,
        stats_text(u),
        parse_mode="HTML",
        reply_markup=stats_keyboard()
    )


@bot.callback_query_handler(func=lambda c: c.data == "refresh")
def refresh_stats(c):
    u = get_user(c.message.chat.id)
    bot.edit_message_text(
        stats_text(u),
        c.message.chat.id,
        c.message.message_id,
        parse_mode="HTML",
        reply_markup=stats_keyboard()
    )


@bot.callback_query_handler(func=lambda c: c.data == "stop")
def stop_shift(c):
    u = get_user(c.message.chat.id)

    if not u["shift"]:
        bot.answer_callback_query(c.id, "Смена не идёт")
        return

    hours = (time.time() - u["shift"]) / 3600
    u["shift"] = None
    save_user(c.message.chat.id, u)

    bot.edit_message_text(
        f"🛑 Смена завершена\n⏱ Отработано: {hours:.2f} ч",
        c.message.chat.id,
        c.message.message_id
    )


# ================== УВЕДОМЛЕНИЯ ==================
def notifier():
    while True:
        cursor.execute("SELECT user_id FROM users WHERE shift_start IS NOT NULL")
        ids = cursor.fetchall()

        for (uid,) in ids:
            u = get_user(uid)
            online = (time.time() - u["shift"]) / 3600
            left = LIMIT_HOURS - online

            if left <= 1 and not u["n1"]:
                bot.send_message(uid, "🔔 Остался 1 час до лимита")
                u["n1"] = 1

            if left <= 0.5 and not u["n30"]:
                bot.send_message(uid, "⚠️ Осталось 30 минут")
                u["n30"] = 1

            if left <= 0.17 and not u["n10"]:
                bot.send_message(uid, "🚨 Осталось 10 минут! Срочно заверши смену.")
                u["n10"] = 1

            save_user(uid, u)

        time.sleep(60)


threading.Thread(target=notifier, daemon=True).start()

# ================== ЗАПУСК ==================
bot.polling(none_stop=True)