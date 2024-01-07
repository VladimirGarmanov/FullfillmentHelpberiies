# coding=utf-8

import asyncio
import openai
from pyrogram import Client, filters

# Your OpenAI API key
openai_api_key = "api_key"

# Config
api_id = 'api_id'
api_hash = "api_hash"


# Инициализация Pyrogram Client
app = Client(name="your_session_name", api_id=api_id, api_hash=api_hash)

# Инициализация OpenAI
openai.api_key = openai_api_key

# Словарь для отслеживания чат-сессий пользователей
chat_sessions = {}


async def send_initial_message(user_id):
    await app.send_message(user_id, "Начальное сообщение")


async def handle_chat_with_gpt(user_id, message):
    try:
        if user_id not in chat_sessions:
            chat_sessions[user_id] = {'messages': []}

        chat_sessions[user_id]['messages'].append({'role': 'user', 'content': message})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_sessions[user_id]['messages']
        )

        chat_sessions[user_id]['messages'].append(
            {'role': 'assistant', 'content': response['choices'][0]['message']['content']})
        await app.send_message(user_id, response['choices'][0]['message']['content'])

    except openai.error.RateLimitError:
        # Обработка ошибки превышения лимита запросов
        await asyncio.sleep(20)  # Задержка перед повторной попыткой
        # Повторная попытка обработки сообщения или отправка уведомления пользователю


def create_prompt(messages):
    context = "Роль менеджера"
    history = "\n".join([f"{message['role']}: {message['content']}" for message in messages])
    return f"{context}\n{history}"


@app.on_message(filters.text & filters.regex("ключевое слово") & ~filters.private)
async def detect_price_keyword_in_group(client, message):
    user_id = message.from_user.id
    await send_initial_message(user_id)


@app.on_message(filters.private & ~filters.command("start"))
async def private_message_handler(client, message):
    user_id = message.from_user.id
    await handle_chat_with_gpt(user_id, message.text)


# Запуск бота
app.run()