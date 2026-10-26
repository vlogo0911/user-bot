import os, sqlite3, logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
OWNER_ID = int(os.getenv('OWNER_ID', '0'))
DB_PATH = os.getenv('DB_PATH', 'users.sqlite3')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('registration')


def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with connect() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending', requested_at TEXT NOT NULL,
            reviewed_at TEXT, reviewed_by INTEGER)''')


def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('📝 Ro‘yxatdan o‘tish', callback_data='register')],
        [InlineKeyboardButton('📋 Holatim', callback_data='status'), InlineKeyboardButton('📖 Yo‘riqnoma', callback_data='guide')]
    ])



async def update_menu_message(update, text):
    q = update.callback_query
    if not q:
        return False
    try:
        await q.edit_message_text(text, reply_markup=menu())
    except Exception as e:
        if "message is not modified" not in str(e).lower():
            log.warning("Menyu xabari yangilanmadi: %s", e)
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u or update.effective_chat.type != 'private':
        return
    with connect() as c:
        row = c.execute('SELECT status FROM users WHERE user_id=?', (u.id,)).fetchone()
    if row and row['status'] == 'approved':
        text = '✅ Siz tasdiqlangansiz.\n\nAkkauntingizni ulash uchun o‘z qurilmangizda userbot mijozini ishga tushiring. Login kodlari va sessiya faylini hech kimga bermang.'
    elif row and row['status'] == 'pending':
        text = '⏳ So‘rovingiz owner ko‘rib chiqishini kutmoqda.'
    else:
        text = 'Assalomu alaykum! Davom etish uchun ro‘yxatdan o‘ting.'
    await update.message.reply_text(text, reply_markup=menu())

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u or not update.effective_chat or update.effective_chat.type != "private":
        return

    now = datetime.now(timezone.utc).isoformat()
    with connect() as c:
        row = c.execute(
            "SELECT status FROM users WHERE user_id=?", (u.id,)
        ).fetchone()

        if row and row["status"] == "approved":
            text = "✅ Siz allaqachon tasdiqlangansiz."
        elif row and row["status"] == "pending":
            text = "⏳ So‘rovingiz hali ko‘rib chiqilmoqda."
        else:
            c.execute(
                """INSERT INTO users(user_id,username,full_name,status,requested_at)
                   VALUES(?,?,?,'pending',?)
                   ON CONFLICT(user_id) DO UPDATE SET
                   username=excluded.username,
                   full_name=excluded.full_name,
                   status='pending',
                   requested_at=excluded.requested_at,
                   reviewed_at=NULL, reviewed_by=NULL""",
                (u.id, u.username, u.full_name or "Foydalanuvchi", now)
            )
            c.commit()
            text = "📨 So‘rovingiz ownerga yuborildi. Tasdiqni kuting."

            if OWNER_ID:
                name = (u.full_name or "Foydalanuvchi").replace("<", "‹").replace(">", "›")
                uname = "@" + u.username if u.username else "username yo‘q"
                kb = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{u.id}"),
                    InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{u.id}")
                ]])
                try:
                    await context.bot.send_message(
                        OWNER_ID,
                        f"🆕 Ro‘yxatdan o‘tish so‘rovi\\n\\n👤 {name}\\n🔗 {uname}\\n🆔 {u.id}\\n🕒 {now}",
                        reply_markup=kb
                    )
                except Exception:
                    log.exception("Ownerga xabar yuborilmadi")

    if update.callback_query:
        await update.callback_query.answer()
        await update_menu_message(update, text)
    else:
        await update.effective_message.reply_text(text, reply_markup=menu())


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u:
        return
    with connect() as c:
        row = c.execute(
            "SELECT status FROM users WHERE user_id=?", (u.id,)
        ).fetchone()

    labels = {
        "pending": "⏳ Kutilmoqda",
        "approved": "✅ Tasdiqlangan",
        "rejected": "❌ Rad etilgan"
    }
    state = labels.get(row["status"], row["status"]) if row else "Ro‘yxatdan o‘tmagansiz."
    text = "📋 Holatingiz: " + state

    if update.callback_query:
        await update.callback_query.answer()
        await update_menu_message(update, text)
    else:
        await update.effective_message.reply_text(text, reply_markup=menu())


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.effective_message.reply_text('Faqat owner uchun.'); return
    with connect() as c: rows = c.execute('SELECT user_id,full_name,username,status FROM users ORDER BY requested_at DESC LIMIT 50').fetchall()
    if not rows: await update.effective_message.reply_text('So‘rovlar yo‘q.'); return
    await update.effective_message.reply_text('\n'.join(f"{r['status']} | {r['full_name']} | @{r['username'] or 'yo‘q'} | ID {r['user_id']}" for r in rows))

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != OWNER_ID:
        await q.answer('Bu tugma faqat owner uchun.', show_alert=True); return
    await q.answer()
    action, raw = q.data.split(':', 1); target = int(raw)
    status = 'approved' if action == 'approve' else 'rejected'
    with connect() as c:
        row = c.execute('SELECT full_name FROM users WHERE user_id=?', (target,)).fetchone()
        if not row: await q.edit_message_text('So‘rov topilmadi.'); return
        c.execute('UPDATE users SET status=?,reviewed_at=?,reviewed_by=? WHERE user_id=?', (status, datetime.now(timezone.utc).isoformat(), OWNER_ID, target))
    msg = ('🎉 So‘rovingiz tasdiqlandi. Endi yo‘riqnomaga amal qiling.' if status == 'approved' else '❌ So‘rovingiz rad etildi. Qayta so‘rash uchun /request yuboring.')
    try: await context.bot.send_message(target, msg, reply_markup=menu())
    except Exception: log.warning('Foydalanuvchiga xabar yetmadi: %s', target)
    await q.edit_message_text(('✅ Tasdiqlandi: ' if status == 'approved' else '❌ Rad etildi: ') + f"{row['full_name']} (ID {target})")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.data == "register":
        await register(update, context)
    elif q.data == "status":
        await status_cmd(update, context)
    elif q.data == "guide":
        await q.answer()
        text = (
            "📖 Yo‘riqnoma\\n\\n"
            "1. Ro‘yxatdan o‘tish tugmasini bosing va owner tasdig‘ini kuting.\\n"
            "2. Userbotni o‘z qurilmangizda alohida ishga tushiring.\\n"
            "3. Saved Messages’ga oddiy matn yuboring — u buffer bo‘ladi.\\n"
            "4. O‘zingiz foydalanadigan chatda bufer, буфер yoki buffer buyrug‘ini ishlating.\\n"
            "5. Tezlikni ko‘rish: тез. O‘zgartirish: тез 0.1.\\n\\n"
            "⚠️ Login kodi, 2FA paroli va session faylini hech kimga bermang."
        )
        await update_menu_message(update, text)


def main():
    if not BOT_TOKEN or not OWNER_ID: raise SystemExit('BOT_TOKEN va OWNER_ID environment variables kerak.')
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('request', register))
    app.add_handler(CommandHandler('status', status_cmd))
    app.add_handler(CommandHandler('users', users_cmd))
    app.add_handler(CallbackQueryHandler(review, pattern=r'^(approve|reject):\d+$'))
    app.add_handler(CallbackQueryHandler(buttons, pattern=r'^(register|status|guide)$'))
    log.info('Registration bot ishga tushdi')
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
