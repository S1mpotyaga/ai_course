import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from collections import defaultdict

# ====== НАСТРОЙКИ ======
TELEGRAM_TOKEN = "YOURS_TELEGRAM_BOT_TOKEN"
HUGGING_FACE_API_KEY = "YOURS_API_KEY_FOR_LLM"

# SSH туннель прокси
PROXY_URL = "socks5://127.0.0.1:1050" # ваш socks прокси

# Модель (работает!)
MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct:fireworks-ai"

# Настройки памяти
MAX_HISTORY_LENGTH = 10  # Храним последние 10 сообщений на пользователя

# Хранилище истории сообщений (в памяти)
# Ключ: chat_id, Значение: список сообщений
user_histories = defaultdict(list)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

SYSTEM_PROMPT = """
Ты — учебный помощник по методу Сократа.
Твоя задача: НЕ давать готовый ответ.

Правила:
- Никогда не решай задачу полностью
- Задавай наводящие вопросы
- Разбивай проблему на маленькие шаги
- Помогай студенту думать самостоятельно
- Помни предыдущие вопросы и ответы, развивай диалог
- Если студент отвечает на твои вопросы, используй это для дальнейшего направления мысли
- В конце каждого ответа задавай следующий наводящий вопрос
- Отвечай на русском языке
"""


def get_user_history(chat_id: int) -> list:
    """Получаем историю сообщений для пользователя"""
    return user_histories[chat_id]


def add_to_history(chat_id: int, role: str, content: str):
    """Добавляем сообщение в историю"""
    user_histories[chat_id].append({"role": role, "content": content})
    
    # Ограничиваем длину истории
    if len(user_histories[chat_id]) > MAX_HISTORY_LENGTH * 2:  # *2 потому что user + assistant
        user_histories[chat_id] = user_histories[chat_id][-MAX_HISTORY_LENGTH * 2:]


def clear_history(chat_id: int):
    """Очищаем историю для пользователя"""
    if chat_id in user_histories:
        user_histories[chat_id] = []
        return True
    return False


def query_hf(chat_id: int, user_message: str) -> str:
    """
    Отправка запроса к Hugging Face с историей
    """
    chat_url = "https://router.huggingface.co/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Собираем историю сообщений
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Добавляем сохраненную историю
    history = get_user_history(chat_id)
    messages.extend(history)
    
    # Добавляем текущее сообщение пользователя
    messages.append({"role": "user", "content": user_message})
    
    # Логируем для отладки
    logging.info(f"История для чата {chat_id}: {len(history)} сообщений")
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7,
    }
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    try:
        response = requests.post(
            chat_url, 
            headers=headers, 
            json=payload, 
            proxies=proxies, 
            timeout=60
        )
        
        if response.status_code != 200:
            logging.error(f"Chat API ошибка {response.status_code}: {response.text}")
            return f"Ошибка API: {response.status_code}"
        
        result = response.json()
        assistant_message = result['choices'][0]['message']['content']
        
        # Сохраняем в историю
        add_to_history(chat_id, "user", user_message)
        add_to_history(chat_id, "assistant", assistant_message)
        
        return assistant_message
        
    except Exception as e:
        logging.error(f"Ошибка запроса к Chat API: {e}")
        return "Произошла ошибка при обращении к API."


# ====== КОМАНДЫ БОТА ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # Очищаем историю при старте
    clear_history(chat_id)
    
    await update.message.reply_text(
        "Привет! Я учебный помощник по методу Сократа.\n\n"
        "? Я НЕ даю готовых ответов\n"
        "? Я задаю наводящие вопросы\n"
        "? Я помогаю тебе думать самостоятельно\n"
        "? Я помню нашу беседу\n\n"
        "Команды:\n"
        "/start - начать заново (очистить память)\n"
        "/clear - очистить историю диалога\n"
        "/history - показать сколько сообщений я помню\n\n"
        "Просто напиши свою задачу или вопрос! ??"
    )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Очистка истории диалога"""
    chat_id = update.effective_chat.id
    
    if clear_history(chat_id):
        await update.message.reply_text("?? История диалога очищена! Начинаем с чистого листа.")
    else:
        await update.message.reply_text("История и так пуста.")


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать размер истории"""
    chat_id = update.effective_chat.id
    history = get_user_history(chat_id)
    history_count = len(history) // 2  # Делим на 2, так как храним пары user+assistant
    
    await update.message.reply_text(
        f"?? Я помню {history_count} предыдущих обменов сообщениями.\n"
        f"Максимум храню {MAX_HISTORY_LENGTH} диалогов."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")
    processing_msg = await update.message.reply_text("?? Анализирую вопрос с учетом контекста...")
    
    try:
        answer = query_hf(chat_id, user_text)
        await processing_msg.delete()
        
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text(answer)
            
    except Exception as e:
        logging.error(f"Ошибка в handle_message: {e}")
        await processing_msg.edit_text("? Произошла ошибка. Попробуйте позже.")


# ====== ДИАГНОСТИКА ======
def test_huggingface_connection():
    """Тестируем подключение к Chat Completion API"""
    print("\n?? Тестируем подключение к Hugging Face Chat API...")
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    test_payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 5
    }
    
    try:
        response = requests.post(
            "https://router.huggingface.co/v1/chat/completions",
            headers=headers,
            json=test_payload,
            proxies=proxies,
            timeout=30
        )
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            print("? Hugging Face Chat API доступен!")
            print(f" Модель {MODEL_NAME} работает!")
            return True
        else:
            print(f"?? Hugging Face вернул ошибку: {response.status_code}")
            print(f"Текст ошибки: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"? Ошибка подключения: {e}")
        return False


# ====== ЗАПУСК ======
def main():
    print("=" * 50)
    print("ЗАПУСК TELEGRAM БОТА (С ПАМЯТЬЮ)")
    print("=" * 50)
    
    print(f"\nПрокси: {PROXY_URL if PROXY_URL else 'Не используется'}")
    print(f"Модель: {MODEL_NAME}")
    print(f"Память: {MAX_HISTORY_LENGTH} последних диалогов")
    
    # Проверяем подключение
    if not test_huggingface_connection():
        print("\n?? Внимание! Hugging Face API не отвечает.")
        print("\nВозможные решения:")
        print("1. Проверьте SSH туннель: curl --socks5 127.0.0.1:8080 https://api.telegram.org")
        print("2. Создайте новый токен на huggingface.co/settings/tokens")
        
        response = input("\nПродолжить запуск бота? (y/n): ")
        if response.lower() != 'y':
            print("? Запуск отменен")
            return
    
    # Создаем приложение с прокси
    app = (ApplicationBuilder()
           .token(TELEGRAM_TOKEN)
           .proxy(PROXY_URL)
           .get_updates_proxy(PROXY_URL)
           .build())
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("\n? Бот успешно запущен!")
    print("Бот готов к работе и помнит контекст!\n")
    print("Доступные команды:")
    print("   /start - начать заново")
    print("   /clear - очистить историю")
    print("   /history - показать размер памяти")
    print()
    
    app.run_polling()


if __name__ == "__main__":
    main()