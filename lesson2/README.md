# Лабораторная работа: Создание Telegram-бота с интеграцией Hugging Face API

## 📚 О чем эта лабораторная работа

В данной лабораторной работе вы научитесь создавать интеллектуального Telegram-бота, который использует большие языковые модели (LLM) от Hugging Face для ведения диалога в стиле Сократа. Бот помогает пользователям самостоятельно находить решения задач, задавая наводящие вопросы, а не выдавая готовые ответы.

Вы также освоите:
- Работу с Telegram Bot API
- Интеграцию с Hugging Face Inference API
- Настройку прокси через SSH-туннель для обхода сетевых ограничений
- Сохранение контекста диалога для поддержания беседы
- Обработку ошибок и диагностику подключений

## 🎯 Цель работы

1. Создать Telegram-бота с использованием библиотеки `python-telegram-bot`
2. Интегрировать Hugging Face API для работы с LLM (модель Llama 3.3 70B)
3. Реализовать систему сохранения контекста диалога (память бота)
4. Настроить прокси-соединение через SSH-туннель
5. Разработать систему prompt'ов для реализации метода Сократа

## 📋 Требования к окружению

### Необходимое программное обеспечение
- Python 3.10 или выше
- Git
- SSH-клиент (для создания туннеля)
- Аккаунт на [Hugging Face](https://huggingface.co)
- Аккаунт в Telegram

### Необходимые библиотеки
```bash
pip install python-telegram-bot requests huggingface_hub pysocks


---

# Теоретическое введение к лабораторной работе

## 1. Метод Сократа в педагогике и искусственном интеллекте

### 1.1 Исторический контекст

Метод Сократа (Socratic method) — древнегреческий метод ведения диалога, названный в честь философа Сократа (469-399 гг. до н.э.). Основная идея заключается в том, что истина постигается через постановку наводящих вопросов, а не прямое изложение фактов.

**Ключевые принципы метода:**
- **Майевтика** (рождение мысли) — помощь собеседнику в "рождении" правильного знания
- **Эленхос** (опровержение) — выявление противоречий в рассуждениях собеседника
- **Индукция** — движение от частных примеров к общим выводам

### 1.2 Применение в LLM

В контексте больших языковых моделей метод Сократа реализуется через специально сконструированный системный промпт:

```python
SYSTEM_PROMPT = """
Ты — учебный помощник по методу Сократа.
Правила:
- Никогда не решай задачу полностью
- Задавай наводящие вопросы
- Разбивай проблему на шаги
- Помогай студенту думать самостоятельно
"""

---

# Шаг 1: Регистрация и получение ключей API

## 1.1 Регистрация в Telegram и создание бота

### Что такое Telegram Bot API?
Telegram Bot API — это интерфейс, позволяющий программам взаимодействовать с платформой Telegram. Боты могут отправлять сообщения, обрабатывать команды, отвечать на сообщения пользователей и выполнять множество других действий.

### Пошаговая инструкция:

#### Шаг 1.1.1: Найдите BotFather
1. Откройте приложение Telegram на любом устройстве (ПК, телефон, веб-версия)
2. В строке поиска введите `@BotFather` (без пробелов)
3. Нажмите на официального бота с синей галочкой верификации ✓

![Поиск BotFather](https://i.imgur.com/placeholder.png)
*Рисунок 1: Поиск BotFather в Telegram*

#### Шаг 1.1.2: Создайте нового бота
1. Отправьте BotFather команду `/newbot`
2. Дождитесь ответа с запросом имени бота

#### Шаг 1.1.3: Получите API токен
После успешного создания бота BotFather выдаст вам **токен** — уникальный ключ доступа

**Важно!** Токен — это ключ от вашего бота. Никогда не публикуйте его в открытом доступе!

#### Шаг 1.1.4: Сохраните токен
Создайте файл `.env` или запишите токен в надежное место:

```bash
# Файл .env (не публикуйте в Git!)
TELEGRAM_TOKEN=8575520649:AAGhxbwFzNLm4PmK8nhkbqsbK8HxiotYAR8

---

# Шаг 2: Настройка SSH-туннеля

## 2.1 Что такое SSH-туннель и зачем он нужен

### 2.1.1 Определение

**SSH-туннель** (SSH tunnel, SSH-прокси) — это зашифрованное соединение, создаваемое поверх протокола SSH (Secure Shell), которое позволяет перенаправлять сетевой трафик через удаленный сервер. В контексте данной лабораторной работы мы используем SSH-туннель как **SOCKS5 прокси** для обхода сетевых ограничений.

### 2.1.2 Зачем нужен SSH-туннель для лабораторной работы?

| Проблема | Решение через SSH-туннель |
|----------|--------------------------|
| Доступ к Hugging Face API может быть ограничен в некоторых регионах | Трафик идет через удаленный сервер, где ограничений нет |
| Telegram API может быть заблокирован | Бот подключается через зашифрованный туннель |
| Желание скрыть IP-адрес вашего компьютера | API видят IP удаленного сервера, а не ваш реальный |
| Необходимость шифрования трафика для безопасности | SSH обеспечивает полное шифрование всех данных |

### 2.1.3 Как работает SSH-туннель

---

# Шаг 3: Создание базовой структуры бота

## 3.1 Создание главного файла бота

Создайте файл `bot.py` в корневой директории проекта:

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

---
## 3.2 Создание Системного промта

```python
# ====== СИСТЕМНЫЙ ПРОМПТ ======
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

---

## 3.3 Работа с памятью

```python
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

---

## 3.4 Интеграция с Hugging Face

```python
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

---
# Шаг 4. Реализация обработчиков команд
---
## Шаг 4.1 Команда /start

```python
# ====== ОБРАБОТЧИКИ КОМАНД ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /start.
    Очищает историю и приветствует пользователя.
    """
    chat_id = update.effective_chat.id
    clear_history(chat_id)
    
    await update.message.reply_text(
        "🤖 *Привет! Я учебный помощник по методу Сократа.*\n\n"
        "✅ Я НЕ даю готовых ответов\n"
        "✅ Я задаю наводящие вопросы\n"
        "✅ Я помогаю тебе думать самостоятельно\n"
        "✅ Я помню нашу беседу\n\n"
        "📌 *Команды:*\n"
        "/start - начать заново (очистить память)\n"
        "/clear - очистить историю диалога\n"
        "/history - показать сколько сообщений я помню\n\n"
        "Просто напиши свою задачу или вопрос! 📚",
        parse_mode="Markdown"
    )

---
## 4.2 Команда /clear

```python
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /clear.
    Очищает историю диалога пользователя.
    """
    chat_id = update.effective_chat.id
    
    if clear_history(chat_id):
        await update.message.reply_text("🧹 *История диалога очищена!* Начинаем с чистого листа.", parse_mode="Markdown")
    else:
        await update.message.reply_text("📭 *История и так пуста.*", parse_mode="Markdown")

---

## 4.3 Команда /history

```python
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик команды /history.
    Показывает количество сохраненных сообщений в истории.
    """
    chat_id = update.effective_chat.id
    history = get_user_history(chat_id)
    history_count = len(history) // 2  # Делим на 2, так как храним пары user+assistant
    
    await update.message.reply_text(
        f"📊 *Статистика памяти:*\n\n"
        f"• Я помню *{history_count}* предыдущих обменов сообщениями\n"
        f"• Максимум храню *{MAX_HISTORY_LENGTH}* диалогов\n"
        f"• Всего сообщений в памяти: *{len(history)}*",
        parse_mode="Markdown"
    )

---

## 4.4 Обработчки текстовых сообщений

```python
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
    processing_msg = await update.message.reply_text("🤔 *Анализирую вопрос с учетом контекста...*", parse_mode="Markdown")
    
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

---
# Шаг 5. Диагностика работоспособности бота

```python
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

---

# Шаг 6. Функция main

```python
def main():
    """
    Главная функция запуска бота.
    """
    print("=" * 60)
    print("🤖 ЗАПУСК TELEGRAM БОТА (С ПАМЯТЬЮ)")
    print("=" * 60)
    
    print(f"\n🔒 Прокси: {PROXY_URL}")
    print(f"📡 Модель: {MODEL_NAME}")
    print(f"💾 Память: {MAX_HISTORY_LENGTH} последних диалогов")
    
    # Проверяем подключение к Telegram через прокси
    if not test_proxy_connection():
        print("\n⚠️ Внимание! Telegram API не отвечает через прокси.")
        response = input("\nПродолжить запуск бота? (y/n): ")
        if response.lower() != 'y':
            print("❌ Запуск отменен")
            return
    
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
    
    # Регистрируем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("\n" + "=" * 60)
    print("✅ Бот успешно запущен!")
    print("📌 Доступные команды:")
    print("   /start   - начать заново (очистить память)")
    print("   /clear   - очистить историю диалога")
    print("   /history - показать статистику памяти")
    print("=" * 60 + "\n")
    
    # Запускаем polling
    app.run_polling()


if __name__ == "__main__":
    main()


# Шаг 6. Запуск бота

---

## 6.1 Подключись к прокси серверу
```bash
ssh -D 8080 -N -f username@your-server.com

---

## 6.2 Запустите вашего бота

```bash
python3 bot.py
