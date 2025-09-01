from telegram import InlineKeyboardButton, InlineKeyboardMarkup

DEFAULT_CATEGORIES = [
    "food", "transport", "groceries", "entertainment", "bills", "health", "other"
]

def categories_keyboard():
    keyboard = []
    row = []
    for i, cat in enumerate(DEFAULT_CATEGORIES, 1):
        row.append(InlineKeyboardButton(cat.title(), callback_data=f"cat|{cat}"))
        if i % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("Custom", callback_data="cat|custom")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm", callback_data="confirm|yes"),
         InlineKeyboardButton("✏️ Edit", callback_data="confirm|edit")],
        [InlineKeyboardButton("❌ Cancel", callback_data="confirm|cancel")]
    ])
