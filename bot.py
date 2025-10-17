from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, ContextTypes
from flask import Flask, request
import os

# Telegram bot token (from Railway environment variable)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Create Flask app
app = Flask(__name__)

# Telegram handlers setup
CHOOSING, VERIFY_NAME, VERIFY_PASSPORT, APPOINTMENT_NAME, APPOINTMENT_DATE = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["Verify Documents", "Book Appointment"]]
    await update.message.reply_text(
        "👋 Welcome to *International Migration Service!* 🇨🇦🇦🇺\n\n"
        "Please choose a service below:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CHOOSING

async def choose_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Verify Documents":
        await update.message.reply_text("Please enter your full name:")
        return VERIFY_NAME
    elif text == "Book Appointment":
        await update.message.reply_text("Please enter your full name for the appointment:")
        return APPOINTMENT_NAME
    else:
        await update.message.reply_text("Please select a valid option.")
        return CHOOSING

async def verify_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Now please enter your travel document number:")
    return VERIFY_PASSPORT

async def verify_passport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    passport = update.message.text
    name = context.user_data.get("name")
    await update.message.reply_text(
        f"✅ Thank you, {name}!\nYour verification request has been received.\n"
        "We will review your documents and contact you shortly."
    )
    return ConversationHandler.END

async def appointment_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Please enter your preferred appointment date (e.g., 2025-10-20):")
    return APPOINTMENT_DATE

async def appointment_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date = update.message.text
    name = context.user_data.get("name")
    await update.message.reply_text(
        f"📅 Thank you, {name}!\nYour appointment request for {date} has been submitted.\n"
        "We’ll contact you soon with confirmation."
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation canceled. Type /start to begin again.")
    return ConversationHandler.END

# Telegram bot app setup
application = Application.builder().token(BOT_TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSING: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_service)],
        VERIFY_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_name)],
        VERIFY_PASSPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, verify_passport)],
        APPOINTMENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_name)],
        APPOINTMENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, appointment_date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(conv_handler)

# Flask route for Telegram webhook
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
