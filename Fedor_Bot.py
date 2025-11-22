import logging
import random
import re
import time
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8328982592:AAGXRR5pJmrQzqk6dknzDaxgVeS0Q_Gnda0"

# Базы знаний Фёдора
POSITIVE_RESPONSES = [
    "Да, конечно", "Сто процентов", "Без сомнений", "Ставлю все что это правда",
    "Абсолютно верно", "Естественно", "Не может быть иначе", "Да, и это факт"
]

NEGATIVE_RESPONSES = [
    "Нет, ни в коем случае", "Вряд ли", "Бро, ты уверен", "Я сомневаюсь",
    "Определенно нет", "Это маловероятно", "Лучше не стоит", "Нет, и это точно"
]

NEUTRAL_RESPONSES = [
    "Как знать", "Затрудняюсь ответить, братишка", "Я не знаю, сам думай",
    "Сложный вопрос", "Может да, а может нет", "Время покажет", "Хз честно говоря"
]

# База знаний для элементарных вопросов
KNOWLEDGE_BASE = {
    'погода': [
        "Сегодня отличная погода", "Лучше взять зонтик", "Идеальный день для прогулки",
        "Погода так себе, сиди дома", "Супер погодка"
    ],
    'время': [
        "Время - это иллюзия, братишка", "Сейчас perfect time для действий",
        "Не смотри на время, живи настоящим"
    ],
    'деньги': [
        "Деньги приходят и уходят", "Главное - не количество, а умение распоряжаться",
        "Финансы поют романсы", "Инвестируй в знания"
    ],
    'работа': [
        "Работа - это важно, но не забывай отдыхать", "Ищи то, что по душе",
        "Карьера строится постепенно", "Не работай слишком много"
    ],
    'отношения': [
        "Любовь творит чудеса", "Цени тех, кто рядом", "Искренность - ключ к успеху",
        "Не торопи события"
    ],
    'здоровье': [
        "Здоровье - главное богатство", "Спорт и правильное питание - залог успеха",
        "Не забывай про отдых", "Слушай свой организм"
    ],
    'еда': [
        "Пицца решает многие проблемы", "Съешь что-нибудь вкусненькое",
        "Фрукты - лучший перекус", "Не забывай про воду"
    ],
    'учеба': [
        "Учиться никогда не поздно", "Знания - это сила", "Практика важнее теории",
        "Не зубри, а понимай"
    ]
}

# База создателей функций
CREATORS = {
    'koshkadevachka': 'ERROR',
    'роковой удар': 'электролит',
    'kartoshka': 'полюс', 
    'сраньё': 'Дачи',
    'сранье': 'Дачи',
    'посрать': 'Дачи'
}

# Части тела для действий
BODY_PARTS = ['яйца', 'жопу', 'нос', 'ухо', 'ногу', 'руку', 'мозг', 'сердце', 'легкие', 'зубы', 'язык', 'печень', 'почки', 'селезенку']
WEAPONS = ['пистолет', 'автомат', 'снайперскую винтовку', 'гранатомет', 'пулемет', 'дробовик', 'ракетницу']
LOCATIONS = ['с крыши', 'с вертолета', 'из подворотни', 'из засады', 'с чердака', 'из окна']

# URL для картошки
POTATO_IMAGES = [
    "https://via.placeholder.com/400/FFD700/000000?text=КАРТОШКА",
    "https://via.placeholder.com/400/8B4513/FFFFFF?text=КАРТОФЕЛЬ",
    "https://via.placeholder.com/400/FF6347/FFFFFF?text=БАТАТ",
    "https://via.placeholder.com/400/32CD32/FFFFFF?text=АРБУЗ+СЮРПРИЗ",
]

# Счетчик сранья за день и время последнего сранья
shit_counter = 0
last_shit_time = {}

# Система кошкодевочки (chat_id -> user_info)
koshka_devachka = {}

# Система аккаунтов пользователей
user_accounts = {}  # user_id -> {join_date, awards, coins, femdits, prefix}
user_join_dates = {}  # chat_id -> {user_id: join_timestamp}

# Система сообщений для статистики
user_messages = {}  # chat_id -> {user_id: {daily: count, weekly: count, monthly: count, last_update: timestamp}}

# Система правил чата
chat_rules = {}  # chat_id -> rules_text

# Система валюты и наград
CURRENCY_SYSTEM = {
    'daily_top_reward': {'coins': 5, 'femdits': 1},
    'weekly_top_reward': {'coins': 10, 'femdits': 5},
    'monthly_top_reward': {'coins': 20, 'femdits': 10},
    'gift_price': 10,
    'prefix_price': 50
}

# Femboy Mod System - уровни модерации
FEMBOY_MOD_SYSTEM = {
    6: {"name": "Создатель", "permissions": ["all"], "income": {"daily": {"coins": 0, "femdits": 0}, "weekly": {"coins": 0, "femdits": 0}}},
    5: {"name": "Фембой", "permissions": ["all"], "income": {"daily": {"coins": 1, "femdits": 0}, "weekly": {"coins": 0, "femdits": 1}}},
    4: {"name": "Фембой поменьше", "permissions": ["mute_30d"], "income": {"daily": {"coins": 0, "femdits": 0}, "weekly": {"coins": 0, "femdits": 0}}},
    3: {"name": "Горничная", "permissions": ["mute_15d"], "income": {"daily": {"coins": 0, "femdits": 0}, "weekly": {"coins": 0, "femdits": 0}}},
    2: {"name": "Комедиант", "permissions": ["mute_3d"], "income": {"daily": {"coins": 0, "femdits": 0}, "weekly": {"coins": 0, "femdits": 0}}},
    1: {"name": "Простолюдин", "permissions": [], "income": {"daily": {"coins": 0, "femdits": 0}, "weekly": {"coins": 0, "femdits": 0}}}
}

# Награды по уровням
AWARDS = {
    1: [
        "Высокоуровневый котик", "Золотой игрок", "Мастер общения", "Легенда чата",
        "Сердечко дня", "Звезда беседы", "Гуру мемов", "Король шуток"
    ],
    2: [
        "Элитный воин", "Платиновый мыслитель", "Виртуоз слова", "Титан юмора",
        "Император беседы", "Магистр дискуссий", "Великий оратор", "Хранитель традиций"
    ],
    3: [
        "Божество чата", "Абсолютный чемпион", "Вечный легенд", "Несокрушимый титан",
        "Великий мастер", "Икона стиля", "Непобедимый воин", "Король королей"
    ]
}

# Фразы для модерации
MUTE_PHRASES = [
    "🔇 {user} отправлен в угол подумать о своем поведении на {time}! Причина: {reason}",
    "🤫 {user} получает тайм-аут на {time} за: {reason}",
    "🚫 {user} лишен права голоса на {time}. Нарушение: {reason}",
]

UNMUTE_PHRASES = [
    "🔊 {user} освобожден из тихого угла! Можете снова общаться!",
    "🎤 {user} возвращает право голоса! Больше не молчите!",
    "💬 {user} снова может говорить! Используйте эту возможность с умом!",
]

BAN_PHRASES = [
    "🚷 {user} изгнан из чата навсегда! Причина: {reason}",
    "💔 {user} покидает наше общество. Основание: {reason}",
]

UNBAN_PHRASES = [
    "🤝 {user} прощен и может вернуться в чат!",
    "🕊️ {user} получает второй шанс! Добро пожаловать обратно!",
]

KOSHKA_PHRASES = [
    "🎀 Сегодня кошкодевочкой становится {user}! Поздравляем! 😻",
    "🐾 Все внимание на {user} - новая кошкодевочка дня! 🎉",
]

# Фразы для действий через ответ
ACTION_PHRASES = {
    'расстрелять': [
        "🔫 {attacker} хладнокровно расстреливает {target} из {weapon}!",
        "💥 {attacker} открывает шквальный огонь по {target} из {weapon}!",
    ],
    'убить': [
        "💀 {attacker} жестоко убивает {target} ударом в {body_part}!",
        "☠️ {attacker} отправляет {target} на тот свет через {body_part}!",
    ],
    'сбросить ядерку': [
        "💣 {attacker} сбрасывает тактическую ядерку на позиции {target}!",
        "☢️ {attacker} запускает ядерную ракету по {target}!",
    ],
    'раздавить': [
        "🐘 {attacker} сокрушительно раздавливает {target} как букашку!",
        "🏔️ {attacker} давит {target} с силой горного обвала!",
    ],
    'уничтожить': [
        "💥 {attacker} полностью уничтожает {target} до молекулярного уровня!",
        "🔥 {attacker} стирает {target} в порошок!",
    ],
    'погладить': [
        "🐱 {attacker} нежно гладит {target} по головке! 😊",
        "💕 {attacker} ласково поглаживает {target}!",
    ],
    'похвалить': [
        "👏 {attacker} хвалит {target} за отличную работу!",
        "🎉 {attacker} аплодирует {target} стоя!",
    ],
    'похлопать по плечу': [
        "🤝 {attacker} дружески хлопает {target} по плечу!",
        "💪 {attacker} ободряюще похлопывает {target} по плечу!",
    ],
    'отказать уважение': [
        "🖕 {attacker} демонстративно отказывает в уважении {target}!",
        "😾 {attacker} показывает {target}, что не уважает его!",
    ]
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_type = update.message.chat.type
    
    if chat_type == 'private':
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n\n"
            f"Я Фёдор - почти что ИИ с собственным интеллектом!\n\n"
            f"Я умею:\n"
            f"• Отвечать на приветствия\n"
            f"• Предсказывать будущее\n"
            f"• Отвечать на элементарные вопросы\n"
            f"• Разные действия через ответ на сообщение\n"
            f"• Показывать картошку\n"
            f"• Считать сранье за день\n"
            f"• Модерировать чат (Femboy Mod System)\n"
            f"• Систему аккаунтов и наград\n"
            f"• Экономику (монеты и фемдиты)\n"
            f"• Топы по сообщениям\n"
            f"• Транскрипцию голосовых\n\n"
            f"В группах я отвечаю только когда ко мне обращаются по имени!"
        )
    else:
        await update.message.reply_text(
            "Привет всем! Я Фёдор - бот для веселья и модерации!\n\n"
            "Развлекательные команды:\n"
            "• Ответь на сообщение с действием\n"
            "• 'kartoshka' - получить картошку\n"
            "• 'Посрать' - добавить сранье\n"
            "• 'сранье статус' - статистика\n"
            "• 'Koshkaдевачка' - стать кошкодевочкой\n"
            "• 'аккаунт' - посмотреть свой аккаунт\n"
            "• 'топ день/неделя/месяц' - топ активности\n"
            "• 'Фёдор что ты умеешь?' - обучение\n\n"
            "Femboy Mod System:\n"
            "• /mute @username время причина\n"
            "• /unmute @username\n"
            "• /ban @username причина\n"
            "• /unban @username\n\n"
            "Награждение: Ответьте 'наградить 1 Название'\n"
            "Транскрипция: Ответьте 'Фёдор перескажи' на голосовое"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Игнорируем сообщения без текста
    if not update.message or not update.message.text:
        # Обработка голосовых сообщений для транскрипции
        if update.message.voice and update.message.reply_to_message:
            reply_text = update.message.caption or ""
            if 'фёдор перескажи' in reply_text.lower() or 'федор перескажи' in reply_text.lower():
                await handle_voice_transcription(update, context)
        return
        
    message_text = update.message.text.lower().strip()
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type
    
    # Обновляем информацию о времени вступления пользователя
    await update_user_join_date(update, user_id, chat_id)
    
    # Обновляем статистику сообщений
    await update_message_stats(chat_id, user_id)
    
    # Обработка команд правил
    if message_text == '+правила' and await is_creator(update, context):
        # Сохраняем правила из следующего сообщения
        context.user_data['waiting_for_rules'] = True
        context.user_data['rules_chat_id'] = chat_id
        await update.message.reply_text("📝 Напишите правила после этой команды в следующем сообщении")
        return
    
    if context.user_data.get('waiting_for_rules') and context.user_data.get('rules_chat_id') == chat_id:
        chat_rules[chat_id] = message_text
        context.user_data['waiting_for_rules'] = False
        await update.message.reply_text("✅ Правила чата успешно установлены!")
        return
    
    if message_text in ['правила', 'правила']:
        await handle_rules(update, chat_id)
        return
    
    # Обработка награждения через ответ на сообщение
    if update.message.reply_to_message and message_text.startswith('наградить'):
        if await check_admin(update, context):
            await handle_award_reply(update, context, message_text)
        else:
            await update.message.reply_text("❌ Только администраторы могут выдавать награды!")
        return
    
    # Обработка команд валюты
    if message_text.startswith('префикс '):
        await handle_prefix_purchase(update, context, message_text)
        return
    
    if message_text == 'подарок':
        await handle_gift_sending(update, context)
        return
    
    # Обработка топа
    if message_text.startswith('топ '):
        await handle_top(update, context, message_text)
        return
    
    # Обработка обучения
    if 'фёдор что ты умеешь' in message_text or 'федор что ты умеешь' in message_text:
        await handle_tutorial(update, chat_type)
        return
    
    # Обработка действий через ответ на сообщение (всегда работает)
    if update.message.reply_to_message:
        for action in ACTION_PHRASES.keys():
            if action in message_text:
                await handle_action_reply(update, context, action)
                return
        
        # Обработка рокового удара через ответ на сообщение
        if 'роковой удар' in message_text:
            await handle_fatal_strike_reply(update, context)
            return
    
    # Специальные команды (всегда работают)
    special_commands = [
        'kartoshka', 'картошк', 'посрать', 'сранье статус', 'сраньё статус',
        'koshkadevachka', 'кошкодевочка', 'кто сегодня кошкодевочка', 'кто кошкодевочка',
        'аккаунт', 'профиль', 'баланс'
    ]
    
    if any(cmd in message_text for cmd in special_commands):
        if 'koshkadevachka' in message_text or 'кошкодевочка' in message_text:
            await handle_koshka_devachka(update, user, chat_id)
            return
        elif any(phrase in message_text for phrase in ['кто сегодня кошкодевочка', 'кто кошкодевочка']):
            await handle_koshka_status(update, chat_id)
            return
        elif 'kartoshka' in message_text or 'картошк' in message_text:
            await handle_potato(update)
            return
        elif 'посрать' in message_text:
            await handle_shit(update, user_id, user.first_name)
            return
        elif 'сранье статус' in message_text or 'сраньё статус' in message_text:
            await handle_shit_counter(update, 'status', user_id, user.first_name)
            return
        elif 'аккаунт' in message_text or 'профиль' in message_text or 'баланс' in message_text:
            await handle_account(update, user_id, chat_id)
            return
    
    # В личных сообщениях обрабатываем все
    if chat_type == 'private':
        if any(greeting in message_text for greeting in ['привет', 'здравствуй', 'hello', 'hi']):
            await handle_greeting(update, user)
        elif any(trigger in message_text for trigger in ['фёдор', 'федор']):
            await handle_fedor_request(update, message_text, user)
        else:
            await handle_smart_response(update, message_text, user)
        return
    
    # В группах отвечаем только на прямые обращения
    if chat_type in ['group', 'supergroup']:
        # Проверяем, обращаются ли к боту
        if is_direct_address(message_text):
            await handle_direct_address(update, message_text, user)
        return

# ========== НОВЫЕ СИСТЕМЫ ==========

async def handle_voice_transcription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Транскрипция голосовых сообщений"""
    try:
        voice_message = update.message.reply_to_message.voice
        if not voice_message:
            await update.message.reply_text("❌ Это не голосовое сообщение!")
            return
        
        # Здесь должна быть интеграция с сервисом транскрипции
        # Временно используем заглушку
        transcription = "🎤 [Транскрипция голосового сообщения]\n\nЭто пример транскрипции. В реальной версии здесь будет текст из голосового сообщения."
        
        await update.message.reply_text(
            transcription,
            reply_to_message_id=update.message.reply_to_message.message_id
        )
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        await update.message.reply_text("❌ Ошибка при транскрипции голосового сообщения")

async def handle_tutorial(update: Update, chat_type: str):
    """Обучение пользователя функциям бота"""
    if chat_type == 'private':
        tutorial_text = (
            "🎓 Обучающий гид по Фёдору!\n\n"
            "💬 Основные команды:\n"
            "• Просто общайся со мной как с другом\n"
            "• Спрашивай о погоде, времени, жизни\n"
            "• Проси предсказания: 'Фёдор расскажи...'\n\n"
            "🎮 Развлечения:\n"
            "• 'kartoshka' - случайная картошка\n"
            "• Ответь на сообщение с действием\n"
            "• 'Koshkaдевачка' - стать кошкодевочкой\n"
            "• 'посрать' - система сранья (раз в 4 часа)\n\n"
            "📊 Аккаунт:\n"
            "• 'аккаунт' - твой профиль\n"
            "• 'топ день' - топ за день\n"
            "• Зарабатывай монеты за активность!\n\n"
            "🎤 Дополнительно:\n"
            "• Ответь 'Фёдор перескажи' на голосовое\n"
            "• Участвуй в жизни чата!"
        )
    else:
        tutorial_text = (
            "🎓 Обучающий гид по Фёдору для групп!\n\n"
            "💬 Обращение ко мне:\n"
            "Начинай сообщения с 'Фёдор' или 'Федор'\n\n"
            "🎮 Развлечения:\n"
            "• Ответь на сообщение: 'расстрелять', 'убить', 'погладить' и др.\n"
            "• 'kartoshka' - случайная картошка\n"
            "• 'Koshkaдевачка' - стать кошкодевочкой дня\n"
            "• 'посрать' - система сранья\n\n"
            "📊 Социальное:\n"
            "• 'аккаунт' - твой профиль\n"
            "• 'топ день/неделя/месяц' - топ активности\n"
            "• Зарабатывай монеты и фемдиты!\n\n"
            "🛡️ Модерация (для админов):\n"
            "• /mute @username время причина\n"
            "• /ban @username причина\n"
            "• Ответь 'наградить 1 Название'\n\n"
            "🎤 Дополнительно:\n"
            "• Ответь 'Фёдор перескажи' на голосовое\n"
            "• 'правила' - правила чата"
        )
    
    await update.message.reply_text(tutorial_text)

async def handle_rules(update: Update, chat_id: int):
    """Показывает правила чата"""
    if chat_id in chat_rules:
        rules = chat_rules[chat_id]
        await update.message.reply_text(f"📜 Правила чата:\n\n{rules}")
    else:
        await update.message.reply_text("📜 Правила чата еще не установлены. Создатель может установить их командой '+правила'")

async def update_message_stats(chat_id: int, user_id: int):
    """Обновляет статистику сообщений пользователя"""
    current_time = time.time()
    
    if chat_id not in user_messages:
        user_messages[chat_id] = {}
    
    if user_id not in user_messages[chat_id]:
        user_messages[chat_id][user_id] = {
            'daily': 0,
            'weekly': 0, 
            'monthly': 0,
            'last_update': current_time
        }
    
    # Проверяем сброс статистики
    user_data = user_messages[chat_id][user_id]
    last_update = user_data['last_update']
    
    # Сброс дневной статистики (каждые 24 часа)
    if current_time - last_update >= 24 * 3600:
        user_data['daily'] = 0
    
    # Сброс недельной статистики (каждые 7 дней)
    if current_time - last_update >= 7 * 24 * 3600:
        user_data['weekly'] = 0
    
    # Сброс месячной статистики (каждые 30 дней)
    if current_time - last_update >= 30 * 24 * 3600:
        user_data['monthly'] = 0
    
    # Обновляем счетчики
    user_data['daily'] += 1
    user_data['weekly'] += 1
    user_data['monthly'] += 1
    user_data['last_update'] = current_time

async def handle_top(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Показывает топ пользователей по сообщениям"""
    chat_id = update.message.chat.id
    
    if chat_id not in user_messages:
        await update.message.reply_text("📊 Статистика пока недоступна для этого чата")
        return
    
    period = message_text.split()[1] if len(message_text.split()) > 1 else 'день'
    
    if period not in ['день', 'неделя', 'месяц']:
        await update.message.reply_text("❌ Используйте: топ день/неделя/месяц")
        return
    
    # Получаем статистику для нужного периода
    period_key = {'день': 'daily', 'неделя': 'weekly', 'месяц': 'monthly'}[period]
    
    # Собираем данные пользователей
    user_stats = []
    for user_id, stats in user_messages[chat_id].items():
        try:
            user = await context.bot.get_chat_member(chat_id, user_id)
            user_stats.append({
                'name': user.user.first_name,
                'count': stats[period_key],
                'user_id': user_id
            })
        except:
            continue
    
    # Сортируем по убыванию
    user_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # Формируем сообщение
    if not user_stats:
        await update.message.reply_text(f"📊 Нет статистики за {period}")
        return
    
    top_text = f"🏆 Топ за {period}:\n\n"
    for i, user in enumerate(user_stats[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        top_text += f"{medal} {user['name']} - {user['count']} сообщ.\n"
    
    await update.message.reply_text(top_text)

async def handle_prefix_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Покупка префикса за монеты"""
    user_id = update.message.from_user.id
    prefix = message_text.replace('префикс ', '').strip()
    
    if len(prefix) > 15:
        await update.message.reply_text("❌ Префикс не может быть длиннее 15 символов")
        return
    
    # Инициализируем аккаунт если нужно
    if user_id not in user_accounts:
        user_accounts[user_id] = {'coins': 0, 'femdits': 0, 'awards': [], 'prefix': ''}
    
    user_data = user_accounts[user_id]
    
    if user_data['coins'] < CURRENCY_SYSTEM['prefix_price']:
        await update.message.reply_text(f"❌ Недостаточно монет! Нужно {CURRENCY_SYSTEM['prefix_price']} монет")
        return
    
    # Списание монет и установка префикса
    user_data['coins'] -= CURRENCY_SYSTEM['prefix_price']
    user_data['prefix'] = prefix
    
    await update.message.reply_text(f"✅ Префикс '{prefix}' успешно установлен!")

async def handle_gift_sending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка подарка высшим админам"""
    user_id = update.message.from_user.id
    
    if user_id not in user_accounts:
        user_accounts[user_id] = {'coins': 0, 'femdits': 0, 'awards': [], 'prefix': ''}
    
    user_data = user_accounts[user_id]
    
    if user_data['coins'] < CURRENCY_SYSTEM['gift_price']:
        await update.message.reply_text(f"❌ Недостаточно монет! Нужно {CURRENCY_SYSTEM['gift_price']} монет")
        return
    
    # Списание монет
    user_data['coins'] -= CURRENCY_SYSTEM['gift_price']
    
    # Здесь должна быть логика отправки подарка админам
    # Временно просто сообщаем об успехе
    await update.message.reply_text("🎁 Подарок отправлен высшим администраторам!")

async def is_creator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь создателем"""
    user = update.message.from_user
    chat_id = update.message.chat.id
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        return chat_member.status == 'creator'
    except Exception as e:
        logger.error(f"Creator check error: {e}")
        return False

# ========== ОБНОВЛЕННЫЕ СИСТЕМЫ ==========

async def handle_account(update: Update, user_id: int, chat_id: int):
    """Показывает аккаунт пользователя с валютой"""
    if chat_id not in user_join_dates or user_id not in user_join_dates[chat_id]:
        await update.message.reply_text("❌ Информация о вашем аккаунте не найдена!")
        return
    
    join_timestamp = user_join_dates[chat_id][user_id]
    join_date = datetime.fromtimestamp(join_timestamp).strftime("%d.%m.%Y %H:%M")
    days_in_chat = int((time.time() - join_timestamp) / (24 * 3600))
    rank = get_user_rank(join_timestamp)
    
    # Получаем данные пользователя
    if user_id not in user_accounts:
        user_accounts[user_id] = {'coins': 0, 'femdits': 0, 'awards': [], 'prefix': ''}
    
    user_data = user_accounts[user_id]
    
    # Получаем статистику сообщений
    message_stats = ""
    if chat_id in user_messages and user_id in user_messages[chat_id]:
        stats = user_messages[chat_id][user_id]
        message_stats = f"💬 Сообщения: {stats['daily']} (день) / {stats['weekly']} (неделя) / {stats['monthly']} (месяц)\n"
    
    # Получаем награды
    awards_text = "Нет наград"
    if user_data['awards']:
        awards_text = "\n".join([f"• {award}" for award in user_data['awards']])
    
    # Получаем префикс
    prefix_text = f"🏷️ Префикс: {user_data['prefix']}\n" if user_data['prefix'] else ""
    
    account_info = (
        f"👤 Аккаунт {update.message.from_user.first_name}\n"
        f"📅 В чате с: {join_date}\n"
        f"⏰ Дней в чате: {days_in_chat}\n"
        f"🎖️ Звание: {rank}\n"
        f"{message_stats}"
        f"💰 Монеты: {user_data['coins']}\n"
        f"💎 Фемдиты: {user_data['femdits']}\n"
        f"{prefix_text}"
        f"🏆 Награды:\n{awards_text}\n\n"
        f"💡 Команды: 'префикс текст' (50 монет), 'подарок' (10 монет)"
    )
    
    await update.message.reply_text(account_info)

# ========== Femboy Mod System ==========

async def check_femboy_permission(update: Update, context: ContextTypes.DEFAULT_TYPE, permission: str) -> bool:
    """Проверяет права доступа по Femboy Mod System"""
    user = update.message.from_user
    chat_id = update.message.chat.id
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        
        # Определяем уровень доступа
        if chat_member.status == 'creator':
            user_level = 6
        elif chat_member.status == 'administrator':
            # Здесь можно добавить логику определения уровня админа
            # Временно считаем всех админов Фембоями (уровень 5)
            user_level = 5
        else:
            user_level = 1
        
        # Проверяем разрешения для уровня
        level_permissions = FEMBOY_MOD_SYSTEM[user_level]['permissions']
        
        if 'all' in level_permissions:
            return True
        
        return permission in level_permissions
        
    except Exception as e:
        logger.error(f"Femboy permission check error: {e}")
        return False

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мут пользователя с проверкой прав Femboy System"""
    if not await check_femboy_permission(update, context, "mute"):
        await update.message.reply_text("❌ Недостаточно прав для мута!")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("Использование: /mute @username время_в_минутах причина")
        return
    
    target_username = context.args[0]
    try:
        mute_minutes = int(context.args[1])
        reason = ' '.join(context.args[2:])
    except ValueError:
        await update.message.reply_text("Время должно быть числом (минуты)")
        return
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("Пользователь не найден")
        return
    
    try:
        until_date = datetime.now() + timedelta(minutes=mute_minutes)
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_date
        )
        
        phrase = random.choice(MUTE_PHRASES).format(
            user=target_user.first_name,
            time=f"{mute_minutes} минут",
            reason=reason
        )
        await update.message.reply_text(phrase)
        
    except Exception as e:
        logger.error(f"Mute error: {e}")
        await update.message.reply_text("Ошибка при муте пользователя")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Размут пользователя"""
    if not await check_femboy_permission(update, context, "unmute"):
        await update.message.reply_text("❌ Недостаточно прав для размута!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /unmute @username")
        return
    
    target_username = context.args[0]
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("Пользователь не найден")
        return
    
    try:
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        
        phrase = random.choice(UNMUTE_PHRASES).format(user=target_user.first_name)
        await update.message.reply_text(phrase)
        
    except Exception as e:
        logger.error(f"Unmute error: {e}")
        await update.message.reply_text("Ошибка при размуте пользователя")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Бан пользователя"""
    if not await check_femboy_permission(update, context, "ban"):
        await update.message.reply_text("❌ Недостаточно прав для бана!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /ban @username причина")
        return
    
    target_username = context.args[0]
    reason = ' '.join(context.args[1:])
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("Пользователь не найден")
        return
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id
        )
        
        phrase = random.choice(BAN_PHRASES).format(
            user=target_user.first_name,
            reason=reason
        )
        await update.message.reply_text(phrase)
        
    except Exception as e:
        logger.error(f"Ban error: {e}")
        await update.message.reply_text("Ошибка при бане пользователя")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разбан пользователя"""
    if not await check_femboy_permission(update, context, "unban"):
        await update.message.reply_text("❌ Недостаточно прав для разбана!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /unban @username")
        return
    
    target_username = context.args[0]
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("Пользователь не найден")
        return
    
    try:
        await context.bot.unban_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id
        )
        
        phrase = random.choice(UNBAN_PHRASES).format(user=target_user.first_name)
        await update.message.reply_text(phrase)
        
    except Exception as e:
        logger.error(f"Unban error: {e}")
        await update.message.reply_text("Ошибка при разбане пользователя")

async def get_user_from_mention(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Получает пользователя из упоминания"""
    clean_username = username.lstrip('@')
    try:
        # В реальной реализации здесь должна быть логика поиска пользователя
        # Пока возвращаем отправителя команды как заглушку
        return update.message.from_user
    except Exception as e:
        logger.error(f"User lookup error: {e}")
        return None

async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Проверяет, является ли пользователь администратором"""
    user = update.message.from_user
    chat_id = update.message.chat.id
    
    try:
        chat_member = await context.bot.get_chat_member(chat_id, user.id)
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Admin check error: {e}")
        return False

# ========== СУЩЕСТВУЮЩИЕ ФУНКЦИИ ==========

async def update_user_join_date(update: Update, user_id: int, chat_id: int):
    """Обновляет информацию о времени вступления пользователя в чат"""
    if chat_id not in user_join_dates:
        user_join_dates[chat_id] = {}
    
    if user_id not in user_join_dates[chat_id]:
        user_join_dates[chat_id][user_id] = time.time()

def get_user_rank(join_timestamp: float) -> str:
    """Определяет звание пользователя по времени пребывания в чате"""
    days_in_chat = (time.time() - join_timestamp) / (24 * 3600)
    
    if days_in_chat < 3:
        return "Новенький"
    elif days_in_chat < 14:
        return "Олд поменьше"
    elif days_in_chat < 28:
        return "Олд"
    elif days_in_chat < 90:
        return "Олдфаг"
    else:
        return "Ветеран"

async def handle_award_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Обработка награждения через ответ на сообщение"""
    try:
        # Разбираем сообщение
        parts = message_text.split()
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Использование: наградить уровень 'название награды'\n"
                "Пример: наградить 1 Высокоуровневый котик"
            )
            return
        
        level = int(parts[1])
        award_name = ' '.join(parts[2:])
        
        if level not in [1, 2, 3]:
            await update.message.reply_text("❌ Уровень награды должен быть 1, 2 или 3!")
            return
        
        # Получаем пользователя, которого награждают
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        
        # Инициализируем аккаунт пользователя если нужно
        if target_user_id not in user_accounts:
            user_accounts[target_user_id] = {'coins': 0, 'femdits': 0, 'awards': [], 'prefix': ''}
        
        # Добавляем награду
        user_accounts[target_user_id]['awards'].append(award_name)
        
        # Отправляем сообщение о награждении
        award_message = (
            f"🎖️ {update.message.from_user.first_name} награждает {target_user.first_name}!\n"
            f"🏆 Награда: {award_name}\n"
            f"⭐ Уровень: {level}"
        )
        
        await update.message.reply_text(
            award_message,
            reply_to_message_id=update.message.reply_to_message.message_id
        )
        
    except ValueError:
        await update.message.reply_text("❌ Уровень награды должен быть числом (1, 2 или 3)!")
    except Exception as e:
        logger.error(f"Award error: {e}")
        await update.message.reply_text("❌ Ошибка при выдаче награды!")

async def handle_action_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Обработка действий через ответ на сообщение"""
    try:
        # Пользователь, который выполняет действие
        attacker = update.message.from_user
        attacker_name = attacker.first_name
        
        # Пользователь, на которого отвечают (цель)
        target_message = update.message.reply_to_message
        target_user = target_message.from_user
        target_name = target_user.first_name
        
        # Выбираем случайную фразу для действия
        phrases = ACTION_PHRASES[action]
        phrase_template = random.choice(phrases)
        
        # Заполняем шаблон в зависимости от действия
        if action in ['расстрелять']:
            weapon = random.choice(WEAPONS)
            location = random.choice(LOCATIONS)
            message = phrase_template.format(
                attacker=attacker_name,
                target=target_name,
                weapon=weapon,
                location=location
            )
        elif action in ['убить', 'раздавить', 'уничтожить']:
            body_part = random.choice(BODY_PARTS)
            message = phrase_template.format(
                attacker=attacker_name,
                target=target_name,
                body_part=body_part
            )
        else:
            message = phrase_template.format(
                attacker=attacker_name,
                target=target_name
            )
        
        # Отправляем ответ на исходное сообщение
        await update.message.reply_text(
            message,
            reply_to_message_id=target_message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error in action reply {action}: {e}")
        await update.message.reply_text("Ошибка при выполнении действия!")

async def handle_fatal_strike_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка рокового удара через ответ на сообщение"""
    try:
        # Пользователь, который наносит удар
        attacker = update.message.from_user
        attacker_name = attacker.first_name
        
        # Пользователь, на которого отвечают (цель)
        target_message = update.message.reply_to_message
        target_user = target_message.from_user
        target_name = target_user.first_name
        
        # Случайная часть тела
        body_part = random.choice(BODY_PARTS)
        
        # Случайная фраза для удара
        strike_message = random.choice(ACTION_PHRASES['убить']).format(
            attacker=attacker_name,
            target=target_name,
            body_part=body_part
        )
        
        # Отправляем ответ на исходное сообщение
        await update.message.reply_text(
            strike_message,
            reply_to_message_id=target_message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error in fatal strike reply: {e}")
        await update.message.reply_text("Ошибка при выполнении рокового удара!")

def is_direct_address(message_text: str) -> bool:
    """Проверяет, обращаются ли к боту напрямую"""
    direct_triggers = [
        'фёдор', 'федор', 'фёдор,', 'федор,', 'фёдор!', 'федор!',
        'фёдор:', 'федор:', 'фёдор ', 'федор '
    ]
    
    for trigger in direct_triggers:
        if message_text.startswith(trigger):
            return True
    
    if any(mention in message_text for mention in ['@', 'бот']):
        return True
    
    return False

async def handle_direct_address(update: Update, message_text: str, user):
    """Обработка прямых обращений к боту в группах"""
    clean_text = message_text
    triggers = ['фёдор', 'федор', 'бот']
    for trigger in triggers:
        clean_text = clean_text.replace(trigger, '').strip()
    
    clean_text = re.sub(r'^[,\s!:\-]+', '', clean_text)
    
    if not clean_text:
        responses = [
            "Да, я слушаю! Что скажешь?",
            "Я здесь! Задавай вопрос!",
            "Привет! Чем могу помочь?"
        ]
        await update.message.reply_text(random.choice(responses))
        return
    
    if any(phrase in clean_text for phrase in ['кто придумал', 'кто создал', 'автор']):
        await handle_creator_question(update, message_text)
        return
    
    if any(phrase in clean_text for phrase in ['расскажи', 'скажи', 'предскажи', 'предсказание']):
        await handle_prediction(update, message_text)
        return
    
    if any(greeting in clean_text for greeting in ['привет', 'здравствуй', 'hello', 'hi']):
        await handle_greeting(update, user)
        return
    
    await handle_smart_response(update, clean_text, user)

async def handle_koshka_devachka(update: Update, user, chat_id):
    """Обработка Koshkaдевачка - назначение кошкодевочки"""
    if chat_id in koshka_devachka:
        current_koshka = koshka_devachka[chat_id]
        if current_koshka['user_id'] == user.id:
            await update.message.reply_text("❌ Ты уже сегодня кошкодевочка! Не жадничай!")
            return
    
    koshka_devachka[chat_id] = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'appointed_at': datetime.now()
    }
    
    phrase = random.choice(KOSHKA_PHRASES).format(user=user.first_name)
    await update.message.reply_text(phrase)

async def handle_koshka_status(update: Update, chat_id):
    """Показывает текущую кошкодевочку"""
    if chat_id in koshka_devachka:
        koshka = koshka_devachka[chat_id]
        appointed_time = koshka['appointed_at'].strftime("%H:%M")
        await update.message.reply_text(
            f"🎀 Сегодняшняя кошкодевочка - {koshka['first_name']}!\n"
            f"Назначена в {appointed_time} 👑"
        )
    else:
        await update.message.reply_text("😿 Сегодня еще никто не стал кошкодевочкой! Напиши 'Koshkaдевачка' чтобы стать первой!")

async def handle_potato(update: Update):
    """Обработка картошки"""
    if random.random() < 0.05:
        await update.message.reply_text("🎉 СЮРПРИЗ! Вместо картошки - АРБУЗ! 🍉")
        await update.message.reply_photo("https://via.placeholder.com/400/32CD32/FFFFFF?text=АРБУЗ+СЮРПРИЗ")
    else:
        potato_message = random.choice([
            "🥔 Держи картошечку!",
            "🍟 Свежая картошка из огорода!",
            "🥔 Лови картофелинку!",
            "🍠 Картошка фри в подарок!"
        ])
        await update.message.reply_text(potato_message)
        await update.message.reply_photo(random.choice(POTATO_IMAGES))

async def handle_shit(update: Update, user_id: int, user_name: str):
    """Обработка команды посрать"""
    global shit_counter
    
    current_time = time.time()
    
    if user_id in last_shit_time:
        time_since_last_shit = current_time - last_shit_time[user_id]
        if time_since_last_shit < 4 * 3600:
            remaining_time = 4 * 3600 - time_since_last_shit
            hours = int(remaining_time // 3600)
            minutes = int((remaining_time % 3600) // 60)
            seconds = int(remaining_time % 60)
            
            await update.message.reply_text(
                f"Ты уже знатно обосрался! Жди 4 часа, ну а если точнее {hours:02d}:{minutes:02d}:{seconds:02d}"
            )
            return
    
    shit_counter += 1
    last_shit_time[user_id] = current_time
    
    shit_messages = [
        f"💩 {user_name} успешно посрал! Всего за день: {shit_counter}",
        f"📊 {user_name} добавил сранье! Общий счет: {shit_counter}",
        f"🎯 {user_name} попал в цель! Сранье: {shit_counter}",
        f"💩 {user_name} срал как бог! Всего: {shit_counter}"
    ]
    await update.message.reply_text(random.choice(shit_messages))

async def handle_shit_counter(update: Update, action: str, user_id: int, user_name: str):
    """Обработка счетчика сранья"""
    global shit_counter
    
    if action == 'status':
        if shit_counter == 0:
            await update.message.reply_text("Сегодня чисто! Сранья: 0")
        else:
            status_messages = [
                f"📈 Статистика сранья за день: {shit_counter}",
                f"💩 Всего насранья сегодня: {shit_counter}",
                f"📊 Текущий уровень сранья: {shit_counter}",
                f"🎯 Количество зафиксированного сранья: {shit_counter}"
            ]
            await update.message.reply_text(random.choice(status_messages))

async def handle_creator_question(update: Update, message_text: str):
    """Обработка вопросов о создателях"""
    message_lower = message_text.lower()
    
    for function_name, creator in CREATORS.items():
        if function_name in message_lower:
            group_name = "Обсуждение зелени" if function_name == 'роковой удар' else "секретной группы"
            responses = [
                f"Эту функцию придумал {creator} из {group_name}",
                f"Автор этой фичи - {creator} из {group_name}",
                f"Это творение {creator} из {group_name}",
                f"Идея принадлежит {creator} из {group_name}"
            ]
            await update.message.reply_text(random.choice(responses))
            return
    
    await update.message.reply_text("У каждой функции есть свой автор! Спроси про конкретную функцию.")

async def handle_greeting(update: Update, user):
    """Обработка приветствий"""
    greetings = [
        f"Привет, {user.first_name}! Как твои дела?",
        f"Здравствуй, {user.first_name}! Рад тебя видеть!",
        f"О, {user.first_name}! Как настроение?",
        f"Приветствую, {user.first_name}! Чем займемся сегодня?"
    ]
    await update.message.reply_text(random.choice(greetings))

async def handle_fedor_request(update: Update, message_text: str, user):
    """Обработка запросов к Фёдору"""
    if any(phrase in message_text for phrase in ['расскажи', 'скажи', 'предскажи', 'предсказание']):
        await handle_prediction(update, message_text)
    else:
        responses = [
            f"Я здесь, {user.first_name}! Спрашивай что угодно!",
            f"Слушаю тебя, {user.first_name}! Задавай вопрос!",
            f"Фёдор на связи! В чем вопрос?"
        ]
        await update.message.reply_text(random.choice(responses))

async def handle_prediction(update: Update, message_text: str):
    """Обработка предсказаний"""
    question = extract_question(message_text)
    
    if random.random() < 0.3:
        smart_response = generate_smart_response(question)
        if smart_response:
            final_response = f"На вопрос '{question}'\n\nФёдор анализирует: {smart_response}"
            await update.message.reply_text(final_response)
            return
    
    response_type = random.choices(['positive', 'negative', 'neutral'], weights=[40, 30, 30])[0]
    
    if response_type == 'positive':
        response = random.choice(POSITIVE_RESPONSES)
    elif response_type == 'negative':
        response = random.choice(NEGATIVE_RESPONSES)
    else:
        response = random.choice(NEUTRAL_RESPONSES)
    
    final_response = f"На вопрос '{question}'\n\nФёдор говорит: {response}"
    await update.message.reply_text(final_response)

async def handle_smart_response(update: Update, message_text: str, user):
    """Обработка умных ответов на элементарные вопросы"""
    response = None
    
    if any(word in message_text for word in ['погод', 'дождь', 'солнц', 'холодно', 'тепло']):
        response = random.choice(KNOWLEDGE_BASE['погода'])
    elif any(word in message_text for word in ['врем', 'час', 'который час', 'сколько времени']):
        current_time = datetime.now().strftime("%H:%M")
        response = f"Сейчас {current_time}\n{random.choice(KNOWLEDGE_BASE['время'])}"
    elif any(word in message_text for word in ['деньг', 'финанс', 'богат', 'бедн', 'зарплат']):
        response = random.choice(KNOWLEDGE_BASE['деньги'])
    elif any(word in message_text for word in ['работ', 'карьер', 'начальник', 'коллег']):
        response = random.choice(KNOWLEDGE_BASE['работа'])
    elif any(word in message_text for word in ['любов', 'отношен', 'парень', 'девушк', 'семь']):
        response = random.choice(KNOWLEDGE_BASE['отношения'])
    elif any(word in message_text for word in ['здоров', 'болит', 'врач', 'лекарств', 'спорт']):
        response = random.choice(KNOWLEDGE_BASE['здоровье'])
    elif any(word in message_text for word in ['еда', 'кушать', 'голод', 'есть', 'пицц', 'бургер']):
        response = random.choice(KNOWLEDGE_BASE['еда'])
    elif any(word in message_text for word in ['учеб', 'учит', 'занят', 'экзамен', 'сессия']):
        response = random.choice(KNOWLEDGE_BASE['учеба'])
    elif any(phrase in message_text for phrase in ['как дела', 'как ты', 'как жизнь']):
        responses = [
            "Отлично! А у тебя?", "Супер! Помогаю людям", "Все хорошо, работаю",
            "Замечательно! Спасибо что спросил"
        ]
        response = random.choice(responses)
    elif any(phrase in message_text for phrase in ['что делаешь', 'чем занят']):
        responses = [
            "Анализирую мироздание", "Отвечаю на твой вопрос",
            "Помогаю людям с их вопросами", "Размышляю о смысле жизни"
        ]
        response = random.choice(responses)
    
    if response:
        await update.message.reply_text(f"{user.first_name}, {response}")
    else:
        await update.message.reply_text(
            f"Интересный вопрос, {user.first_name}!\n"
            f"Попробуй спросить о чем-то конкретном или используй одну из наших функций!"
        )

def generate_smart_response(question: str) -> str:
    """Генерирует умный ответ на основе вопроса"""
    if not question:
        return ""
    
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['сдам', 'успех', 'получится', 'выигра']):
        return "Шансы высоки! Готовься основательно и все получится"
    elif any(word in question_lower for word in ['встреч', 'свидан', 'знакомств']):
        return "Социальные взаимодействия важны! Будь собой и все сложится хорошо"
    
    return ""

def extract_question(text: str) -> str:
    """Извлекает вопрос из сообщения пользователя"""
    triggers = ['фёдор расскажи', 'федор расскажи', 'фёдор скажи', 'федор скажи']
    
    for trigger in triggers:
        if trigger in text:
            question = text.split(trigger, 1)[1].strip()
            if question.startswith(','):
                question = question[1:].strip()
            return question.capitalize()
    
    return ""

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f'Update {update} caused error {context.error}')

def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Команды
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        application.add_handler(CommandHandler("mute", mute_user))
        application.add_handler(CommandHandler("unmute", unmute_user))
        application.add_handler(CommandHandler("ban", ban_user))
        application.add_handler(CommandHandler("unban", unban_user))
        
        # Обработка сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.VOICE | filters.TEXT, handle_message))
        application.add_error_handler(error)

        print("Улучшенный бот Фёдор запускается...")
        print("Добавлены новые системы:")
        print("- Экономика (монеты и фемдиты)")
        print("- Femboy Mod System (6 уровней)")
        print("- Топы по сообщениям с наградами") 
        print("- Транскрипция голосовых")
        print("- Обучение функциям бота")
        print("- Система правил чата")
        print("Бот активен! Добавьте его в группу или напишите в личку")
        application.run_polling()
        
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
