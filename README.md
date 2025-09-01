# 💸 Telegram Expense Tracker Bot

A bot that helps you track expenses in **Google Sheets** via **Telegram**.

---

## 🛠 Setup Instructions

### 1. Prerequisites
- Python **3.10+**
- Telegram account
- Google account with access to Google Sheets API

---

### 2. Create a Virtual Environment (macOS/Linux)
```bash
python3 -m venv venv
source venv/bin/activate
Windows:

bash
Copy code
python -m venv venv
venv\Scripts\activate
3. Install Dependencies
bash
Copy code
pip install -r requirements.txt
Create requirements.txt with:

txt
Copy code
python-telegram-bot==20.0
gspread
oauth2client
python-dotenv
matplotlib
4. Set Up Google Sheets API
Visit Google Cloud Console

Create a new project

Enable the Google Sheets API

Go to APIs & Services → Credentials

Click Create credentials → Service Account

Grant Viewer or Editor access

Click Create Key → JSON → Download as credentials.json

Share your Google Sheet with the service account email (e.g., xyz@project.iam.gserviceaccount.com)

5. Create and Setup Your Google Sheet
Go to Google Sheets → Create a new file → Name it myexpenses

Rename the first worksheet to: Sheet1

Add a header row:

javascript
Copy code
Date | Category | Amount | Note
6. Configure Environment
Create a .env file:

env
Copy code
TOKEN=your_telegram_bot_token
USER_NAME=your_telegram_username
USER_ID=your_numeric_telegram_user_id
SPREADSHEET_ID=your_google_spreadsheet_id
To get your Telegram USER_ID:

Open Telegram

Send a message to your bot

Temporarily add print(update.effective_user.id) in a handler

Or use @userinfobot

🚀 Run the Bot
bash
Copy code
python bot.py
💡 Usage Examples
Add today's expense
bash
Copy code
/add 150 groceries lunch
Add expense with custom date
bash
Copy code
/add 01/06/2025 train 80
Get today's total
bash
Copy code
/summary today
Get monthly total
bash
Copy code
/summary month
View chart of monthly expenses
bash
Copy code
/chart
Check if bot is alive
bash
Copy code
/ping
📝 Logs
Unauthorized access attempts are logged in logs.csv with:

Date

Time

User ID

Username

First Name

Last Name

⚠️ Important Notes
❌ Never commit credentials.json or .env to public repositories

🌐 For production, consider cloud hosting (Azure, Render, Railway, or Docker on a VM)

🔒 Use .gitignore to protect secrets

📌 Features
✅ Add expenses by message

✅ Automatic storage in Google Sheets

✅ Daily, monthly, yearly summaries

✅ Pie & bar chart visualizations

✅ Optimized with in-memory cache + batch writes

✅ Error handling with retries & backoff