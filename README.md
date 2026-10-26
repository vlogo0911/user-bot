# Userbot + ro'yxatdan o'tish boti

## Arxitektura
- `bot.py` — Railway serverida ishlaydigan ro'yxatdan o'tish va owner tasdiqlash boti.
- `userbot.py` — HAR BIR foydalanuvchi o'z qurilmasida ishga tushiradigan Telegram mijozidir. Bitta nusxa bitta Telegram akkaunti uchun.
- Telefon raqami, Telegram login kodi, 2FA paroli va `.session` fayli foydalanuvchining o'z qurilmasida qoladi. Ularni botga, ownerga yoki GitHub'ga yubormang.

## Railway (faqat ro'yxatdan o'tish boti)
Environment Variables:
- `BOT_TOKEN` — BotFather bergan bot tokeni
- `OWNER_ID` — ownerning Telegram numeric ID raqami
- `DB_PATH` — ixtiyoriy, doimiy volume bo'lsa masalan `/data/users.sqlite3`

Build/deploy buyruq: `Procfile` dagi `worker: python bot.py`.
`requirements.txt` Railway tomonidan o'rnatiladi.

## Har bir foydalanuvchi qurilmasida userbotni sozlash
1. Python va pip o'rnating.
2. `pip install -r requirements.txt`
3. `config.example.json` faylidan nusxa olib `config.json` deb nomlang.
4. `config.json` ichiga o'zingizning Telegram `api_id` va `api_hash` qiymatlaringizni yozing.
5. `python userbot.py` ni ishga tushiring. Raqam va Telegram yuborgan login kodini faqat shu qurilmada kiriting.
6. Telegram Saved Messages ga oddiy matn yuboring — bu buferga saqlanadi.
7. O'zingiz foydalanadigan chatda `bufer`, `буфер` yoki `buffer` deb yuboring.
8. `tez` yoki `тез` joriy kechikishni ko'rsatadi. `tez 0.1` yoki `тез 0.1` 0.1 soniyaga sozlaydi. Ruxsat etilgan oraliq: 0.09–0.70 soniya.

## Muhim cheklov
Bu paket foydalanuvchilarning telefon raqami va login kodini bot ichida qabul qilib, akkauntlarini serverga ulaydigan multi-account tizim EMAS. Bunday qilish o'rniga akkaunt egasi o'z qurilmasida ulanadi va sessiyani o'zi saqlaydi. Serverdagi bot ro'yxatdan o'tish va owner tasdig'ini boshqaradi. `userbot.py` alohida ishga tushiriladi; serverdagi `bot.py` uni avtomatik boshqarmaydi.

Faqat o'zingiz foydalanadigan va xabar yuborishga rozilik berilgan chatlarda ishlating; ommaviy/so'ralmagan xabar yubormang.
