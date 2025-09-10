# handlers.py  (REPLACE your old handlers.py with this)
import asyncio
import json
import os
from collections import defaultdict, deque, Counter
from datetime import datetime
from typing import Dict, Any

from telegram import Update
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

from keyboards import categories_keyboard, confirm_keyboard
import sheets
import charts
from utils import parse_amount, now_date_str

# Conversation states
SELECT_CATEGORY, ENTER_AMOUNT, ENTER_NOTE, CONFIRM = range(4)

# Cache file
CACHE_FILE = "cache.json"

# Background queue for writes to Google Sheets
_write_queue: asyncio.Queue | None = None
_worker_started = False

# Cache structure (in-memory)
_cache_lock = asyncio.Lock()
_totals_by_day: Dict[str, float] = defaultdict(float)      # 'DD/MM/YYYY' -> amount
_totals_by_month: Dict[str, float] = defaultdict(float)    # 'YYYY-MM' -> amount
_totals_by_year: Dict[str, float] = defaultdict(float)     # 'YYYY' -> amount
_totals_by_category: Dict[str, float] = defaultdict(float) # 'food' -> amount
_recent = deque(maxlen=200)                                # most recent entries
_processed_tx_ids = set()                                  # optional dedupe if needed
# We will not rely on any DB id; keep for future use.


def _date_to_month_key(date_s: str) -> str:
    # date_s expected "DD/MM/YYYY"
    try:
        dt = datetime.strptime(date_s, "%d/%m/%Y")
    except Exception:
        dt = datetime.now()
    return dt.strftime("%Y-%m")


def _date_to_year_key(date_s: str) -> str:
    try:
        dt = datetime.strptime(date_s, "%d/%m/%Y")
    except Exception:
        dt = datetime.now()
    return dt.strftime("%Y")


async def _save_cache_to_disk():
    """Persist the aggregates and recent list to disk (non-blocking)."""
    # We intentionally only store aggregates to keep file small.
    async with _cache_lock:
        data = {
            "totals_by_day": dict(_totals_by_day),
            "totals_by_month": dict(_totals_by_month),
            "totals_by_year": dict(_totals_by_year),
            "totals_by_category": dict(_totals_by_category),
            "recent": list(_recent),
        }
    loop = asyncio.get_event_loop()
    def _write():
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    await loop.run_in_executor(None, _write)


async def _load_cache_from_disk():
    """Load aggregates if cache file exists."""
    if not os.path.exists(CACHE_FILE):
        return
    loop = asyncio.get_event_loop()

    def _read():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        data = await loop.run_in_executor(None, _read)
    except Exception:
        return

    async with _cache_lock:
        _totals_by_day.clear()
        _totals_by_day.update({k: float(v) for k, v in data.get("totals_by_day", {}).items()})
        _totals_by_month.clear()
        _totals_by_month.update({k: float(v) for k, v in data.get("totals_by_month", {}).items()})
        _totals_by_year.clear()
        _totals_by_year.update({k: float(v) for k, v in data.get("totals_by_year", {}).items()})
        _totals_by_category.clear()
        _totals_by_category.update({k: float(v) for k, v in data.get("totals_by_category", {}).items()})
        _recent.clear()
        for item in data.get("recent", []):
            _recent.append(item)


async def _ensure_worker_started():
    global _write_queue, _worker_started
    if _worker_started:
        return
    if _write_queue is None:
        _write_queue = asyncio.Queue()
    # start background task
    asyncio.create_task(_background_writer())
    _worker_started = True


async def _enqueue_row_for_write(row: list):
    """Add a row to the in-memory queue to be pushed to Sheets by background worker."""
    await _ensure_worker_started()
    await _write_queue.put(row)


async def _background_writer():
    """Background loop that flushes write queue to Google Sheets."""
    # simple retry/backoff behavior per-row
    while True:
        try:
            row = await _write_queue.get()
            success = False
            attempt = 0
            max_attempts = 5
            backoff = 1.0
            while not success and attempt < max_attempts:
                attempt += 1
                try:
                    # sheets.append_transaction is blocking; run in thread
                    await asyncio.to_thread(sheets.append_transaction, row)
                    success = True
                except Exception as e:
                    # log and retry with exponential backoff
                    # (don't crash the loop)
                    print(f"[background_writer] attempt {attempt} failed: {e}")
                    await asyncio.sleep(backoff)
                    backoff *= 2
            if not success:
                # final fallback: requeue at the end (so we don't lose it),
                # and also persist to local cache file so it's safe.
                print("[background_writer] failed to sync row after retries, re-queuing and saving cache.")
                await _write_queue.put(row)
                await _save_cache_to_disk()
                # wait longer before continuing to avoid hot loop
                await asyncio.sleep(10)
        except Exception as e:
            print("[background_writer] unexpected error:", e)
            await asyncio.sleep(5)  # on unexpected error, back off briefly


def _add_expense_to_cache(date_s: str, category: str, amount: float, note: str, username: str):
    """Synchronous helper to update in-memory aggregates. Called within cache lock."""
    # date_s expected "DD/MM/YYYY"
    _totals_by_day[date_s] = _totals_by_day.get(date_s, 0.0) + float(amount)
    month_k = _date_to_month_key(date_s)
    _totals_by_month[month_k] = _totals_by_month.get(month_k, 0.0) + float(amount)
    year_k = _date_to_year_key(date_s)
    _totals_by_year[year_k] = _totals_by_year.get(year_k, 0.0) + float(amount)
    _totals_by_category[category] = _totals_by_category.get(category, 0.0) + float(amount)
    # recent entry
    _recent.appendleft({
        "date": date_s,
        "category": category,
        "amount": float(amount),
        "note": note,
        "username": username,
    })


async def add_expense(date_s: str, category: str, amount: float, note: str, username: str):
    """Public: update cache, persist cache file periodically, and enqueue write to Sheets."""
    # 1) update in-memory quickly
    async with _cache_lock:
        _add_expense_to_cache(date_s, category, amount, note, username)
    # 2) persist cache to disk in background (do not await long in caller)
    asyncio.create_task(_save_cache_to_disk())
    # 3) enqueue row for Sheets
    row = [date_s, category, f"{float(amount):.2f}", note or "", username or ""]
    await _enqueue_row_for_write(row)


# ----------------- Telegram conversation handlers -----------------

# Entry: /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # lazy-load existing cache file once on first call
    await _load_cache_from_disk()
    await _ensure_worker_started()

    user = update.effective_user
    context.user_data.clear()
    context.user_data["user"] = {"id": user.id, "username": user.username}
    await update.message.reply_text(
        f"Hi {user.first_name}! Choose a category for this expense:",
        reply_markup=categories_keyboard(),
    )
    return SELECT_CATEGORY


# When a category button pressed
async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data  # e.g., "cat|food" or "cat|custom"
    _, value = data.split("|", 1)
    if value == "custom":
        await query.edit_message_text("Type your custom category name (text):")
        return SELECT_CATEGORY  # we'll accept free text via message
    # store and ask for amount
    context.user_data.setdefault("txn", {})["category"] = value
    await query.edit_message_text(f"Category: {value.title()}\n\nNow send the amount (e.g. 120 or 120.50):")
    return ENTER_AMOUNT


# Accept free-text category (when user typed instead of pressing)
async def category_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data.setdefault("txn", {})["category"] = text
    await update.message.reply_text(f"Category set to: {text}\nNow enter amount (e.g. 199):")
    return ENTER_AMOUNT


# Amount handler
async def amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    try:
        amount = parse_amount(text)
    except Exception:
        await update.message.reply_text("Couldn't parse amount. Send numeric like: 120 or 120.50")
        return ENTER_AMOUNT
    context.user_data["txn"]["amount"] = amount
    await update.message.reply_text("Optional: add a note/description (or send /skip to skip):")
    return ENTER_NOTE


# Skip note
async def skip_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["txn"]["note"] = ""
    return await _ask_confirm(update, context)


# Note handler
async def note_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    context.user_data["txn"]["note"] = text
    return await _ask_confirm(update, context)


# Internal: ask confirm with summary
async def _ask_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txn = context.user_data.get("txn", {})
    date = now_date_str()  # returns "DD/MM/YYYY"
    user = context.user_data.get("user", {})
    cat = txn.get("category", "uncategorized")
    amt = txn.get("amount", 0)
    note = txn.get("note", "")
    msg = f"Please confirm:\n\nDate: {date}\nCategory: {cat}\nAmount: ₹{amt:.2f}\nNote: {note or '-'}"
    # If this is a callback query, edit; else reply
    if update.callback_query:
        await update.callback_query.edit_message_text(msg, reply_markup=confirm_keyboard())
    else:
        await update.message.reply_text(msg, reply_markup=confirm_keyboard())
    return CONFIRM


# Confirm callback handler
async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Fast confirm: update cache + enqueue write, reply instantly.
    Do NOT call blocking sheets.append_transaction directly here.
    """
    query = update.callback_query
    await query.answer()
    _, value = query.data.split("|", 1)  # confirm|yes / confirm|edit / confirm|cancel
    if value == "edit":
        await query.edit_message_text("OK — send a new amount (or category) to edit. Type category name or amount:")
        return ENTER_AMOUNT
    if value == "cancel":
        await query.edit_message_text("Cancelled. Use /start to add again.")
        context.user_data.pop("txn", None)
        return ConversationHandler.END

    # Confirm yes -> update cache and enqueue row for sheets (fast)
    txn = context.user_data.get("txn", {})
    date = now_date_str()
    category = txn.get("category", "uncategorized")
    amount = float(txn.get("amount", 0))
    note = txn.get("note", "")
    username = str(context.user_data.get("user", {}).get("username", "unknown"))

    # update cache + queue (async)
    try:
        # fast update + background write
        await add_expense(date, category, amount, note, username)
    except Exception as e:
        # If something goes wrong updating cache/queue, inform user
        await query.edit_message_text(f"❌ Failed to record locally: {e}")
        return ConversationHandler.END

    # Respond immediately (instant confirm)
    await query.edit_message_text(f"✅ Saved: {category} — ₹{amount:.2f}\nSaved locally and will sync to Google Sheets shortly.")
    context.user_data.pop("txn", None)
    return ConversationHandler.END


# Cancel command (global)
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled. Use /start to add a new expense.")
    context.user_data.clear()
    return ConversationHandler.END


# Stats handler (for commands: /today /month /summary)
async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # All stats are served from in-memory cache (fast, O(1))
    text = update.message.text.strip().lower()
    if text.startswith("/today"):
        date = now_date_str()  # 'DD/MM/YYYY'
        async with _cache_lock:
            total = _totals_by_day.get(date, 0.0)
        await update.message.reply_text(f"Today's total: ₹{total:.2f}")
        return

    if text.startswith("/month"):
        # default: current month
        now = datetime.now()
        key = now.strftime("%Y-%m")
        async with _cache_lock:
            agg = dict(_totals_by_category)
            month_total = _totals_by_month.get(key, 0.0)
        # build response
        lines = [f"{k}: ₹{v:.2f}" for k, v in agg.items()]
        msg = "This month's spend (per category - from cache):\n" + "\n".join(lines) + f"\n\nTotal: ₹{month_total:.2f}"
        await update.message.reply_text(msg)
        return

    if text.startswith("/summary"):
        # usage: /summary DD/MM/YYYY:DD/MM/YYYY  -> fallback: if omitted, show month
        parts = text.split()
        if len(parts) < 2:
            # fallback to month summary
            now = datetime.now()
            month_key = now.strftime("%Y-%m")
            async with _cache_lock:
                month_total = _totals_by_month.get(month_key, 0.0)
            await update.message.reply_text(f"Month ({month_key}) total: ₹{month_total:.2f}")
            return
        rng = parts[1]
        try:
            start_s, end_s = rng.split(":")
            s_dt = datetime.strptime(start_s, "%d/%m/%Y")
            e_dt = datetime.strptime(end_s, "%d/%m/%Y")
            # We'll iterate through cached daily totals within range (cheap)
            total = 0.0
            async with _cache_lock:
                for day_k, amt in _totals_by_day.items():
                    try:
                        d = datetime.strptime(day_k, "%d/%m/%Y")
                        if s_dt <= d <= e_dt:
                            total += amt
                    except Exception:
                        continue
            await update.message.reply_text(f"Summary {start_s} to {end_s}:\nTotal: ₹{total:.2f}")
        except Exception:
            await update.message.reply_text("Could not parse range. Use DD/MM/YYYY:DD/MM/YYYY")
        return

    await update.message.reply_text("Unknown stats command. Use /today, /month or /summary DD/MM/YYYY:DD/MM/YYYY")


# Chart handler: /chart [pie|bar] (reads from cache)
async def chart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    chart_type = "pie"
    if "bar" in text:
        chart_type = "bar"

    async with _cache_lock:
        agg = dict(_totals_by_category)

    if not agg:
        await update.message.reply_text("No data yet to build chart.")
        return

    # Create chart in a thread (chart functions use matplotlib but are headless)
    try:
        if chart_type == "bar":
            buf = await asyncio.to_thread(charts.bar_chart_from_dict, agg, "This month's expenses")
        else:
            buf = await asyncio.to_thread(charts.pie_chart_from_dict, agg, "This month's expenses")

        if buf is None:
            await update.message.reply_text("Failed to create chart.")
            return

        # charts.* returns BytesIO or path; prefer BytesIO -> send as photo
        if hasattr(buf, "read"):
            buf.seek(0)
            await update.message.reply_photo(buf)
        else:
            # assume it's a file path
            with open(buf, "rb") as f:
                await update.message.reply_photo(f)
            try:
                os.remove(buf)
            except Exception:
                pass
    except Exception as e:
        await update.message.reply_text(f"Chart generation failed: {e}")


# Message fallback to guide user while in conversation
async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I didn't understand that. Use /start to add an expense or /today /month /chart.")


# ConversationHandler registration
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start_command)],
    states={
        SELECT_CATEGORY: [
            CallbackQueryHandler(category_selected, pattern="^cat\\|"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, category_text),
        ],
        ENTER_AMOUNT: [
            MessageHandler(filters.Regex(r"^[\d₹\\.\\,\\s]+$"), amount_input),
            MessageHandler(filters.TEXT & ~filters.COMMAND, amount_input),
        ],
        ENTER_NOTE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, note_input),
            CommandHandler("skip", skip_note),
        ],
        CONFIRM: [
            CallbackQueryHandler(confirm_callback, pattern="^confirm\\|"),
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel_command)],
    allow_reentry=True,
)
