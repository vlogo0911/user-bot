import os, sqlite3, logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
DB_PATH = os.getenv("DB_PATH", "users.sqlite3")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("registration")

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', requested_at TEXT NOT NULL,
        reviewed_at TEXT, reviewed_by INTEGER)""")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u or update.effective_chat.type != "private":
        return
    with connect() as c:
        row = c.execute("SELECT status FROM users WHERE user_id=?", (u.id,)).fetchone()
    if row and row["status"] == "approved":
        await update.message.reply_text(
            "✅ Siz tasdiqlangansiz.\n\n"
            "Bu bot ruxsat holatini boshqaradi. `буфер` funksiyasi uchun userbot mijozini "
            "o‘z qurilmangizda alohida ishga tushiring. Sessiya fayli, login kodi va parolni "
            "hech kimga yubormang."
        )
        return
    if row and row["status"] == "pending":
        await update.message.reply_text("⏳ So‘rovingiz owner ko‘rib chiqishini kutmoqda.")
        return
    now = datetime.now(timezone.utc).isoformat()
    with connect() as c:
        c.execute("""INSERT INTO users(user_id,username,full_name,status,requested_at)
        VALUES(?,?,?,'pending',?) ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username, full_name=excluded.full_name, status='pending',
        requested_at=excluded.requested_at, reviewed_at=NULL, reviewed_by=NULL""",
        (u.id, u.username, u.full_name or "Foydalanuvchi", now))
    await update.message.reply_text("📨 Ro‘yxatdan o‘tish so‘rovingiz ownerga yuborildi. Tasdiqni kuting.")
    name = (u.full_name or "Foydalanuvchi").replace("<","‹").replace(">","›")
    uname = f"@{u.username}" if u.username else "username yo‘q"
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{u.id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject:{u.id}")
    ]])
    try:
        await context.bot.send_message(
            OWNER_ID,
            f"🆕 Yangi ro‘yxatdan o‘tish so‘rovi\n\n👤 Ism: {name}\n🔗 Username: {uname}\n🆔 ID: {u.id}\n🕒 {now}",
            reply_markup=keyboard
        )
    except Exception:
        log.exception("Ownerga so‘rov yuborilmadi")

async def request_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    if not u: return
    with connect() as c:
        row = c.execute("SELECT status FROM users WHERE user_id=?", (u.id,)).fetchone()
    if row and row["status"] == "approved":
        await update.message.reply_text("✅ Siz allaqachon tasdiqlangansiz.")
    elif row and row["status"] == "pending":
        await update.message.reply_text("⏳ So‘rovingiz ko‘rib chiqilmoqda.")
    else:
        # Re-use /start request flow by deleting any rejected record first.
        with connect() as c:
            c.execute("DELETE FROM users WHERE user_id=?", (u.id,))
        await start(update, context)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    with connect() as c:
        row = c.execute("SELECT status FROM users WHERE user_id=?", (u.id,)).fetchone()
    labels={"pending":"⏳ Kutilmoqda","approved":"✅ Tasdiqlangan","rejected":"❌ Rad etilgan"}
    await update.message.reply_text("Holat: " + (labels.get(row["status"], row["status"]) if row else "Ro‘yxatdan o‘tmagansiz. /start bosing."))

async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Faqat owner uchun.")
        return
    with connect() as c:
        rows=c.execute("SELECT user_id,full_name,username,status FROM users ORDER BY requested_at DESC LIMIT 50").fetchall()
    if not rows:
        await update.message.reply_text("So‘rovlar yo‘q."); return
    await update.message.reply_text("\n".join(
        f"{r['status']} | {r['full_name']} | @{r['username'] or 'yo‘q'} | ID {r['user_id']}" for r in rows
    ))

async def review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    if q.from_user.id != OWNER_ID:
        await q.answer("Bu tugma faqat owner uchun.", show_alert=True); return
    await q.answer()
    try:
        action, raw=q.data.split(":",1); target=int(raw)
    except Exception:
        await q.edit_message_text("So‘rov formati noto‘g‘ri."); return
    status="approved" if action=="approve" else "rejected" if action=="reject" else None
    if not status: return
    with connect() as c:
        row=c.execute("SELECT full_name FROM users WHERE user_id=?", (target,)).fetchone()
        if not row:
            await q.edit_message_text("So‘rov topilmadi."); return
        c.execute("UPDATE users SET status=?,reviewed_at=?,reviewed_by=? WHERE user_id=?",
                  (status,datetime.now(timezone.utc).isoformat(),OWNER_ID,target))
    if status=="approved":
        msg=("🎉 So‘rovingiz tasdiqlandi!\n\n"
             "Userbot funksiyasidan foydalanish uchun o‘z qurilmangizdagi mijozni sozlang. "
             "Login kodlari, parollar va sessiya fayllarini hech kimga bermang.")
        result=f"✅ Tasdiqlandi: {row['full_name']} (ID {target})"
    else:
        msg="❌ Ro‘yxatdan o‘tish so‘rovingiz rad etildi. Qayta so‘rash uchun /request yuboring."
        result=f"❌ Rad etildi: {row['full_name']} (ID {target})"
    try: await context.bot.send_message(target,msg)
    except Exception: log.warning("Qaror xabari foydalanuvchiga yetmadi: %s",target)
    await q.edit_message_text(result)

def main():
    if not BOT_TOKEN or not OWNER_ID:
        raise SystemExit("BOT_TOKEN va OWNER_ID ni environment variables sifatida kiriting.")
    init_db()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("request",request_cmd))
    app.add_handler(CommandHandler("status",status_cmd))
    app.add_handler(CommandHandler("users",users_cmd))
    app.add_handler(CallbackQueryHandler(review,pattern=r"^(approve|reject):\d+$"))
    log.info("Bot ishga tushdi.")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__": main()
