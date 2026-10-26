BIRLASHTIRILGAN PAKET: OWNER TASDIG'I + SHAXSIY USERBOT MIJOZI

Muhim arxitektura:
- bot.py: umumiy Telegram bot, /start so'rovi, owner tasdiqlash/rad etish, /status, /request, /users.
- userbot.py: har bir foydalanuvchi O'Z QURILMASIDA ishga tushiradi; o'z Telegram akkauntiga ulanadi va bufer/tezlikni mahalliy saqlaydi.
- Bot owner tasdig'i userbotni avtomatik ishga tushirmaydi. Tasdiqlangan foydalanuvchi o'z qurilmasida userbot.py ni alohida sozlaydi.
- API_ID/API_HASH o'zingizniki bo'lishi kerak. Ochiq internetdagi tasodifiy kalitlar kafolatlanmagan.
- Telegram login kodi, 2FA paroli yoki .session faylini umumiy botga yubormang.

O'RNATISH
pip install -r requirements.txt

Umumiy ro'yxatdan o'tish botini ishga tushirish:
export BOT_TOKEN='BotFather token'
export OWNER_ID='sizning raqamli Telegram ID'
python bot.py

Har bir foydalanuvchining shaxsiy qurilmasida userbot:
export API_ID='o'zingizning API_ID'
export API_HASH='o'zingizning API_HASH'
python userbot.py

Bot va userbotni bir xil jarayonda ishga tushirish shart emas. Railwayda bot.py doimiy ishlashi mumkin; userbotlar foydalanuvchilarning o'z qurilmalarida ishlaydi.
