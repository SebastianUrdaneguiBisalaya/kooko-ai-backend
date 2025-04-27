# Creating a Chatbot using Telegram
# To receive the image from user through a simple message

# Telegram libraries
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update
# Config libraries
import logging
import os
from pathlib import Path
import tempfile
from dotenv import load_dotenv
# Importing functions
from functions.invoice import invoice_processing

# Name of the bot: Dolfin.ai
# Link of Telegram Bot: https://t.me/DolfinAIBot

# Config environment variables
dotenv_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

TELEGRAM_API_KEY = os.getenv("TELEGRAM_BOTFATHER_API_KEY")

# Config to improve the method to find errors
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

WAITING_FOR_IMAGE = 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    user_first_name = user.first_name
    user_last_name = user.last_name
    print(user_id, user_first_name, user_last_name)
    inline_keyboard = [
        [
            InlineKeyboardButton("¿Qué es Dolfin.ai? 🤔",
                                 callback_data="definition"),
            InlineKeyboardButton("¿Cómo funciona? 🤔",
                                 callback_data="how-it-works"),
            InlineKeyboardButton("Subir boleta y/o factura 📋",
                                 callback_data="upload-invoice"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard
    )
    await update.message.reply_html(
        rf"¡Hola {user_first_name}!",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id,
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "definition":
        await query.message.reply_text("Dolfin.ai 🚀 es un chatbot que te ayuda a digitalizar tus boletas y/o facturas.")
    elif query.data == "how-it-works":
        await query.message.reply_html("👉🏻 Debes selecionar la opción de <b>Subir boleta o factura</b>, enviar la imagen y listo.")
    elif query.data == "upload-invoice":
        await query.message.reply_text("👨🏻‍💻 Por favor, envíame la imagen de tu boleta y/o factura. Procura que sea nítido.")
        context.user_data["waiting_for"] = 1


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo = update.message.photo[-1]  # Get the better photo
    file_id = photo.file_id
    file = await context.bot.get_file(file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        local_file_path = temp_file.name
    try:
        await file.download_to_drive(local_file_path)
        await update.message.reply_text("👨🏻‍💻 Gracias por enviarme la imagen. Estoy procesando la imagen.")
        proccesing_result = invoice_processing(path_file=local_file_path)
        await update.message.reply_text(f"La imagen se ha procesado correctamente. 🙌🏻 ${proccesing_result["data"]["id_invoice"]}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ha ocurrido un error al procesar la imagen. 😔")
        print(f"Error al procesar la imagen: {e}")
    finally:
        try:
            os.remove(local_file_path)
        except OSError as e:
            print(f"Error al eliminar el archivo: {e}")
    if "waiting_for" in context.user_data:
        del context.user_data['waiting_for']


def main() -> None:
    application = Application.builder().token(TELEGRAM_API_KEY).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, start))
    application.add_handler(MessageHandler(filters.PHOTO, receive_image))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
