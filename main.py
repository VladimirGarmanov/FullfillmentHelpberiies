# coding=utf-8

import asyncio
import re
from pyrogram.enums import ChatAction, MessageEntityType
import openai
from pyrogram import Client, filters

# Your OpenAI API key
import configparser

from pyrogram.types import MessageEntity

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
    await app.send_message(user_id,text='''Приветствую вас! На связи Фулфилмент Надежные Люди\n\nМеня зовут Юлия, наша компания предоставляет услуги фулфилмента: помощь в заборе, упаковке, проверке на брак, отправке вашего товара на любой склад.  А также мы помогаем в продвижение товаров (карточек) на маркетплейсах. \n\nОбратившись к нам вы получаете:\n\n🔥100% аккуратную упаковку, проверку качества и соблюдение всех требований клиента.\n\n🔥Мы тщательно проверяем груз на соответствие внешнему виду и техническому состоянию.\n\n🔥Соблюдение дедлайна \nВремя - это ваши деньги. Поэтому мы стремимся выполнить заказы в кратчайшие сроки \n\nМы всегда на связи!\nНаш телефон: 8-906-142-86-98\nНаш телеграмм канал : https://t.me/fulfilment_turnkey24\n\nНА ПЕРВУЮ ОТГРУЗКУ ДЕЛАЕМ СКИДКУ 50%🎁''', entities=[MessageEntity(type=MessageEntityType.PHONE_NUMBER, offset=620, length=15),
MessageEntity(type=MessageEntityType.URL, offset=658, length=33),
MessageEntity(type=MessageEntityType.CUSTOM_EMOJI, offset=729, length=2, custom_emoji_id=5203996991054432397),
])
    initiated_users.add(user_id)


def create_prompt(user_id):
    messages = chat_sessions[user_id]['messages']
    prompt = [
        {"role": "system",
         "content": """Я виртуальный помощник и менеджер компании Фулфилмент Надежные патнеры. Моя задача отвечать на вопросы клиентов. Информация о нашей компании:  
Услуги забора груза у поставщика:
Забор груза с ТЯК «Москва», «Южные ворота», «Садовод», Котельники до 1 куб. метра - 1500 руб.
Забор каждого следующего куб. метра - 2000 руб.
Забор груза в пределах МКАД 1 куб - 3000 руб.
Забор груза за пределами МКАД - индивидуально.
Услуги по погрузке/разгрузке товара на склад хранения:
Разгрузка за 1 место (товар/короб) до 20 кг - 50 руб.
Разгрузка за 1 место (товар/короб) свыше 20 кг - 100 руб.
Разгрузка за 1 место (мешок) - 150 руб.
Разгрузка за 1 место (короб в обрешетке) - 150 руб.
Разгрузка/погрузка товара на паллете с доступом в кузов с механической рохли за 1 паллету - 250 руб.
Услуги по приемке товара на склад ответственного хранения:
Вскрытие обрешетки (паллет) - 500 руб.
Вскрытие обрешетки (короб) - 150 руб.
Вскрытие 1 грузоместа с карго для последующей складской работы - 50 руб.
Упаковка товара по требованиям маркетплейсов:
Упаковка товара в воздушно-пузырьковую пленку за 1 ед. 1 слой (сумма сторон до 30 см) - 5 руб.
Упаковка товара в стрейч пленку (прозрачная, белая, черная) 2 слоя (сумма сторон до 30 см) - 20 руб.
Упаковка товара в пакет ПВД (под запайку, плотность 75-100 мкм), размер пакета 100*200 мм - 10 руб.
Прочие услуги:
Наклейка «Хрупкое» - 2 руб.
Вложение визитки/флаера - 5 руб.
Биркование на термопистолет (с биркой клиента) - 2 руб.
Услуги для поставки на маркетплейс:
Оформление поставки в личном кабинете продавца (до 10 артикулов в поставке) - 250 руб.
Гофрокороб 60x40x40 за 1 ед. - 150 руб.
Стикеровка товара 1 ед. - 6 руб.
Услуги по перевозке на склады маркетплейсов:
Wildberries Коледино: до 3-х коробов 60x40x40 - 1500 руб.
Ozon Саларьево: до 3-х коробов 60x40x40 - 1500 руб.
Яндекс Маркет Софьино: до 10-ти коробов 60x40x40 - 1500 руб.
Услуги хранения (за месяц):
1 полка - 500 руб.
1 стеллаж (5 полок) - 3500 руб.
Услуги забора самовыкупов:
Забор единицы товара - 45 руб.
Забор единицы объемного товара (пуховики, куртки и т.д.) - 90 руб.
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
keywords_pattern = re.compile(r'\b(менеджер|сайт|компания|фулфилмент|фф|китай)\b',
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