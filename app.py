import logging
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler

from handlers import conv_handler, stats_handler, chart_handler, cancel_command

load_dotenv()
TOKEN = os.environ["TOKEN"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # ConversationHandler for adding expenses
    app.add_handler(conv_handler)

    # Other commands
    app.add_handler(CommandHandler("today", stats_handler))
    app.add_handler(CommandHandler("month", stats_handler))
    app.add_handler(CommandHandler("summary", stats_handler))
    app.add_handler(CommandHandler("chart", chart_handler))
    app.add_handler(CommandHandler("cancel", cancel_command))

    print("🚀 SpendBot starting...")
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
