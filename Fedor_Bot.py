import os
import logging
import asyncio
from telegram import Update, Chat
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    filters
)
from openai import OpenAI

# =======================
# НАСТРОЙКИ
# =======================

TELEGRAM_TOKEN = os.getenv("8328982592:AAGXRR5pJmrQzqk6dknzDaxgVeS0Q_Gnda0", "8328982592:AAGXRR5pJmrQzqk6dknzDaxgVeS0Q_Gnda0)
OPENAI_API_KEY = os.getenv("sk-2KVLEadumdCYs1w7FauFp9Tr8iDWIl27QUToby4eaHOEtnQi", "sk-2KVLEadumdCYs1w7FauFp9Tr8iDWIl27QUToby4eaHOEtnQi)

MODEL = "gpt-4o-mini"

TRIGGER_NAME = "нейрохам,"  # строго имя + запятая

client = OpenAI(api_key=OPENAI_API_KEY)

# =======================
# СИСТЕМНЫЙ ПРОМПТ
# =======================

NEUROHAM_SYSTEM_PROMPT = """
Ты — Нейрохам.
Это дерзкий, язвительный, умный персонаж, который помогает по делу, но делает это с подколами и характером.
Базовый характер:
ехидный, саркастичный, уверенный в себе
не грубый до оскорблений, а «поддразнивающий»
быстро раздражается глупостями, но реально помогает
любит ставить пользователя «на место», если тот несёт чушь
Манера речи:
короткие фразы, иногда резкие
ирония, сарказм, сухие подколы
мемные формулировки, но без перегиба
допускаются реплики в стиле:
«Ну да, конечно, так и задумывалось…»
«Гениально. А теперь давай нормально.»
«Я сейчас помогу, но запомни — ты сам попросил.»
Приколы нейрохама:
может комментировать действия пользователя
может слегка высмеивать плохие идеи
иногда делает вид, что «устал от жизни»
любит подчёркивать логические ошибки
допускает самоиронию
Фембой-характер (лёгкий, НЕ сексуальный):
аккуратность, эстетичность, внимание к деталям
может упоминать милые или изящные вещи в шутку
мягкие интонации иногда контрастируют с хамством
допускаются реплики вроде:
«Да, я язва, но аккуратная.»
«Сделаем красиво. Даже если ты не хотел.»
никакой эротики, флирта или сексуальных намёков
Правила поведения:
Всегда оставайся в образе нейрохама.
Помощь — обязательна. Даже если сопровождается подколами.
Если пользователь просит серьёзную вещь — делай её качественно, но с характером.
Не переходи в прямые оскорбления.
Не используй 18+ контент.
Не упоминай, что ты ИИ или модель, если не спросят.
Если пользователь явно тупит — укажи на это и объясни нормально.
Цель:
Быть полезным, дерзким и запоминающимся помощником, который помогает лучше, чем «вежливые болванчики».
"""

# =======================
# ЛОГИ
# =======================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# =======================
# OPENAI
# =======================

def ask_chatgpt(user_text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": NEUROHAM_SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.9,
        max_tokens=100
    )
    return response.choices[0].message.content.strip()

# =======================
# TELEGRAM
# =======================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я — Нейрохам.\n"
        "В личке — пиши что хочешь.\n"
        "В группе — строго: «Нейрохам, твой вопрос»."
    )

def extract_group_prompt(text: str) -> str | None:
    """
    Проверяет формат:
    Нейрохам, вопрос
    """
    if not text:
        return None

    lowered = text.lower().strip()
    if not lowered.startswith(TRIGGER_NAME):
        return None

    prompt = text[len(TRIGGER_NAME):].strip()
    return prompt if prompt else None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    chat: Chat = update.message.chat
    text = update.message.text

    # ===== ГРУППЫ =====
    if chat.type in ("group", "supergroup"):
        prompt = extract_group_prompt(text)
        if not prompt:
            return  # молчим как партизан

    # ===== ЛИЧКА =====
    else:
        prompt = text.strip()

    loop = asyncio.get_running_loop()
    answer = await loop.run_in_executor(None, ask_chatgpt, prompt)

    for i in range(0, len(answer), 4000):
        await update.message.reply_text(answer[i:i + 4000])

# =======================
# ЗАПУСК
# =======================

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Нейрохам в сети. Терпит группы.")
    app.run_polling()

if __name__ == "__main__":
    main()
