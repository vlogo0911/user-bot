import asyncio, json, os
from pathlib import Path
from telethon import TelegramClient, events

BASE_DIR=Path(__file__).resolve().parent
CONFIG_PATH=BASE_DIR/"config.json"
BUFFER_PATH=BASE_DIR/"buffer.json"
SESSION_PATH=BASE_DIR/"user_session"

def read_json(path, default):
    try:
        with path.open("r",encoding="utf-8") as f: return json.load(f)
    except (FileNotFoundError,json.JSONDecodeError): return default

def write_json(path,value):
    temp=path.with_suffix(path.suffix+".tmp")
    with temp.open("w",encoding="utf-8") as f: json.dump(value,f,ensure_ascii=False,indent=2)
    temp.replace(path)

config=read_json(CONFIG_PATH,{"speed":0.10})
buffer_data=read_json(BUFFER_PATH,{"text":""})
speed=max(0.09,min(0.70,float(config.get("speed",0.10))))
api_id_raw=os.getenv("API_ID","").strip()
api_hash=os.getenv("API_HASH","").strip()
if not api_id_raw or not api_hash:
    raise SystemExit("API_ID va API_HASH kerak. O'zingizning Telegram API ma'lumotlaringizni sozlang.")
try: api_id=int(api_id_raw)
except ValueError: raise SystemExit("API_ID raqam bo'lishi kerak.")
client=TelegramClient(str(SESSION_PATH),api_id,api_hash)

def save_speed(value):
    global speed
    speed=round(value,2); write_json(CONFIG_PATH,{"speed":speed})

def save_buffer(value):
    global buffer_data
    buffer_data={"text":value}; write_json(BUFFER_PATH,buffer_data)

@client.on(events.NewMessage(outgoing=True))
async def outgoing_handler(event):
    text=(event.raw_text or "").strip()
    if not text: return
    lower=text.lower()
    if lower in ("тез","tez"):
        await event.edit(f"⚡ Joriy tezlik: {speed:.2f} soniya"); return
    if lower.startswith(("тез ","tez ")):
        try: value=float(text.split(maxsplit=1)[1].replace(",","."))
        except (IndexError,ValueError):
            await event.edit("❌ Misol: тез 0.1"); return
        if not 0.09<=value<=0.70:
            await event.edit("❌ Tezlik 0.09 dan 0.70 soniyagacha bo'lishi kerak."); return
        save_speed(value); await event.edit(f"⚡ Tezlik saqlandi: {speed:.2f} soniya"); return
    if lower in ("буфер","bufer","buffer"):
        saved=str(buffer_data.get("text","")).strip()
        if not saved:
            await event.edit("📭 Bufer bo'sh. Avval Saved Messages'ga matn yuboring."); return
        reply_to=event.reply_to_msg_id if event.is_reply else None
        try: await event.delete()
        except Exception: pass
        await asyncio.sleep(speed)
        await client.send_message(event.chat_id,saved,reply_to=reply_to)
        return
    me=await client.get_me()
    if event.is_private and event.chat_id==me.id:
        save_buffer(text)

async def main():
    print("Userbot ishga tushmoqda. Kod/parolni faqat shu qurilmada kiriting.")
    await client.start()
    me=await client.get_me()
    print(f"Ulandi: {me.first_name or 'Telegram foydalanuvchisi'}")
    print("Buyruqlar: тез | тез 0.1 | буфер")
    await client.run_until_disconnected()

if __name__=="__main__":
    with client: client.loop.run_until_complete(main())
