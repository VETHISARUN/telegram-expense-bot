# 💸 Telegram Expense Tracker Bot

A bot that helps you track expenses in **Google Sheets** via **Telegram**.

---

## 🛠 Setup Instructions

### 1. Prerequisites
- Python **3.10+**
- Telegram account
- Google account with access to Google Sheets API

---

### 2. Create a Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Create `requirements.txt` with:
```txt
python-telegram-bot==20.0
gspread
oauth2client
python-dotenv
matplotlib
```

---

### 4. Set Up Google Sheets API

1. Visit [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable the Google Sheets API
4. Go to **APIs & Services** → **Credentials**
5. Click **Create credentials** → **Service Account**
6. Grant **Viewer** or **Editor** access
7. Click **Create Key** → **JSON** → Download as `credentials.json`
8. Share your Google Sheet with the service account email (e.g., `xyz@project.iam.gserviceaccount.com`)

---

### 5. Create and Setup Your Google Sheet

1. Go to [Google Sheets](https://sheets.google.com) → Create a new file → Name it `myexpenses`
2. Rename the first worksheet to: `Sheet1`
3. Add a header row:
   ```
   Date | Category | Amount | Note
   ```

---

### 6. Configure Environment

Create a `.env` file:
```env
TOKEN=your_telegram_bot_token
USER_NAME=your_telegram_username
USER_ID=your_numeric_telegram_user_id
SPREADSHEET_ID=your_google_spreadsheet_id
```

**To get your Telegram USER_ID:**
- Open Telegram
- Send a message to your bot
- Temporarily add `print(update.effective_user.id)` in a handler
- Or use [@userinfobot](https://t.me/userinfobot)

---

## 🚀 Run the Bot

```bash
python bot.py
```

---

## 💡 Usage Examples

### Add today's expense
```
/add 150 groceries lunch
```

### Add expense with custom date
```
/add 01/06/2025 train 80
```

### Get today's total
```
/summary today
```

### Get monthly total
```
/summary month
```

### View chart of monthly expenses
```
/chart
```

### Check if bot is alive
```
/ping
```

---


## 📌 Features

✅ Add expenses by message  
✅ Automatic storage in Google Sheets  
✅ Daily, monthly, yearly summaries  
✅ Pie & bar chart visualizations  
✅ Optimized with in-memory cache + batch writes  
✅ Error handling with retries & backoff