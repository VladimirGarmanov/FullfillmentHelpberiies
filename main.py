# coding=utf-8

import asyncio
import re

import openai
from pyrogram import Client, filters

# Your OpenAI API key
openai_api_key = "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"

# Config
api_id = '21705953'
api_hash = "7f6f2655d25747fc6fcbf0be1d7296ad"


# Инициализация Pyrogram Client
app = Client(name="your_session_name", api_id=api_id, api_hash=api_hash)

# Инициализация OpenAI
openai.api_key = openai_api_key

# Словарь для отслеживания чат-сессий пользователей
chat_sessions = {}
# Список пользователей, которым бот уже отправлял сообщения
initiated_users = set()


async def send_initial_message(user_id):
    await app.send_message(user_id, "Привет! Я ваш виртуальный помощник компании PrepCentr. Как я могу вам помочь?")
    initiated_users.add(user_id)


def create_prompt(user_id):
    messages = chat_sessions[user_id]['messages']
    prompt = [
        {"role": "system",
         "content": "Я виртуальный помощник и менеджер компании PrepCentr. Моя задача - помогать клиентам с их вопросами и запросами."}
    ]
    prompt.extend(messages)
    return prompt


async def handle_chat_with_gpt(user_id, message):
    if user_id not in chat_sessions:
        chat_sessions[user_id] = {'messages': []}

    chat_sessions[user_id]['messages'].append({'role': 'user', 'content': message})

    prompt = create_prompt(user_id)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt
    )

    chat_sessions[user_id]['messages'].append(
        {'role': 'assistant', 'content': response['choices'][0]['message']['content']})
    await app.send_message(user_id, response['choices'][0]['message']['content'])


# Регулярное выражение для определения ключевых слов
keywords_pattern = re.compile(r'\b(прайс|прайс лист|расчет услуг|рассчитайте|консультация|фулфилмент|цену|условия)\b',
                              re.IGNORECASE)


@app.on_message(filters.text & filters.regex(keywords_pattern) & ~filters.private)
async def detect_keywords_in_group(client, message):
    user_id = message.from_user.id
    if user_id not in initiated_users:
        await send_initial_message(user_id)


@app.on_message(filters.command("stopchat"))
async def stop_chat(client, message):
    user_id = message.from_user.id
    if user_id in initiated_users:
        initiated_users.remove(user_id)
        await message.reply_text("Общение с виртуальным помощником прекращено.")


@app.on_message(filters.command("startchat"))
async def start_chat(client, message):
    user_id = message.from_user.id
    if user_id not in initiated_users:
        initiated_users.add(user_id)
        await message.reply_text("Общение с виртуальным помощником возобновлено.")


@app.on_message(filters.private & ~filters.command("start"))
async def private_message_handler(client, message):
    user_id = message.from_user.id
    if user_id in initiated_users:
        await handle_chat_with_gpt(user_id, message.text)


# Запуск бота
app.run()