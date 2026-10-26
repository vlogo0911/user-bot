import asyncio, json, logging, os
from pathlib import Path
from telethon import TelegramClient, events

BASE = Path(__file__).resolve().parent
CONFIG = BASE / 'config.json'
BUFFER = BASE / 'buffer.json'
SESSION = BASE / 'user_session'
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('userbot')

def load_json(path, default):
    try: return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError): return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    try: os.chmod(path, 0o600)
    except OSError: pass

async def main():
    cfg = load_json(CONFIG, {})
    api_id = cfg.get('api_id') or os.getenv('API_ID')
    api_hash = cfg.get('api_hash') or os.getenv('API_HASH')
    if not api_id or not api_hash:
        raise SystemExit('config.json ga api_id va api_hash kiriting yoki API_ID/API_HASH environment variables sozlang.')
    client = TelegramClient(str(SESSION), int(api_id), str(api_hash))
    await client.start()  # Telefon raqami va Telegram login kodi faqat shu qurilmada kiritiladi.
    me = await client.get_me()
    print(f'Ulandi: {me.first_name} (@{me.username or "username yo‘q"})')
    print('Saved Messages ga matn yuboring. Keyin o‘zingiz foydalanadigan chatda bufer/буфер/buffer deb yuboring.')
    print('Tezlik: тез | tez 0.1 (0.09–0.70 soniya)')
    data = load_json(BUFFER, {'text':'', 'speed':0.2})

    @client.on(events.NewMessage(outgoing=True))
    async def handle(event):
        nonlocal data
        msg = (event.raw_text or '').strip()
        low = msg.lower()
        if event.is_private and event.chat_id == me.id:
            if msg and not low.startswith(('тез ', 'tez ', '/')) and low not in ('тез','tez'):
                data['text'] = msg
                save_json(BUFFER, data)
                await event.reply('✅ Buffer matni saqlandi.')
            return
        if low in ('буфер','bufer','buffer'):
            text = data.get('text','')
            if not text:
                await event.reply('📭 Buffer bo‘sh. Avval Saved Messages ga matn yuboring.')
                return
            try:
                speed = max(0.09, min(0.70, float(data.get('speed',0.2))))
                await asyncio.sleep(speed)
                reply = await event.get_reply_message() if event.is_reply else None
                await client.send_message(event.chat_id, text, reply_to=reply.id if reply else None)
            except Exception:
                log.exception('Buffer yuborishda xato')
            return
        if low in ('тез','tez'):
            await event.reply(f"⚡ Hozirgi tezlik: {data.get('speed',0.2)} soniya\nO‘zgartirish: тез 0.1")
            return
        if low.startswith(('тез ','tez ')):
            try:
                speed = float(msg.split(maxsplit=1)[1].replace(',','.'))
                if not 0.09 <= speed <= 0.70: raise ValueError
                data['speed'] = speed; save_json(BUFFER, data)
                await event.reply(f'✅ Tezlik {speed} soniyaga o‘zgartirildi.')
            except ValueError:
                await event.reply('❌ 0.09–0.70 oralig‘idagi tezlikni kiriting. Masalan: тез 0.1')
    await client.run_until_disconnected()

if __name__ == '__main__': asyncio.run(main())
