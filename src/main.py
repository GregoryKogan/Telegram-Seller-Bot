import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)
from payment.endpoints import select_amount, pay, check_payment
from api_keys import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Это бот для демонстрации оплаты по QIWI",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Заплатить", callback_data="select_amount")]]
        ),
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Не понимаю вас..."
    )


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Извините, я не знаю такой команды",
    )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "select_amount":
        await select_amount(update=update, context=context)
    elif query.data.startswith("pay"):
        await pay(update=update, context=context, query_data=query.data)
    elif query.data.startswith("check_payment"):
        await check_payment(update=update, context=context, query_data=query.data)


if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    start_handler = CommandHandler("start", start)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    callback_query_handler = CallbackQueryHandler(handle_callback_query)

    application.add_handler(start_handler)
    application.add_handler(unknown_handler)
    application.add_handler(echo_handler)
    application.add_handler(callback_query_handler)

    application.run_polling()