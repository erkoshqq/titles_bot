# 🤖 WatchBot — настройка

## Что нужно получить перед запуском

### 1. Telegram Bot Token
1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. `/newbot` → придумай имя → получи токен
3. Вставь в `.env` как `BOT_TOKEN`

### 2. Твой Telegram ID
1. Напиши [@userinfobot](https://t.me/userinfobot)
2. Он пришлёт твой ID
3. Вставь в `.env` как `MY_TELEGRAM_ID`

### 3. YouTube API Key
1. Зайди на [console.cloud.google.com](https://console.cloud.google.com)
2. Создай проект → APIs & Services → Enable APIs
3. Найди **YouTube Data API v3** → включи
4. Credentials → Create Credentials → API Key
5. Вставь в `.env` как `YOUTUBE_API_KEY`

### 4. Google Sheets + Service Account
1. На том же [console.cloud.google.com](https://console.cloud.google.com)
2. APIs & Services → Enable APIs → **Google Sheets API** + **Google Drive API** — включи оба
3. Credentials → Create Credentials → **Service Account**
4. Дай любое имя → Create
5. Зайди в созданный аккаунт → Keys → Add Key → JSON → скачай файл
6. Переименуй файл в `credentials.json` и положи рядом с `bot.py`
7. Создай новую Google таблицу на своём аккаунте
8. Скопируй ID таблицы из URL: `docs.google.com/spreadsheets/d/ВОТ_ЭТОТ_ID/edit`
9. Вставь в `.env` как `GOOGLE_SHEET_ID`
10. Открой `credentials.json`, найди поле `client_email` — скопируй этот email
11. В Google таблице: Поделиться → вставь этот email → роль **Редактор**

---

## Установка и запуск

```bash
# Установить зависимости
pip install -r requirements.txt

# Скопировать и заполнить .env
cp .env.example .env
# отредактируй .env

# Запустить
python bot.py
```

---

## Структура файлов

```
watchbot/
├── bot.py            # основной бот
├── sheets.py         # работа с Google Sheets
├── youtube.py        # получение инфо с YouTube
├── credentials.json  # ключ сервис-аккаунта (не публиковать!)
├── .env              # токены (не публиковать!)
├── .env.example      # шаблон
└── requirements.txt
```

---

## Как пользоваться

- `/start` — главное меню
- **Добавить** → выбери категорию → отправь ссылку (YouTube) или название
- **Список** → выбери категорию → листай по 5 штук → тапни на тайтл → удали или вернись
