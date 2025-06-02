# Telegram Expense Tracker Bot

A bot that helps you track expenses in Google Sheets via Telegram.

## 🛠 Setup Instructions

### 1. Prerequisites
- Python 3.7+
- Telegram account
- Google account

### 2. Create a Virtual Environment (macOS/Linux)
```bash
python3 -m venv venv
source venv/bin/activate
```
3. Install Dependencies
```bash
pip install -r requirements.txt
```
Create requirements.txt with:
```bash
python-telegram-bot==20.0
gspread
python-dotenv
```
4. Set Up Google Sheets API
```bash
Visit Google Cloud Console

Create a new project

Enable the "Google Sheets API"

Go to "APIs & Services" → "Credentials"

Click "Create credentials" → "Service Account"

Grant Viewer or Editor access

Click "Create Key" → Choose JSON → Download as credentials.json

Share your Google Sheet with the service account email (e.g., xyz@project.iam.gserviceaccount.com)
```
5. Create and Setup Your Google Sheet
```
Go to Google Sheets → Create new file → Name it myexpenses

Rename first worksheet to: Sheet1

Add header row:

Date | Description | Amount
```
6. Configure Environment
Create .env file:
```
env
TOKEN=your_telegram_bot_token
USER_NAME=your_telegram_username
USER_ID=your_numeric_telegram_user_id
```
To get your Telegram USER_ID:

Open Telegram

Send message to your bot

Temporarily add print(update.effective_user.id) in handler

Or use @userinfobot in Telegram

🚀 Run the Bot
bash
python app.py
💡 Usage Examples
Add today's expense:
Groceries, 150
Add expense with date:
01/06/2025, Train, 80
Get today's total:
today
Get monthly total:
month
Test if bot is alive:
ping

📝 Logs
Unauthorized access attempts are logged to logs.csv with:

Date

Time

User ID

Username

First Name

Last Name

⚠️ Important Notes
Never commit credentials.json or .env to public repositories

For production, consider cloud hosting (Azure, Render, etc.)


This README includes:
- Clear section headings with emojis
- Proper code blocks with syntax highlighting
- Step-by-step instructions
- Usage examples
- Important warnings
- Consistent formatting

You can copy this directly into your README.md file.
