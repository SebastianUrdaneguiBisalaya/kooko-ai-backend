# Creating a Chatbot using Telegram
# To receive the image from user through a simple message

# Telegram libraries
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.constants import ParseMode
# Config libraries
import logging
import os
from pathlib import Path
import tempfile
import re
import httpx
from dotenv import load_dotenv
# Importing functions
from functions.invoice import invoice_processing, format_money, sum_all_taxes
from functions.supabase import verify_user, insert_invoice_data, insert_invoice_detail_data, insert_user_credits_data, upload_file

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


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    inline_keyboard = [
        [InlineKeyboardButton("¿Qué es kooko.ai? 🤔",
                              callback_data="definition")],
        [InlineKeyboardButton("¿Cómo funciona? 🤔",
                              callback_data="how-it-works")],
        [InlineKeyboardButton("¡Quiero registrarme! 🚀",
                              callback_data="want-to-register")],
        [InlineKeyboardButton("Subir boleta y/o factura 📋",
                              callback_data="upload-invoice")],
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await update.message.reply_html(
        f"¡Hola {user.first_name}!\nPor favor, elige una opción:",
        reply_markup=reply_markup,
        reply_to_message_id=update.message.message_id,
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text.strip().lower()
    if context.user_data.get("waiting_for_phone"):
        phone_match = re.fullmatch(r'\+?\d{9,15}', user_input)
        if "user_phone" in context.user_data:
            await update.message.reply_text("⚠️ Ya he registrado tu número. Por favor, envíame tu imagen de boleta o factura.")
            return
        if phone_match:
            context.user_data["user_phone"] = user_input
            del context.user_data["waiting_for_phone"]
            await update.message.reply_text("✅ ¡Gracias! Tu número ha sido registrado correctamente. Ahora puedes subir una imagen.")
        else:
            await update.message.reply_text("⚠️ El número ingresado no es válido. Debes enviar con el prefijo de tu país, por ejemplo, +51 para Perú.")
        return
    if user_input in ["hola"]:
        await show_main_menu(update, context)
        return


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "definition":
        await query.message.reply_text("kooko.ai 🚀 es un chatbot que te ayuda a digitalizar tus boletas y/o facturas.")
    elif query.data == "how-it-works":
        await query.message.reply_html("👉🏻 Debes selecionar la opción de <b>Subir boleta o factura</b>, enviar la imagen y listo.")
    elif query.data == "upload-invoice":
        await query.message.reply_text("👨🏻‍💻 Por favor, envíame la imagen de tu boleta y/o factura. Procura que sea nítido.")
        context.user_data["waiting_for"] = 1
    elif query.data == "confirm-invoice":
        keyboard = [
            [InlineKeyboardButton(
                "¿Deseas subir otra factura y/o boleta?", callback_data="send-another-invoice")],
            [InlineKeyboardButton(
                "Por el momento, no. Gracias. ✅", callback_data="finish-process")]
        ]
        reply_markup = InlineKeyboardMarkup(
            keyboard
        )
        await query.message.reply_text("✅ ¡Registro confirmado! Puedes visualizarlo en tu panel de control.", reply_markup=reply_markup)
    elif query.data == "send-another-invoice":
        await query.message.reply_text("👨🏻‍💻 Por favor, envíame la imagen de tu boleta y/o factura. Procura que sea nítido.")
        context.user_data["waiting_for"] = 1
    elif query.data == "forgot-products":
        await query.message.reply_text("🛒 Entendido. Por favor, envíame los productos faltantes o una nueva imagen.")
    elif query.data == "finish-process":
        await query.message.reply_text("!Gracias por usar el servicio!. Si necesitas digitalizar más boletas o facturas en el futuro, puedes volver a iniciar mi sistema con un saludo. 🙌🏻")
        if "waiting_for" in context.user_data:
            context.user_data.clear()
    elif query.data == "want-to-register":
        context.user_data["waiting_for_phone"] = True
        await query.message.reply_text("👨🏻‍💻 Solo requiero que me envíes el número de celular que estás utilizando en este chat con el prefijo de tu país. Por ejemplo, +51987535574 para Perú.")


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # First, we will verify if the user is already registered by full name
    if "user_phone" not in context.user_data:
        await update.message.reply_text("⚠️ Hey, no tengo cómo validar tu identidad.\nPor favor, envíame tu número de celular antes de subir una imagen.")
        return
    user_phone = context.user_data["user_phone"]

    try:
        user_id = verify_user(user_phone=user_phone)
    except httpx.ConnectTimeout:
        await update.message.reply_text("⚠️ Error de conexión con el servidor. Intenta nuevamente en unos minutos.")
        return
    except httpx.RequestError as e:
        await update.message.reply_text("⚠️ No se pudo conectar con el servidor. Verifica tu conexión a internet.")
        return

    if not user_id:
        await update.message.reply_text("⚠️ El número enviado no está registrado en nuestro sistema. Por favor, envíame un número válido.")
        del context.user_data['user_phone']
        return

    photo = update.message.photo[-1]  # Get the better photo
    file_id = photo.file_id
    file = await context.bot.get_file(file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        local_file_path = temp_file.name
    try:
        await file.download_to_drive(local_file_path)
        await update.message.reply_text("👨🏻‍💻 Gracias por enviarme la imagen. Estoy procesando...")
        processing_result = invoice_processing(path_file=local_file_path)
        processing_data = processing_result["data"]
        products_info = ""
        total_amount = 0
        all_taxes = sum_all_taxes(processing_data["taxes"])
        for product in processing_data["products"]:
            name = product["product_name"] or ""
            price = float(product["unit_price"]
                          ) if product["unit_price"] is not None else 0
            quantity = float(product["quantity"]
                             ) if product["quantity"] is not None else 0
            subtotal = price * quantity
            total_amount += subtotal
            products_info += f"\n - {name}: {format_money(price)} x {quantity}u"

        res_upload_file = upload_file(f"{local_file_path}", user_id=user_id)

        insert_invoice_data(user_id=user_id,
                            total=total_amount,
                            invoice_data=processing_data,
                            path_file=res_upload_file)

        insert_invoice_detail_data(invoice_detail_data=processing_data)

        insert_user_credits_data(user_id=user_id,
                                 credits=processing_result)
        message_text = (
            f"Por favor, confirma los siguiente datos para culminar el proceso.\n\n"
            f"<b>N° Factura:</b> {processing_data["id_invoice"]}\n"
            f"<b>Cliente:</b> {processing_data["client"]["name_client"]} - {processing_data["client"]["id_client"]}\n\n"
            f"<b>Vendedor:</b> {processing_data["seller"]["name_seller"]} - {processing_data["seller"]["id_seller"]}\n\n"
            f"<b>Fecha de la compra:</b> {processing_data["date"]}\n\n"
            f"<b>Productos:</b> {products_info}\n\n"
            f"<b>Total de impuestos:</b> {format_money(all_taxes)}\n\n"
            f"<b>Total:</b> {format_money(total_amount + all_taxes)}"
        )
        keyboards = [
            [
                InlineKeyboardButton(
                    "✅ Aceptar", callback_data="confirm-invoice"),
            ],
            [
                InlineKeyboardButton(
                    "🛒 Olvidaste algunos productos", callback_data="forgot-products"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(
            keyboards,
        )
        await update.message.reply_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
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
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.PHOTO, receive_image))
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
