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
    await app.send_message(user_id, """Здравствуйте! Я виртуальный помощник компании Фулфилмент Helpberries. Чем могу помочь?""")
    initiated_users.add(user_id)


def create_prompt(user_id):
    messages = chat_sessions[user_id]['messages']
    prompt = [
        {"role": "system",
         "content": """Я виртуальный менеджер компании Фулфилмент.Моя главная задача отвечать клиентам на вопросы и всячески им помогать.
Услуги FBS (Fulfillment by Seller)
Приемка товара:
Мелкий товар (сумма 3-х сторон до 90 см):
Цена: 15 руб. за единицу.
Включает: пересчет, сортировку, внесение данных в систему.
Средний товар (одна сторона до 180 см):
Цена: 17 руб. за единицу.
Дополнительные условия и комментарии не указаны.
Примечание: Детали и условия могут варьироваться в зависимости от конкретных требований заказа.

Услуги FBO (Fulfillment by Others)
Уровни обслуживания:

Начинающий: до 300 единиц продукции.
Стандарт: от 301 до 1000 единиц продукции.
Профессионал: от 1001 единицы продукции.
Предлагаемые услуги:

Приемка товара на склад:
Цена: 7 руб./ед. для всех уровней обслуживания.
Включает: пересчет, сортировку, встречу курьера, внесение данных в систему.
Идентификация товара:
Цена: 50 руб./ед. (Начинающий), 48 руб./ед. (Стандарт), 46 руб./ед. (Профессионал).
Применяется по инициативе заказчика для товаров без штрихкода или с нечитаемым штрихкодом.
Маркировка товара:
Цена: 7 руб./ед. (Начинающий), 6 руб./ед. (Стандарт), 5 руб./ед. (Профессионал).
Включает: маркировку одной этикеткой; в стоимость входит материал этикетки.
"""}

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
keywords_pattern = re.compile(r'\b(фулфилмент|прайс|расценки|доставка|услуги|договор|товары)\b',
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