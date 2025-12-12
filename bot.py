from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler

# Токен бота
TOKEN = "8247364713:AAG7jB2Y4zqn81j6Y7Sawo_fpLAb4I6CL6w"

# Главное меню
def main_menu_markup():
    keyboard = [
        [InlineKeyboardButton("📊 Моя статистика", callback_data='stats')],
        [InlineKeyboardButton("🕒 Время на линии", callback_data='time_on_line')],
        [InlineKeyboardButton("💰 Заработок", callback_data='income')],
        [InlineKeyboardButton("🚗 Аренда", callback_data='rent')],
        [InlineKeyboardButton("🧾 Отчёты по заказам", callback_data='orders')],
        [InlineKeyboardButton("⚙ Настройки", callback_data='settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update, context):
    await update.message.reply_text("Выберите действие:", reply_markup=main_menu_markup())

# Обработка нажатий
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'stats':
        stats_text = (
            "📊 Твоя статистика за сегодня:\n"
            "— Онлайн: 4ч 12м / 12ч\n"
            "— Осталось: 7ч 48м\n"
            "— Заработано: 15 560 ₸\n"
            "— До аренды осталось: 6 630 ₸\n"
            "— Чистыми: -6 630 ₸"
        )
        await query.edit_message_text(text=stats_text, reply_markup=main_menu_markup())
    else:
        await query.edit_message_text(text=f"Вы нажали: {query.data}", reply_markup=main_menu_markup())

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()