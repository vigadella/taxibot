import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Бот работает! 🚖")

bot.polling(none_stop=True)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackQueryHandler, CommandHandler, JobQueue
import config, utils

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

def start(update, context):
    update.message.reply_text("Выберите действие:", reply_markup=main_menu_markup())

def button_handler(update, context):
    query = update.callback_query
    query.answer()
    
    if query.data == 'stats':
        query.edit_message_text(text=utils.get_stats(), reply_markup=main_menu_markup())
    else:
        query.edit_message_text(text=f"Вы нажали: {query.data}", reply_markup=main_menu_markup())

def auto_update(context):
    # Автообновление — можно отправлять сообщение администратору или пользователю
    chat_id = 8247364713:AAG7jB2Y4zqn81j6Y7Sawo_fpLAb4I6CL6w  # замените на ваш chat_id
    context.bot.send_message(chat_id=chat_id, text=utils.get_stats())

def main():
    updater = Updater(config.TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем автообновление каждые UPDATE_INTERVAL секунд
    job_queue = updater.job_queue
    job_queue.run_repeating(auto_update, interval=config.UPDATE_INTERVAL, first=10)
    
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()