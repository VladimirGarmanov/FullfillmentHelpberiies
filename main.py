# coding=utf-8

import asyncio
import re
from pyrogram.enums import ChatAction
import openai
from pyrogram import Client, filters

import configparser

# Создание объекта ConfigParser
config = configparser.ConfigParser()

# Чтение файла config.ini
config.read('config.ini')

# Получение значений переменных из секции 'Config'
openai_api_key = config.get('Config', 'openai_api_key')
api_id = config.get('Config', 'api_id')
api_hash = config.get('Config', 'api_hash')

# Инициализация Pyrogram Client
app = Client(name="garmvs", api_id=api_id, api_hash=api_hash)

# Инициализация OpenAI
openai.api_key = openai_api_key

# Словарь для отслеживания чат-сессий пользователей
chat_sessions = {}
# Список пользователей, которым бот уже отправлял сообщения
initiated_users = set()


async def send_initial_message(user_id):
    await app.send_message(user_id, """Кстати, я квартиру продаю, не знаешь, контакты кому нужна квартира?""")
    initiated_users.add(user_id)


def create_prompt(user_id):
    messages = chat_sessions[user_id]['messages']
    prompt = [
        {"role": "system",
         "content": """Я Карина, девушка 25-30 лет, живу в этом ЖК, продаю квартиру"""}

    ]
    prompt.extend(messages)
    return prompt


async def handle_chat_with_gpt(user_id, message):
    if user_id not in chat_sessions:
        chat_sessions[user_id] = {'messages': []}

    chat_sessions[user_id]['messages'].append({'role': 'user', 'content': message})

    # Использование объекта Enum для отправки статуса "печатает"
    await app.send_chat_action(user_id, ChatAction.TYPING)

    prompt = create_prompt(user_id)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )

    chat_sessions[user_id]['messages'].append(
        {'role': 'assistant', 'content': response['choices'][0]['message']['content']})
    await app.send_message(user_id, response['choices'][0]['message']['content'])


# Регулярное выражение для определения ключевых слов
keywords_pattern = re.compile(r'\b(продажа|покупка|квартира|ипотека|арендовать|снять|ЛСР|по первой очереди|ук|гис|жкх|официальное уведомление| жилищно-коммунальные услуги)\b',
                              re.IGNORECASE)


@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    user_id = message.from_user.username
    if user_id not in initiated_users:
        await send_initial_message(user_id)


@app.on_message(filters.chat('me'))
async def my_messages(client, message):
    # Обработка входящих сообщений, отправленных в ваш собственный чат
    print(initiated_users)
    if message.text in initiated_users:
        await message.reply(f"{message.text} - отключен от ИИ")

        initiated_users.remove(message.text)
    else:
        await message.reply(f"{message.text} - не найден")





@app.on_message(filters.private & ~filters.command("start"))
async def private_message_handler(client, message):
    user_id = message.from_user.id
    if user_id in initiated_users:
        await handle_chat_with_gpt(user_id, message.text)


# Запуск бота
app.run()