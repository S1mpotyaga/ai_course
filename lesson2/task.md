
УРОВЕНЬ 1: Базовый Telegram-бот с интеграцией Hugging Face


ЗАДАНИЕ: Замените все {TODO} на соответствующие значения


```python
import logging
import requests
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from collections import defaultdict

# Загрузка переменных окружения
load_dotenv()

# ====== НАСТРОЙКИ ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
PROXY_URL = os.getenv("PROXY_URL", "socks5://127.0.0.1:8080")

# Проверка наличия обязательных переменных
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не найден в .env файле")
if not HUGGING_FACE_API_KEY:
    raise ValueError("HUGGING_FACE_API_KEY не найден в .env файле")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Настройки модели
MODEL_NAME = "meta-llama/Llama-3.3-70B-Instruct:fireworks-ai"
CHAT_API_URL = "https://router.huggingface.co/v1/chat/completions"

# Настройки памяти
MAX_HISTORY_LENGTH = 10  # Храним последние 10 обменов сообщениями
user_histories = defaultdict(list)  # Словарь для хранения истории каждого пользователя

print("✅ Конфигурация загружена успешно")
print(f"📡 Модель: {MODEL_NAME}")
print(f"🔒 Прокси: {PROXY_URL}")

# ====== СИСТЕМНЫЙ ПРОМПТ ======
SYSTEM_PROMPT = {TODO: напишите промт для ии, чтобы он был помощником в обучении, а не давал готовые ответы и решения.}

# ====== ФУНКЦИИ ПАМЯТИ ======

def get_user_history(chat_id: int) -> list:
    """
    Получает историю сообщений для конкретного пользователя.
    
    Args:
        chat_id: ID чата Telegram
        
    Returns:
        list: Список сообщений в формате [{"role": "user/assistant", "content": "..."}]
    """
    return user_histories[chat_id]


def add_to_history(chat_id: int, role: str, content: str):
    """
    Добавляет сообщение в историю пользователя.
    
    Args:
        chat_id: ID чата Telegram
        role: Роль отправителя ("user" или "assistant")
        content: Текст сообщения
    """
    user_histories[chat_id].append({"role": role, "content": content})
    
    # Ограничиваем длину истории (удаляем старые сообщения)
    if len(user_histories[chat_id]) > MAX_HISTORY_LENGTH * 2:
        user_histories[chat_id] = user_histories[chat_id][-MAX_HISTORY_LENGTH * 2:]


def clear_history(chat_id: int) -> bool:
    """
    Очищает историю сообщений для пользователя.
    
    Args:
        chat_id: ID чата Telegram
        
    Returns:
        bool: True если история была очищена, False если она уже была пуста
    """
    if chat_id in user_histories and user_histories[chat_id]:
        user_histories[chat_id] = []
        return True
    return False

# ====== ФУНКЦИЯ ЗАПРОСА К HUGGING FACE ======

def query_hf(chat_id: int, user_message: str) -> str:
    """
    Отправляет запрос к Hugging Face API с учетом истории диалога.
    
    Args:
        chat_id: ID чата Telegram
        user_message: Текст сообщения пользователя
        
    Returns:
        str: Ответ от модели
    """
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Формируем список сообщений: системный промпт + история + текущее сообщение
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(get_user_history(chat_id))
    messages.append({"role": "user", "content": user_message})
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.95,
        "do_sample": True
    }
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    
    try:
        response = requests.post(
            CHAT_API_URL,
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"HF API ошибка {response.status_code}: {response.text[:200]}")
            return f"Ошибка API: {response.status_code}"
        
        result = response.json()
        assistant_message = result['choices'][0]['message']['content']
        
        # Сохраняем сообщения в историю
        add_to_history(chat_id, "user", user_message)
        add_to_history(chat_id, "assistant", assistant_message)
        
        return assistant_message
        
    except requests.exceptions.Timeout:
        logger.error("Таймаут запроса к HF API")
        return "Превышено время ожидания ответа. Попробуйте позже."
    except requests.exceptions.ProxyError as e:
        logger.error(f"Ошибка прокси: {e}")
        return "Ошибка подключения через прокси. Проверьте SSH-туннель."
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return "Произошла непредвиденная ошибка."

# ====== ОБРАБОТЧИКИ КОМАНД ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Очищает историю и приветствует пользователя.
    """

    {TODO: напишите промт, который сгенирирует код обработки команды /start.}


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /clear.
    Очищает историю диалога пользователя.
    """

    {TODO: напишите промт, который сгенирирует код обработки команды /clear}


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /history.
    Показывает количество сохраненных сообщений в истории.
    """

    {TODO: напишите промт, который сгенирирует код обработки команды /history и покажет количество сохраненных сообщений в истории.}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик обычных текстовых сообщений.
    Отправляет запрос к Hugging Face API и возвращает ответ.
    """
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Показываем, что бот печатает
    await update.message.chat.send_action(action="typing")
    
    # Отправляем временное сообщение о процессе обработки
    processing_msg = await update.message.reply_text("🤔 *Анализирую вопрос...*", parse_mode="Markdown")
    
    try:
        answer = query_hf(chat_id, user_text)
        await processing_msg.delete()
        
        # Разбиваем длинные сообщения на части (ограничение Telegram 4096 символов)
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text(answer)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_message: {e}")
        await processing_msg.edit_text("❌ *Произошла ошибка. Попробуйте позже.*", parse_mode="Markdown")

# ====== ДИАГНОСТИКА ======

def test_huggingface_connection() -> bool:
    """
    Тестирует подключение к Hugging Face API через прокси.
    
    Returns:
        bool: True если подключение успешно, False в противном случае
    """
    print("\n🔍 Тестируем подключение к Hugging Face Chat API...")
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    
    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Простой тестовый запрос
    test_payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 5,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            CHAT_API_URL,
            headers=headers,
            json=test_payload,
            proxies=proxies,
            timeout=30
        )
        
        print(f"📡 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Hugging Face Chat API доступен!")
            print(f"📡 Модель {MODEL_NAME} работает!")
            return True
        else:
            print(f"⚠️ Hugging Face вернул ошибку: {response.status_code}")
            print(f"📄 Текст ошибки: {response.text[:300]}")
            
            # Анализ ошибки
            if "model_not_supported" in response.text:
                print("\n💡 Модель не поддерживается. Попробуйте другой формат:")
                print("   - meta-llama/Llama-3.3-70B-Instruct:fireworks-ai")
                print("   - microsoft/phi-3-mini-4k-instruct:fireworks-ai")
                print("   - Qwen/Qwen2.5-7B-Instruct-1M:fireworks-ai")
            elif "authorization" in response.text.lower():
                print("\n💡 Проблема с API ключом. Проверьте HUGGING_FACE_API_KEY")
            elif "timeout" in response.text.lower():
                print("\n💡 Таймаут. Проверьте скорость прокси-соединения")
            
            return False
            
    except requests.exceptions.ProxyError as e:
        print(f"❌ Ошибка прокси: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Проверьте, запущен ли SSH-туннель:")
        print("   ssh -D 8080 -N -f user@server.com")
        print("2. Проверьте, что порт 8080 открыт:")
        print("   netstat -an | findstr 8080 (Windows)")
        print("   lsof -i :8080 (Mac/Linux)")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\n🔧 Проверьте:")
        print("1. Интернет-соединение")
        print("2. Правильность PROXY_URL")
        print("3. Доступность сервера")
        return False
        
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        return False


def test_proxy_connection() -> bool:
    """
    Тестирует подключение через прокси к Telegram API.
    
    Returns:
        bool: True если подключение успешно
    """
    print("\n🔍 Тестируем подключение через прокси к Telegram API...")
    
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
        response = requests.get(url, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Telegram API доступен!")
            print(f"   Бот: @{data['result']['username']}")
            return True
        else:
            print(f"⚠️ Ошибка Telegram API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

# ====== ФУНКЦИЯ MAIN ======

def main():
    {TODO: напишите промт, который сгенирирует код для вывода информации о программе: прокси, модель, максимальную длину диалога.}

    {TODO: напишите промт, который сгенирирует код для проверки подключения к Telegram через прокси, используя написанные ранее функции}

    # Проверяем подключение к Hugging Face
    if not test_huggingface_connection():
        print("\n⚠️ Внимание! Hugging Face API не отвечает.")
        print("\nВозможные решения:")
        print("1. Проверьте SSH-туннель")
        print("2. Создайте новый токен на huggingface.co/settings/tokens")
        print("3. Попробуйте другую модель")
        
        response = input("\nПродолжить запуск бота? (y/n): ")
        if response.lower() != 'y':
            print("❌ Запуск отменен")
            return
    
    # Создаем приложение с прокси
    app = (ApplicationBuilder()
           .token(TELEGRAM_TOKEN)
           .proxy(PROXY_URL)
           .get_updates_proxy(PROXY_URL)
           .build())

    {TODO: напишите промт, который сгенирирует код для добавление команд в приложение и выведет информацию, что бот запущен и сами команды (их название и описание)}
    
    # Запускаем polling
    app.run_polling()


if __name__ == "__main__":
    main()
```

```bash
# .env.example - Пример файла с переменными окружения
# Скопируйте этот файл как .env и заполните своими значениями

# Telegram Bot Token (получите у @BotFather)
TELEGRAM_TOKEN=your_telegram_token_here

# Hugging Face API Key (получите на https://huggingface.co/settings/tokens)
HUGGING_FACE_API_KEY=hf_your_api_key_here

# Proxy URL для SSH-туннеля (опционально)
PROXY_URL=socks5://127.0.0.1:8080
```
