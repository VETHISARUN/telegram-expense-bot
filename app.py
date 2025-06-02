import os
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

import gspread

# Load .env variables
load_dotenv()
TOKEN = os.environ.get('TOKEN')
USERNAME = os.environ.get('USER_NAME')
USER_ID = os.environ.get('USER_ID')

# Google Sheets setup
gc = gspread.service_account(filename='credentials.json')
sh = gc.open("myexpenses")
current_month = datetime.now().strftime('%B')

# Create worksheet for current month if not exists
if current_month not in [ws.title for ws in sh.worksheets()]:
    sh.add_worksheet(title=current_month, rows="300", cols="10")

worksheet = sh.worksheet(current_month)

# Add headers if empty
if not worksheet.acell('A1').value:
    worksheet.append_row(['Date', 'Description', 'Amount'])

# Message Handler
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message.text.strip()

    if user.username != USERNAME and str(user.id) != USER_ID:
        now = datetime.now()
        with open('logs.csv', 'a') as f:
            f.write(f"{now.strftime('%d/%m/%Y')},{now.strftime('%H:%M:%S')},{user.id},{user.username},{user.first_name},{user.last_name}\n")
        return

    if message == '/start':
        await update.message.reply_text(f"Hi {user.first_name}, your bot is running!")

    elif message == 'ping':
        await update.message.reply_text("pong")

    elif message == 'today':
        today = datetime.now().strftime('%d/%m/%Y')
        records = worksheet.get_all_records()
        today_records = [r for r in records if r['Date'] == today]
        total = sum(float(r['Amount']) for r in today_records)
        await update.message.reply_text(f"Today's expenses: ₹{total}")

    elif message == 'month':
        records = worksheet.get_all_records()
        total = sum(float(r['Amount']) for r in records)
        await update.message.reply_text(f"This month's expenses: ₹{total}")

    elif ',' in message:
        parts = [x.strip() for x in message.split(',')]
        if len(parts) == 2:
            date = datetime.now().strftime('%d/%m/%Y')
            description, amount = parts
        elif len(parts) == 3:
            date, description, amount = parts
        else:
            await update.message.reply_text("Invalid format. Use: Description, Amount or Date, Description, Amount")
            return

        try:
            worksheet.append_row([date, description, amount])
            await update.message.reply_text(f"✅ Expense added:\nDate: {date}\nDescription: {description}\nAmount: ₹{amount}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    else:
        await update.message.reply_text("Send a command like 'ping', 'today', or an expense like 'Tea, 20'")

# MAIN
if __name__ == "__main__":
    print("🚀 Bot is starting...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.add_handler(MessageHandler(filters.COMMAND, message_handler))
    app.run_polling()