import logging
import random
import re
import time
from datetime import datetime, timedelta
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8328982592:AAGXRR5pJmrQzqk6dknzDaxgVeS0Q_Gnda0"

# Система уровней модерации
MODERATION_LEVELS = {
    0: {"name": "Простолюдин", "permissions": []},
    1: {"name": "Комейдийнер", "permissions": ["warn", "mute_short"]},
    2: {"name": "Горничная", "permissions": ["warn", "mute_short", "mute_medium", "delete"]},
    3: {"name": "Фембой", "permissions": ["warn", "mute_short", "mute_medium", "mute_long", "delete", "kick"]},
    4: {"name": "Главарь фембоев", "permissions": ["warn", "mute_short", "mute_medium", "mute_long", "delete", "kick", "ban_temp"]},
    5: {"name": "Создатель", "permissions": ["warn", "mute_short", "mute_medium", "mute_long", "delete", "kick", "ban_temp", "ban_permanent", "promote", "demote"]}
}

# База данных прав пользователей (user_id -> level)
user_permissions = {}

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

CREATORS = {
    'koshkadevachka': 'ERROR',
    'роковой удар': 'электролит',
    'kartoshka': 'полюс',
    'сраньё': 'Дачи',
    'сранье': 'Дачи',
    'посрать': 'Дачи'
}

BODY_PARTS = ['яйца', 'жопу', 'нос', 'ухо', 'ногу', 'руку', 'мозг', 'сердце', 'легкие', 'зубы', 'язык', 'печень', 'почки', 'селезенку']
WEAPONS = ['пистолет', 'автомат', 'снайперскую винтовку', 'гранатомет', 'пулемет', 'дробовик', 'ракетницу']
LOCATIONS = ['с крыши', 'с вертолета', 'из подворотни', 'из засады', 'с чердака', 'из окна']

POTATO_IMAGES = [
    "https://via.placeholder.com/400/FFD700/000000?text=КАРТОШКА",
    "https://via.placeholder.com/400/8B4513/FFFFFF?text=КАРТОФЕЛЬ",
    "https://via.placeholder.com/400/FF6347/FFFFFF?text=БАТАТ",
    "https://via.placeholder.com/400/32CD32/FFFFFF?text=АРБУЗ+СЮРПРИЗ",
]

shit_counter = 0
last_shit_time = {}

koshka_devachka = {}

user_accounts = {}
user_join_dates = {}

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

MUTE_PHRASES = [
    "🔇 {user} отправлен в угол подумать о своем поведении на {time} минут! Причина: {reason}",
    "🤫 {user} получает тайм-аут на {time} минут за: {reason}",
    "🚫 {user} лишен права голоса на {time} минут. Нарушение: {reason}",
    "💂‍♂️ {user} отправлен в молчаливый отсек на {time} минут. Вина: {reason}",
    "🔒 {user} получает цифровой кляп на {time} минут. Основание: {reason}",
    "🎭 {user} отправлен за кулисы на {time} минут. Грех: {reason}",
    "⏰ {user} получает перерыв в общении на {time} минут. Причина: {reason}"
]

UNMUTE_PHRASES = [
    "🔊 {user} освобожден из тихого угла! Можете снова общаться!",
    "🎤 {user} возвращает право голоса! Больше не молчите!",
    "💬 {user} снова может говорить! Используйте эту возможность с умом!",
    "🗣️ {user} освобожден от обета молчания! Расскажите нам все новости!",
    "🎉 {user} возвращается в чат! Давайте поприветствуем!",
    "🌟 {user} снова с нами! Надеюсь, вы сделали правильные выводы!"
]

BAN_PHRASES = [
    "🚷 {user} изгнан из чата навсегда! Причина: {reason}",
    "💔 {user} покидает наше общество. Основание: {reason}",
    "☠️ {user} отправлен в цифровое небытие. Вина: {reason}",
    "🏴‍☠️ {user} становится пиратом одиноких морей. Причина: {reason}",
    "🚀 {user} запущен в космическое изгнание. Нарушение: {reason}",
    "🌋 {user} сброшен в жерло вулкана. Проступок: {reason}"
]

UNBAN_PHRASES = [
    "🤝 {user} прощен и может вернуться в чат!",
    "🕊️ {user} получает второй шанс! Добро пожаловать обратно!",
    "🌈 {user} возвращается из изгнания! Надеемся на лучшее!",
    "🎊 {user} снова с нами! Давайте устроим теплый прием!",
    "🌟 {user} получает амнистию! Рады видеть вас снова!"
]

KOSHKA_PHRASES = [
    "🎀 Сегодня кошкодевочкой становится {user}! Поздравляем! 😻",
    "🐾 Все внимание на {user} - новая кошкодевочка дня! 🎉",
    "👑 {user} удостоен(а) звания кошкодевочки! Носите с гордостью! 💫",
    "🌸 Символ дня - {user} в роли кошкодевочки! 🎀",
    "💕 {user} получает корону кошкодевочки! Поздравляем! 👑"
]

ACTION_PHRASES = {
    'расстрелять': [
        "🔫 {attacker} хладнокровно расстреливает {target} из {weapon}!",
        "💥 {attacker} открывает шквальный огонь по {target} из {weapon}!",
        "🎯 {attacker} метко попадает в {target} из {weapon} с расстояния 100 метров!",
        "🔥 {attacker} устраивает настоящую бойню для {target} с помощью {weapon}!",
        "⚡ {attacker} молниеносно расстреливает {target} из {weapon}!"
    ],
    'убить': [
        "💀 {attacker} жестоко убивает {target} ударом в {body_part}!",
        "☠️ {attacker} отправляет {target} на тот свет через {body_part}!",
        "🩸 {attacker} совершает хладнокровное убийство {target}!",
        "⚰️ {attacker} готовит могилу для {target} после смертельного удара!",
        "🌪️ {attacker} уничтожает {target} в схватке не на жизнь, а на смерть!"
    ],
    'сбросить ядерку': [
        "💣 {attacker} сбрасывает тактическую ядерку на позиции {target}!",
        "☢️ {attacker} запускает ядерную ракету по {target}!",
        "🌋 {attacker} вызывает ядерный апокалипсис для {target}!",
        "💥 {attacker} стирает {target} с лица земли ядерным ударом!",
        "🔥 {attacker} превращает местоположение {target} в радиоактивный пепел!"
    ],
    'раздавить': [
        "🐘 {attacker} сокрушительно раздавливает {target} как букашку!",
        "🏔️ {attacker} давит {target} с силой горного обвала!",
        "💥 {attacker} расплющивает {target} в лепешку!",
        "🦏 {attacker} топчет {target} как носорог!",
        "🌊 {attacker} сминает {target} мощным прессом!"
    ],
    'уничтожить': [
        "💥 {attacker} полностью уничтожает {target} до молекулярного уровня!",
        "🔥 {attacker} стирает {target} в порошок!",
        "⚡ {attacker} аннигилирует {target} с помощью плазменной пушки!",
        "🌪️ {attacker} разрывает {target} на атомы!",
        "💫 {attacker} отправляет {target} в небытие!"
    ],
    'погладить': [
        "🐱 {attacker} нежно гладит {target} по головке! 😊",
        "💕 {attacker} ласково поглаживает {target}!",
        "✨ {attacker} дарит {target} приятные поглаживания!",
        "🌟 {attacker} нежно гладит {target}, вызывая улыбку!",
        "😻 {attacker} поглаживает {target} с любовью и заботой!"
    ],
    'похвалить': [
        "👏 {attacker} хвалит {target} за отличную работу!",
        "🎉 {attacker} аплодирует {target} стоя!",
        "⭐ {attacker} признает великолепные качества {target}!",
        "🏆 {attacker} вручает {target} воображаемый кубок за успехи!",
        "💫 {attacker} восхищается талантами {target}!"
    ],
    'похлопать по плечу': [
        "🤝 {attacker} дружески хлопает {target} по плечу!",
        "💪 {attacker} ободряюще похлопывает {target} по плечу!",
        "👊 {attacker} по-братски хлопает {target} по плечу!",
        "😄 {attacker} поддерживающе похлопывает {target} по плечу!",
        "🌟 {attacker} одобрительно хлопает {target} по плечу!"
    ],
    'отказать уважение': [
        "🖕 {attacker} демонстративно отказывает в уважении {target}!",
        "😾 {attacker} показывает {target}, что не уважает его!",
        "👎 {attacker} открыно выражает неуважение к {target}!",
        "💢 {attacker} пренебрежительно относится к {target}!",
        "🚫 {attacker} отказывает {target} в элементарном уважении!"
    ]
}

# Фразы для функции "инфа"
INFO_PHRASES = [
    "🔮 Вероятность: {percent}%",
    "🎯 Шансы: {percent}%", 
    "📊 Прогноз: {percent}%",
    "💫 Шанс: {percent}%",
    "🎰 Вероятность: {percent}%",
    "📈 Прогнозирую: {percent}%",
    "🔍 Анализ показывает: {percent}%",
    "🎲 Случайность говорит: {percent}%"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_type = update.message.chat.type

    if chat_type == 'private':
        await update.message.reply_text(
            f"Привет, {user.first_name}!\n\n"
            f"Я Фёдор - бот с продвинутой системой модерации!\n\n"
            f"Система уровней модерации:\n"
            f"0️⃣ Простолюдин - базовые права\n"
            f"1️⃣ Комейдийнер - варны, короткие муты\n"
            f"2️⃣ Горничная - +средние муты, удаление\n"
            f"3️⃣ Фембой - +длинные муты, кик\n"
            f"4️⃣ Главарь фембоев - +временные баны\n"
            f"5️⃣ Создатель - +пермабаны, повышение прав\n\n"
            f"Команды модерации:\n"
            f"• /warn @user причина\n"
            f"• /mute @user время(м) причина\n"
            f"• /unmute @user\n"
            f"• /kick @user причина\n"
            f"• /ban @user причина\n"
            f"• /unban @user\n"
            f"• /promote @user уровень\n"
            f"• /demote @user\n"
            f"• /mylevel - ваш уровень\n"
            f"• /modlist - список модераторов\n\n"
            f"Развлекательные функции:\n"
            f"• Фёдор инфа [вопрос] - оценка вероятности\n"
            f"• kartoshka - получить картошку\n"
            f"• Koshkaдевачка - стать кошкодевочкой\n"
            f"• Действия через ответ на сообщение"
        )
    else:
        await update.message.reply_text(
            "Привет всем! Я Фёдор - бот с продвинутой системой модерации!\n\n"
            "Развлекательные команды:\n"
            "• Ответь на сообщение с действием: 'расстрелять', 'убить', 'сбросить ядерку', 'раздавить', 'уничтожить', 'погладить', 'похвалить', 'похлопать по плечу', 'отказать уважение'\n"
            "• 'kartoshka' - получить картошку\n"
            "• 'Посрать' - добавить сранье (раз в 4 часа)\n"
            "• 'сранье статус' - статистика сранья\n"
            "• 'Koshkaдевачка' - стать кошкодевочкой дня\n"
            "• 'аккаунт' - посмотреть свой аккаунт\n"
            "• 'Фёдор инфа [вопрос]' - оценка вероятности\n\n"
            "Модерация:\n"
            "• /warn @user причина\n"
            "• /mute @user время(м) причина\n"
            "• /unmute @user\n"
            "• /kick @user причина\n"
            "• /ban @user причина\n"
            "• /promote @user уровень\n"
            "• /mylevel - ваш уровень\n\n"
            "Обращайтесь ко мне: 'Фёдор [вопрос]' или 'Федор [вопрос]'"
        )

# ===== СИСТЕМА ПРАВ И УРОВНЕЙ =====

async def get_user_level(update: Update, user_id: int) -> int:
    """Получает уровень пользователя"""
    chat_id = update.message.chat.id
    
    # Создатель чата всегда имеет уровень 5
    try:
        chat_member = await update.message.chat.get_member(user_id)
        if chat_member.status == 'creator':
            return 5
    except:
        pass
    
    # Проверяем установленные права
    if user_id in user_permissions:
        return user_permissions[user_id]
    
    # По умолчанию все пользователи имеют уровень 0
    return 0

async def check_permission(update: Update, user_id: int, permission: str) -> bool:
    """Проверяет наличие прав у пользователя"""
    user_level = await get_user_level(update, user_id)
    user_perms = MODERATION_LEVELS[user_level]["permissions"]
    
    return permission in user_perms

async def can_moderate_target(update: Update, moderator_id: int, target_id: int) -> bool:
    """Проверяет, может ли модератор модерировать цель"""
    moderator_level = await get_user_level(update, moderator_id)
    target_level = await get_user_level(update, target_id)
    
    return moderator_level > target_level

async def promote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Повышение уровня пользователя"""
    if not await check_permission(update, update.message.from_user.id, "promote"):
        await update.message.reply_text("❌ У вас нет прав для повышения уровня!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /promote @username уровень(1-5)")
        return
    
    target_username = context.args[0]
    try:
        new_level = int(context.args[1])
        if new_level < 1 or new_level > 5:
            await update.message.reply_text("❌ Уровень должен быть от 1 до 5!")
            return
    except ValueError:
        await update.message.reply_text("❌ Уровень должен быть числом!")
        return
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    promoter_level = await get_user_level(update, update.message.from_user.id)
    if new_level >= promoter_level:
        await update.message.reply_text("❌ Вы не можете повысить до уровня выше или равного вашему!")
        return
    
    # Устанавливаем новый уровень
    user_permissions[target_user.id] = new_level
    
    level_name = MODERATION_LEVELS[new_level]["name"]
    await update.message.reply_text(
        f"🎉 {target_user.first_name} повышен до уровня {new_level} - {level_name}!\n"
        f"Теперь доступны: {', '.join(MODERATION_LEVELS[new_level]['permissions'])}"
    )

async def demote_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Понижение уровня пользователя"""
    if not await check_permission(update, update.message.from_user.id, "demote"):
        await update.message.reply_text("❌ У вас нет прав для понижения уровня!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /demote @username")
        return
    
    target_username = context.args[0]
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    if not await can_moderate_target(update, update.message.from_user.id, target_user.id):
        await update.message.reply_text("❌ Вы не можете понизить этого пользователя!")
        return
    
    # Сбрасываем уровень до 0
    user_permissions[target_user.id] = 0
    
    await update.message.reply_text(
        f"📉 {target_user.first_name} понижен до уровня 0 - Простолюдин!\n"
        f"Все специальные права сняты."
    )

async def show_my_level(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает текущий уровень пользователя"""
    user_id = update.message.from_user.id
    user_level = await get_user_level(update, user_id)
    level_info = MODERATION_LEVELS[user_level]
    
    permissions_text = "\n".join([f"• {perm}" for perm in level_info["permissions"]]) if level_info["permissions"] else "• Нет специальных прав"
    
    await update.message.reply_text(
        f"👤 Ваш уровень: {user_level} - {level_info['name']}\n"
        f"📋 Доступные права:\n{permissions_text}"
    )

async def show_mod_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список модераторов"""
    moderators = []
    
    # Собираем всех пользователей с уровнем > 0
    for user_id, level in user_permissions.items():
        if level > 0:
            try:
                user = await update.message.chat.get_member(user_id)
                moderators.append((user.user.first_name, level))
            except:
                continue
    
    # Добавляем создателя чата
    try:
        chat_creator = await update.message.chat.get_member(update.message.chat.id)
        if chat_creator.status == 'creator':
            moderators.append((chat_creator.user.first_name, 5))
    except:
        pass
    
    if not moderators:
        await update.message.reply_text("📋 В этом чате пока нет модераторов.")
        return
    
    moderators.sort(key=lambda x: x[1], reverse=True)
    mod_list = "\n".join([f"• {name} - уровень {level} ({MODERATION_LEVELS[level]['name']})" for name, level in moderators])
    
    await update.message.reply_text(f"📋 Список модераторов:\n{mod_list}")

# ===== КОМАНДЫ МОДЕРАЦИИ =====

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выдача предупреждения"""
    if not await check_permission(update, update.message.from_user.id, "warn"):
        await update.message.reply_text("❌ У вас нет прав для выдачи предупреждений!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /warn @username причина")
        return
    
    target_username = context.args[0]
    reason = ' '.join(context.args[1:])
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    if not await can_moderate_target(update, update.message.from_user.id, target_user.id):
        await update.message.reply_text("❌ Вы не можете выдать предупреждение этому пользователю!")
        return
    
    await update.message.reply_text(
        f"⚠️ {target_user.first_name} получает предупреждение!\n"
        f"📝 Причина: {reason}\n"
        f"🎯 Выдал: {update.message.from_user.first_name}"
    )

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Мут пользователя"""
    if len(context.args) < 3:
        await update.message.reply_text("Использование: /mute @username время_в_минутах причина")
        return
    
    target_username = context.args[0]
    try:
        mute_minutes = int(context.args[1])
        reason = ' '.join(context.args[2:])
    except ValueError:
        await update.message.reply_text("❌ Время должно быть числом (минуты)")
        return
    
    # Определяем необходимые права в зависимости от времени мута
    if mute_minutes <= 60:
        required_permission = "mute_short"
    elif mute_minutes <= 360:
        required_permission = "mute_medium"
    else:
        required_permission = "mute_long"
    
    if not await check_permission(update, update.message.from_user.id, required_permission):
        await update.message.reply_text(f"❌ У вас нет прав для {mute_minutes}-минутного мута!")
        return
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    if not await can_moderate_target(update, update.message.from_user.id, target_user.id):
        await update.message.reply_text("❌ Вы не можете замутить этого пользователя!")
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
            time=mute_minutes,
            reason=reason
        )
        await update.message.reply_text(phrase)
        
    except Exception as e:
        logger.error(f"Mute error: {e}")
        await update.message.reply_text("❌ Ошибка при муте пользователя")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Размут пользователя"""
    if not await check_permission(update, update.message.from_user.id, "mute_short"):
        await update.message.reply_text("❌ У вас нет прав для размута!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /unmute @username")
        return
    
    target_username = context.args[0]
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
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
        await update.message.reply_text("❌ Ошибка при размуте пользователя")

async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Кик пользователя"""
    if not await check_permission(update, update.message.from_user.id, "kick"):
        await update.message.reply_text("❌ У вас нет прав для кика!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /kick @username причина")
        return
    
    target_username = context.args[0]
    reason = ' '.join(context.args[1:])
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    if not await can_moderate_target(update, update.message.from_user.id, target_user.id):
        await update.message.reply_text("❌ Вы не можете кикнуть этого пользователя!")
        return
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id,
            until_date=datetime.now() + timedelta(minutes=1)
        )
        
        await context.bot.unban_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id
        )
        
        await update.message.reply_text(
            f"👢 {target_user.first_name} был кикнут из чата!\n"
            f"📝 Причина: {reason}\n"
            f"🎯 Кикнул: {update.message.from_user.first_name}"
        )
        
    except Exception as e:
        logger.error(f"Kick error: {e}")
        await update.message.reply_text("❌ Ошибка при кике пользователя")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Бан пользователя"""
    if len(context.args) < 2:
        await update.message.reply_text("Использование: /ban @username причина")
        return
    
    target_username = context.args[0]
    reason = ' '.join(context.args[1:])
    
    # Определяем тип бана (временный или перманентный)
    is_permanent = await check_permission(update, update.message.from_user.id, "ban_permanent")
    required_permission = "ban_permanent" if is_permanent else "ban_temp"
    
    if not await check_permission(update, update.message.from_user.id, required_permission):
        await update.message.reply_text("❌ У вас нет прав для бана!")
        return
    
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
        return
    
    if not await can_moderate_target(update, update.message.from_user.id, target_user.id):
        await update.message.reply_text("❌ Вы не можете забанить этого пользователя!")
        return
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat.id,
            user_id=target_user.id,
            until_date=None if is_permanent else datetime.now() + timedelta(days=7)
        )
        
        ban_type = "навсегда" if is_permanent else "на 7 дней"
        await update.message.reply_text(
            f"🚫 {target_user.first_name} забанен {ban_type}!\n"
            f"📝 Причина: {reason}\n"
            f"🎯 Забанил: {update.message.from_user.first_name}"
        )
        
    except Exception as e:
        logger.error(f"Ban error: {e}")
        await update.message.reply_text("❌ Ошибка при бане пользователя")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разбан пользователя"""
    if not await check_permission(update, update.message.from_user.id, "ban_temp"):
        await update.message.reply_text("❌ У вас нет прав для разбана!")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text("Использование: /unban @username")
        return
    
    target_username = context.args[0]
    target_user = await get_user_from_mention(update, context, target_username)
    if not target_user:
        await update.message.reply_text("❌ Пользователь не найден!")
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
        await update.message.reply_text("❌ Ошибка при разбане пользователя")

# ===== ФУНКЦИЯ "ИНФА" =====

async def handle_info_request(update: Update, message_text: str, user):
    """Обработка запроса 'инфа'"""
    # Извлекаем вопрос после 'инфа'
    question = message_text.replace('фёдор инфа', '').replace('федор инфа', '').replace('инфа', '').strip()
    
    if not question:
        responses = [
            "Задай вопрос после 'инфа', братишка!",
            "Что хочешь узнать? Напиши после 'инфа'!",
            "Инфа о чем? Задай вопрос!"
        ]
        await update.message.reply_text(random.choice(responses))
        return
    
    # Генерируем "случайную" вероятность на основе хеша вопроса
    question_hash = hash(question) % 100
    probability = abs(question_hash) % 101  # От 0 до 100%
    
    # Добавляем немного "интеллекта" - анализируем ключевые слова
    if any(word in question.lower() for word in ['соль', 'проигра', 'поражен', 'не получит']):
        probability = max(0, probability - 20)
    elif any(word in question.lower() for word in ['выигра', 'побед', 'успех', 'получит']):
        probability = min(100, probability + 20)
    elif any(word in question.lower() for word in ['любов', 'встреч', 'свидан']):
        probability = 50 + (probability - 50) // 2  # Сдвигаем к 50%
    
    phrase = random.choice(INFO_PHRASES).format(percent=probability)
    
    # Добавляем эмоциональную реакцию в зависимости от вероятности
    if probability >= 80:
        reaction = "🎉 Высокий шанс! Верь в успех!"
    elif probability >= 60:
        reaction = "👍 Хорошие шансы! Можно пробовать!"
    elif probability >= 40:
        reaction = "🤔 Шансы 50/50... Решай сам!"
    elif probability >= 20:
        reaction = "👎 Маловато шансов... Подумай еще!"
    else:
        reaction = "💀 Практически нет шансов... Не стоит!"
    
    response = f"📊 На вопрос: '{question}'\n{phrase}\n{reaction}"
    
    await update.message.reply_text(response)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def get_user_from_mention(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Получает пользователя из упоминания"""
    clean_username = username.lstrip('@')
    try:
        # В реальной реализации здесь должен быть поиск пользователя по username
        # Для демонстрации возвращаем отправителя команды
        return update.message.from_user
    except Exception as e:
        logger.error(f"User lookup error: {e}")
        return None

def is_direct_address(message_text: str) -> bool:
    """Проверяет, обращаются ли к боту напрямую"""
    direct_triggers = [
        'фёдор', 'федор', 'фёдор,', 'федор,', 'фёдор!', 'федор!',
        'фёдор:', 'федор:', 'фёдор ', 'федор '
    ]
    
    for trigger in direct_triggers:
        if message_text.lower().startswith(trigger):
            return True
    
    if any(mention in message_text.lower() for mention in ['@', 'бот']):
        return True
    
    return False

async def handle_direct_address(update: Update, message_text: str, user):
    """Обработка прямых обращений к боту в группах"""
    clean_text = message_text.lower()
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
    
    # Проверяем запрос "инфа"
    if 'инфа' in clean_text:
        await handle_info_request(update, message_text, user)
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

# ===== РАЗВЛЕКАТЕЛЬНЫЕ ФУНКЦИИ =====

async def handle_award_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    """Обработка награждения через ответ на сообщение"""
    try:
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
        
        target_user = update.message.reply_to_message.from_user
        target_user_id = target_user.id
        
        if target_user_id not in user_accounts:
            user_accounts[target_user_id] = {'awards': []}
        
        user_accounts[target_user_id]['awards'].append(award_name)
        
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

async def handle_account(update: Update, user_id: int, chat_id: int):
    """Показывает аккаунт пользователя"""
    if chat_id not in user_join_dates or user_id not in user_join_dates[chat_id]:
        await update.message.reply_text("❌ Информация о вашем аккаунте не найдена!")
        return
    
    join_timestamp = user_join_dates[chat_id][user_id]
    join_date = datetime.fromtimestamp(join_timestamp).strftime("%d.%m.%Y %H:%M")
    days_in_chat = int((time.time() - join_timestamp) / (24 * 3600))
    rank = get_user_rank(join_timestamp)
    
    awards_text = "Нет наград"
    if user_id in user_accounts and 'awards' in user_accounts[user_id]:
        awards = user_accounts[user_id]['awards']
        if awards:
            awards_text = "\n".join([f"• {award}" for award in awards])
    
    account_info = (
        f"👤 Аккаунт {update.message.from_user.first_name}\n"
        f"📅 В чате с: {join_date}\n"
        f"⏰ Дней в чате: {days_in_chat}\n"
        f"🎖️ Звание: {rank}\n"
        f"🏆 Награды:\n{awards_text}"
    )
    
    await update.message.reply_text(account_info)

async def handle_action_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str):
    """Обработка действий через ответ на сообщение"""
    try:
        attacker = update.message.from_user
        attacker_name = attacker.first_name
        
        target_message = update.message.reply_to_message
        target_user = target_message.from_user
        target_name = target_user.first_name
        
        phrases = ACTION_PHRASES[action]
        phrase_template = random.choice(phrases)
        
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
        attacker = update.message.from_user
        attacker_name = attacker.first_name
        
        target_message = update.message.reply_to_message
        target_user = target_message.from_user
        target_name = target_user.first_name
        
        body_part = random.choice(BODY_PARTS)
        
        strike_message = random.choice(ACTION_PHRASES['убить']).format(
            attacker=attacker_name,
            target=target_name,
            body_part=body_part
        )
        
        await update.message.reply_text(
            strike_message,
            reply_to_message_id=target_message.message_id
        )
        
    except Exception as e:
        logger.error(f"Error in fatal strike reply: {e}")
        await update.message.reply_text("Ошибка при выполнении рокового удара!")

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
    # Проверяем запрос "инфа"
    if 'инфа' in message_text.lower():
        await handle_info_request(update, message_text, user)
        return
    
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    message_text = update.message.text.lower().strip()
    user = update.message.from_user
    user_id = user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type

    await update_user_join_date(update, user_id, chat_id)

    # Обработка награждения через ответ на сообщение
    if update.message.reply_to_message and message_text.startswith('наградить'):
        if await check_permission(update, user_id, "promote"):
            await handle_award_reply(update, context, message_text)
        else:
            await update.message.reply_text("❌ Только модераторы могут выдавать награды!")
        return

    # Обработка действий через ответ на сообщение
    if update.message.reply_to_message:
        for action in ACTION_PHRASES.keys():
            if action in message_text:
                await handle_action_reply(update, context, action)
                return
        
        if 'роковой удар' in message_text:
            await handle_fatal_strike_reply(update, context)
            return
    
    # Специальные команды
    special_commands = [
        'kartoshka', 'картошк', 'посрать', 'сранье статус', 'сраньё статус',
        'koshkadevachka', 'кошкодевочка', 'кто сегодня кошкодевочка', 'кто кошкодевочка',
        'аккаунт', 'профиль'
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
        elif 'аккаунт' in message_text or 'профиль' in message_text:
            await handle_account(update, user_id, chat_id)
            return
    
    # Обработка обычных сообщений
    if chat_type == 'private':
        if any(greeting in message_text for greeting in ['привет', 'здравствуй', 'hello', 'hi']):
            await handle_greeting(update, user)
        elif any(trigger in message_text for trigger in ['фёдор', 'федор']):
            await handle_fedor_request(update, message_text, user)
        else:
            await handle_smart_response(update, message_text, user)
        return
    
    if chat_type in ['group', 'supergroup']:
        if is_direct_address(message_text):
            await handle_direct_address(update, message_text, user)
        return

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ошибок"""
    logger.error(f'Update {update} caused error {context.error}')

def main():
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Команды модерации
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", start))
        application.add_handler(CommandHandler("warn", warn_user))
        application.add_handler(CommandHandler("mute", mute_user))
        application.add_handler(CommandHandler("unmute", unmute_user))
        application.add_handler(CommandHandler("kick", kick_user))
        application.add_handler(CommandHandler("ban", ban_user))
        application.add_handler(CommandHandler("unban", unban_user))
        application.add_handler(CommandHandler("promote", promote_user))
        application.add_handler(CommandHandler("demote", demote_user))
        application.add_handler(CommandHandler("mylevel", show_my_level))
        application.add_handler(CommandHandler("modlist", show_mod_list))

        # Обработка сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_error_handler(error)

        print("Бот Фёдор с полной системой модерации запускается...")
        print("Добавлена функция 'инфа' для оценки вероятностей!")
        print("Система уровней модерации:")
        for level, info in MODERATION_LEVELS.items():
            print(f"Уровень {level}: {info['name']} - {', '.join(info['permissions'])}")
        print("Бот активен! Добавьте его в группу или напишите в личку")
        application.run_polling()

    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
