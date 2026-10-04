# English A1 bot — rivojlantirish rejasi

## 1. Kontent modeli (ikki kitob roli)
| Kitob | Botdagi vazifasi |
|---|---|
| Coursebook | Dars: tushuntirish, lug'at, dialog, video, bo'lim takrori |
| Workbook | Mashq + uyga vazifa: sahifa havolasi + botdagi original mashqlar |

Har dars: **Dars → Lug'at → Mashq → Quiz → Uyga vazifa (Workbook p.X + bot topshirig'i)**.
Har 3 darsda lug'at takrori, bo'lim oxirida imtihon (80%+ bo'lsa keyingi bo'lim ochiladi).

## 2. Qiziqarli qiladigan funksiyalar (ustuvorlik bo'yicha)
1. **XP va streak** — har to'g'ri javob +XP, kunlik seriya 🔥, streak yo'qolmasin deb eslatma.
2. **Haftalik liga** — Bronza → Kumush → Oltin; guruh ichida reyting.
3. **Kunlik challenge** — 5 daqiqalik aralash mashq + bonus XP.
4. **Takrorlash (spaced repetition)** — xato qilingan so'zlar 1-3-7 kunda qaytadi.
5. **Ovozli mashqlar** — o'quvchi ovoz yuboradi, AI talaffuz/gap to'g'riligini baholaydi (`services/ai/tutor.py`).
6. **Mini-o'yinlar** — so'z topish, gap tuzish (order), tez-quiz (taymer), juftlash.
7. **Nishonlar (badges)** — "Alifbo ustasi", "10 kun seriya", "1-bo'lim imtihoni 100%".
8. **Sertifikat (PDF)** — bo'lim / kurs tugaganda avtomatik.
9. **AI suhbatdosh** — dars mavzusida rolli suhbat (mehmonxonada, do'konda).
10. **O'qituvchi paneli** — uyga vazifa tekshiruvi, xavf ostidagi o'quvchilar, kunlik hisobot (mavjud).

## 3. Bosqichlar
- **1-bosqich (1 hafta):** 10 bo'lim kontentini shu formatda to'ldirish (1-bo'lim tayyor); seeder'ga JSON import.
- **2-bosqich:** XP, streak, badge, kunlik challenge.
- **3-bosqich:** spaced repetition, ovozli mashqlar, liga.
- **4-bosqich:** sertifikat, statistika, reklama/taklif (referal) tizimi.

## 4. Xavfsizlik
- `.env` dagi BOT_TOKEN va kalitlarni hech qachon umumiy joyga yubormang; oshkor bo'lsa @BotFather → /revoke.
- Kitob PDF'larini bot repozitoriyasiga qo'shmang; kontent original yozilgan bo'lishi kerak.
