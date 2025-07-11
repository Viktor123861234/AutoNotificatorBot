import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
from datetime import datetime

# Sheets / Excel
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import openpyxl

# === Инициализация ===
load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
USE_GOOGLE_SHEETS = os.getenv("USE_GOOGLE_SHEETS") == "True"

# Логгинг
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Функции логирования ===
def log_to_gsheet(text: str, user: str):
    client = gspread.service_account("credentials.json")

    sheet = client.open_by_key(os.getenv("GSHEET_KEY")).worksheet(os.getenv("GSHEET_WORKSHEET"))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, user, text])

def log_to_excel(text: str, user: str):
    file = os.getenv("EXCEL_FILE")
    if not os.path.exists(file):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Timestamp", "User", "Message"])
        wb.save(file)

    wb = openpyxl.load_workbook(file)
    ws = wb.active
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append([timestamp, user, text])
    wb.save(file)

# === Основной хэндлер ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.full_name
    message = update.message.text
    logger.info(f"Message from {user}: {message}")

    # Ответ пользователю
    await update.message.reply_text("✅Thank you, I wrote it down!")

    # Уведомление админу
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📩 New message from {user}:\n{message}")

    # Логирование
    try:
        if USE_GOOGLE_SHEETS:
            log_to_gsheet(message, user)
        else:
            log_to_excel(message, user)
    except Exception as e:
        logger.error(f"Logging error: {e}")
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚠️ Logging error:\n{e}")

# === Запуск бота ===
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("The bot has been launched.")
    app.run_polling()
