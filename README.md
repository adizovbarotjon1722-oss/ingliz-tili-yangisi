# English A1 — Telegram kurs boti

Beginner darajadagi ingliz tili kursi uchun to'liq Telegram bot: 10 bo'lim, ketma-ket
(dars sakrab o'tib bo'lmaydi) darslar, har bir darsda lug'at, amaliy mashqlar va test;
har 3 darsda lug'at takrorlash, bo'lim oxirida imtihon. O'qituvchi uchun alohida
admin panel: o'quvchilarni tasdiqlash, analitika, kontent (video, lug'at, mashq, test)
yuklash, AI monitoring va ogohlantirishlar.

## Tez boshlash

```bash
pip install -r requirements.txt
cp .env.example .env        # BOT_TOKEN va SUPERADMIN_IDS ni to'ldiring
python run.py seed          # kontentni bazaga yozish
python run.py bot           # polling rejimida ishga tushirish
```

## Boshqaruv

| Buyruq | Vazifasi |
| --- | --- |
| `python run.py check` | `.env` sozlamalarini tekshirish |
| `python run.py seed` | Kontentni yozish (mavjudlariga tegmaydi) |
| `python run.py seed --force` | Kontentni noldan qayta yozish |
| `python run.py stats` | Baza bo'yicha qisqa hisobot |
| `python run.py bot` | Botni ishga tushirish |

## Arxitektura

```
app/
  config.py            # .env dan sozlamalar
  main.py              # ishga tushirish: middleware'lar, router'lar, polling/webhook
  db/                  # SQLAlchemy async modellari, sessiya
  handlers/            # start, course, practice, quiz, ai, menu, fallback, admin/
  middlewares/         # user konteksti, ruxsat filtri, antispam throttle
  services/            # users, progress, quiz, practice, vocab, analytics, alerts,
                       # settings_store, ratelimit, notify; ai/ (client, tutor, monitor)
  security/            # kirish nazorati (access), audit jurnali
  ui/                  # klaviaturalar, matnlar, render yordamchilari
  content/             # 10 bo'limlik dastur (lug'at/mashq/test matnlari) va seeder
  tasks/scheduler.py   # AI monitoring, eslatmalar, kunlik hisobot davriy vazifalari
assets/images/         # dars rasmlari
run.py                 # boshqaruv CLI
```

## Muhim xususiyatlar

- **Ketma-ketlik qoidasi**: yangi o'quvchi 1.1 darsidan boshlaydi, dars yakunlanmaguncha
  keyingisi yopiq (`handlers/common.py` — `node_state`).
- **Har 3 darsda takrorlash**: seeder avtomatik tuzadi, admin panelda ham yaratib bo'ladi.
- **AI**: o'quvchi savollariga javob (`services/ai/tutor.py`), xavf ostidagi o'quvchilarni
  skanerlash va o'qituvchiga ogohlantirish (`services/ai/monitor.py`), kunlik hisobot,
  o'qituvchi savoliga kurs holati asosida javob.
- **Xavfsizlik**: admin panel faqat xodimlar uchun (`admin/__init__.py` — StaffMiddleware),
  ruxsatsiz foydalanuvchi o'quvchi oqimiga kira olmaydi (`middlewares/access.py`),
  barcha o'zgartirishlar audit jurnalida (`security/audit.py`), antispam throttle.
- **Miqyos**: PostgreSQL + asyncpg (production), Redis (rate-limit va FSM) ixtiyoriy;
  webhooks rejimi (`WEBHOOK_BASE_URL` bo'sh bo'lsa polling); broadcast bo'lakli yuborish.

## Production uchun

1. `DATABASE_URL=postgresql+asyncpg://user:parol@host:5432/baza` qo'ying.
2. `REDIS_URL=redis://host:6379/0` qo'ying (bir nechta jarayon ishga tushsa ham kerak).
3. `WEBHOOK_BASE_URL=https://domain.uz` bilan webhook rejimini yoqing, `WEBHOOK_SECRET`
   ni tasodifiy qatorga almashtiring.
4. Telegram webhook portini (`PORT`, standart 8080) tashqi reverse proxy orqali oching.
5. `SUPERADMIN_IDS` ga faqat ishonchli Telegram ID larni kiriting — ular OWNER rolida
   boshlang'ich kirish huquqiga ega bo'ladi.
