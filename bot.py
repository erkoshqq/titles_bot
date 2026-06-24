import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from dotenv import load_dotenv
import sheets
import youtube

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_TELEGRAM_ID = int(os.getenv("MY_TELEGRAM_ID"))

CATEGORIES = {
    "youtube": "📺 YouTube",
    "anime":   "🎌 Аниме",
    "movies":  "🎬 Фильмы",
    "series":  "📺 Сериалы",
    "games":   "🎮 Игры",
}

WAITING_FOR_CONTENT = 1

# --- Auth check ---
def is_me(update: Update) -> bool:
    return update.effective_user.id == MY_TELEGRAM_ID

# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_me(update):
        return
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить", callback_data="action:add"),
         InlineKeyboardButton("📋 Список", callback_data="action:list")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = "Привет! Что делаем?"
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.effective_message.reply_text(text, reply_markup=markup)

# --- Category picker keyboard ---
def category_keyboard(prefix: str):
    buttons = []
    row = []
    for key, label in CATEGORIES.items():
        row.append(InlineKeyboardButton(label, callback_data=f"{prefix}:{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="action:back")])
    return InlineKeyboardMarkup(buttons)

# --- Callback handler ---
async def handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_me(update):
        return
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "action:add":
        await q.edit_message_text("Выбери категорию:", reply_markup=category_keyboard("add"))

    elif data == "action:list":
        await q.edit_message_text("Выбери категорию:", reply_markup=category_keyboard("list"))

    elif data == "action:back":
        await show_main_menu(update, context, edit=True)

    elif data.startswith("add:"):
        category = data.split(":")[1]
        context.user_data["add_category"] = category
        label = CATEGORIES[category]
        if category == "youtube":
            await q.edit_message_text(f"{label}\n\nОтправь ссылку на YouTube видео:")
        else:
            await q.edit_message_text(f"{label}\n\nНапиши название:")
        context.user_data["state"] = WAITING_FOR_CONTENT

    elif data.startswith("list:"):
        category = data.split(":")[1]
        await show_list(update, context, category, page=0, edit=True)

    elif data.startswith("page:"):
        _, category, page = data.split(":")
        await show_list(update, context, category, page=int(page), edit=True)

    elif data.startswith("item:"):
        _, category, row_index = data.split(":")
        await show_item(update, context, category, int(row_index), edit=True)

    elif data.startswith("delete:"):
        _, category, row_index = data.split(":")
        sheets.delete_item(category, int(row_index))
        await q.edit_message_text("✅ Удалено!")
        await show_list(update, context, category, page=0)

    elif data.startswith("keep:"):
        _, category, row_index = data.split(":")
        await show_list(update, context, category, page=0, edit=True)

# --- Handle text messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_me(update):
        return
    state = context.user_data.get("state")
    if state != WAITING_FOR_CONTENT:
        await show_main_menu(update, context)
        return

    text = update.message.text.strip()
    category = context.user_data.get("add_category")
    context.user_data["state"] = None

    if category == "youtube":
        await update.message.reply_text("⏳ Получаю инфо с YouTube...")
        info = youtube.get_video_info(text)
        if not info:
            await update.message.reply_text("❌ Не удалось получить инфо. Проверь ссылку.")
            await show_main_menu(update, context)
            return
        sheets.add_item(category, {
            "title": info["title"],
            "author": info["author"],
            "url": text,
        })
        await update.message.reply_text(
            f"✅ Сохранено!\n\n*{info['title']}*\n{info['author']}",
            parse_mode="Markdown"
        )
    else:
        sheets.add_item(category, {"title": text})
        await update.message.reply_text(f"✅ *{text}* сохранено!", parse_mode="Markdown")

    await show_main_menu(update, context)

# --- Show list ---
async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, page: int, edit=False):
    PAGE_SIZE = 5
    items = sheets.get_items(category)

    if not items:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="action:list")]]
        text = f"{CATEGORIES[category]}\n\nСписок пуст."
        if edit and update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    total = len(items)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_items = items[start:end]

    buttons = []
    for i, item in enumerate(page_items):
        real_index = start + i
        title = item.get("title", "—")
        author = item.get("author", "")
        label_btn = f"{title}" + (f" — {author}" if author else "")
        buttons.append([InlineKeyboardButton(label_btn, callback_data=f"item:{category}:{real_index}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data=f"page:{category}:{page - 1}"))
    if end < total:
        nav.append(InlineKeyboardButton("▶️", callback_data=f"page:{category}:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="action:list")])

    text = f"{CATEGORIES[category]} — {total} шт. (стр. {page + 1}/{(total - 1) // PAGE_SIZE + 1})"
    markup = InlineKeyboardMarkup(buttons)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.effective_message.reply_text(text, reply_markup=markup)

# --- Show single item ---
async def show_item(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str, row_index: int, edit=False):
    items = sheets.get_items(category)
    item = items[row_index]

    title = item.get("title", "—")
    author = item.get("author", "")
    url = item.get("url", "")

    lines = [f"*{title}*"]
    if author:
        lines.append(f"👤 {author}")
    if url:
        lines.append(f"🔗 [Ссылка]({url})")

    text = "\n".join(lines)
    keyboard = [
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{category}:{row_index}"),
            InlineKeyboardButton("🔙 Назад", callback_data=f"keep:{category}:{row_index}"),
        ]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update.effective_message.reply_text(text, reply_markup=markup, parse_mode="Markdown")

# --- Keep-alive сервер для UptimeRobot ---
class KeepAliveHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # отключаем логи пингов

def run_keep_alive():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), KeepAliveHandler)
    server.serve_forever()

# --- Main ---
def main():
    thread = threading.Thread(target=run_keep_alive, daemon=True)
    thread.start()
    logger.info("Keep-alive сервер запущен")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_action))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
