import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import re

# Ваш API ключ для DeepSeek (если у вас есть)
DEEPSEEK_API_KEY = 'sk-14e5e0afd78a41f696806e6ba2c457fa'
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/query'

# Включим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для общения с DeepSeek API
def get_deepseek_response(query: str):
    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
    }
    data = {
        'query': query,
    }
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('response', 'Не удалось получить ответ')
    else:
        return 'Ошибка запроса к API DeepSeek'

# Функция обработки сообщений
def respond_to_message(update: Update, context: CallbackContext):
    message_text = update.message.text.lower()
    
    # Если сообщение из личного чата
    if update.message.chat.type == 'private':
        response = f"Привет, {update.message.from_user.first_name}! Ты в личном чате. Что ты хочешь узнать?"
        
        # Проверка на имя "Фёдор"
        if 'фёдор' in update.message.from_user.first_name.lower():
            response = "Привет, Фёдор! Чем могу помочь?"

        # Запрос к DeepSeek API
        ai_response = get_deepseek_response(message_text)
        update.message.reply_text(f"{response}\n\nОтвет от AI: {ai_response}")

    # Если сообщение из группы
    elif update.message.chat.type in ['group', 'supergroup']:
        response = "Ты написал в группе! Ожидай ответ от AI."
        
        # Запрос к DeepSeek API
        ai_response = get_deepseek_response(message_text)
        update.message.reply_text(f"{response}\n\nОтвет от AI: {ai_response}")

# Основная функция для запуска бота
def main():
    # Создаем Updater и передаем токен бота
    updater = Updater('8328982592:AAGXRR5pJmrQzqk6dknzDaxgVeS0Q_Gnda0')

    # Получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Обработчик команд /start
    dispatcher.add_handler(CommandHandler('start', lambda update, context: update.message.reply_text('Привет! Я бот с искусственным интеллектом.')))

    # Обработчик всех текстовых сообщений
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, respond_to_message))

    # Запускаем бота
    updater.start_polling()

    # Ожидаем завершения работы
    updater.idle()

if __name__ == '__main__':
    main()
