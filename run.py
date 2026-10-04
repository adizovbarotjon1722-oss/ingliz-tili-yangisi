"""Loyiha boshqaruv CLI.

Foydalanish:
    python run.py check              # sozlamalar + token jonli tekshiruvi (getMe)
    python run.py seed               # kontentni bazaga yozish (mavjudlariga tegmaydi)
    python run.py seed --force       # kontentni noldan qayta yozish (tahrir va natijalar o'chadi)
    python run.py stats              # baza bo'yicha qisqa hisobot
    python run.py backup             # baza zaxira nusxasi (data/backups/, oxirgi 14 saqlanadi)
    python run.py bot                # botni ishga tushirish (polling yoki webhook)
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.config import DATA_DIR, ensure_dirs, settings
from app.logging_setup import setup_logging

BACKUP_KEEP = 14


def _fix_console() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - eski muhitlar uchun
        pass


async def _with_session(func):
    from app.db.base import dispose_db, init_db, session_scope

    await init_db()
    try:
        async with session_scope() as session:
            return await func(session)
    finally:
        await dispose_db()


async def cmd_seed(force: bool) -> None:
    from app.content.seeder import content_overview, seed_all

    async def _run(session):
        stats = await seed_all(session, force=force)
        overview = await content_overview(session)
        return stats, overview

    stats, overview = await _with_session(_run)
    print("\n=== Kontent bazaga yozildi ===")
    print(f"  Darslar      : {stats['lessons']}")
    print(f"  Takrorlashlar: {stats['reviews']}")
    print(f"  Imtihonlar   : {stats['exams']}")
    print(f"  O'tkazildi   : {stats['skipped']} (avvaldan mavjud)")
    print(f"  Rasmlar      : {stats['images']}")
    print(f"  Kunlik/uy    : {stats['sections']} (kunlik mashg'ulot + uy vazifasi)")
    print("\n=== Baza holati ===")
    for key, value in overview.items():
        print(f"  {key:12s}: {value}")


async def cmd_stats() -> None:
    from app.content.seeder import content_overview

    overview = await _with_session(content_overview)
    print("\n=== Baza holati ===")
    for key, value in overview.items():
        print(f"  {key:12s}: {value}")


async def _probe_token() -> tuple[str, str | None]:
    """Tokenni Telegram orqali jonli tekshiradi (getMe)."""
    from aiogram import Bot
    from aiogram.client.session.aiohttp import AiohttpSession
    from aiogram.exceptions import TelegramUnauthorizedError

    bot = Bot(token=settings.bot_token, session=AiohttpSession(timeout=10))
    try:
        me = await bot.get_me()
        return f"✅ @{me.username} — bot tirik", None
    except TelegramUnauthorizedError:
        return (
            "❌ Telegram rad etdi (Unauthorized)",
            "BOT_TOKEN yaroqsiz — @BotFather → /mybots → botni tanlang → API Token "
            "orqali yangi token olib, .env faylga yozing",
        )
    except Exception as error:  # pragma: no cover - tarmoq
        return f"⚠️  tekshirilmadi ({error})", None
    finally:
        await bot.session.close()


def cmd_check() -> None:
    problems = settings.validate()
    print("\n=== Sozlamalar ===")
    print(f"  BOT_TOKEN        : {'✅ bor' if settings.bot_token else '❌ yo`q'}")
    print(f"  SUPERADMIN_IDS   : {settings.superadmins or '❌ yo`q'}")
    print(f"  DATABASE_URL     : {settings.database_url}")
    print(f"  Rejim            : {'webhook' if settings.use_webhook else 'polling'}")
    print(f"  AI               : {'✅ yoniq' if settings.ai_enabled else '⚪️ o`chiq (OPENAI_API_KEY yo`q)'}")
    print(f"  Redis            : {settings.redis_url or 'in-memory'}")
    if settings.bot_token and ":" in settings.bot_token:
        status, problem = asyncio.run(_probe_token())
        print(f"  Telegram         : {status}")
        if problem:
            problems.append(problem)
    if problems:
        print("\n⚠️  Muammolar:")
        for problem in problems:
            print(f"  - {problem}")
    else:
        print("\n✅ Hammasi joyida.")


def cmd_bot() -> None:
    problems = settings.validate()
    if problems:
        print("\n❌ Botni ishga tushirish uchun .env faylini to'ldiring:")
        for problem in problems:
            print(f"  - {problem}")
        raise SystemExit(1)
    from app.main import main as bot_main

    asyncio.run(bot_main())


# -------------------------------------------------------------------- backup
def _prune_backups(backup_dir, keep: int = BACKUP_KEEP) -> None:
    files = sorted(
        backup_dir.glob("bot_*"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    for old in files[keep:]:
        old.unlink()


def cmd_backup() -> None:
    import shutil
    import sqlite3
    import subprocess
    from pathlib import Path

    from sqlalchemy.engine import make_url

    from app.utils import local_now

    backup_dir = DATA_DIR / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = local_now().strftime("%Y%m%d_%H%M%S")
    url = make_url(settings.database_url)

    if settings.is_sqlite:
        db_path = Path(url.database or "./data/bot.db")
        if not db_path.exists():
            print(f"❌ Baza fayli topilmadi: {db_path}")
            raise SystemExit(1)
        # WAL jurnalini asosiy faylga singdiramiz — aks holda nusxa to'liq bo'lmaydi
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        dest = backup_dir / f"bot_{stamp}.db"
        shutil.copy2(db_path, dest)
        _prune_backups(backup_dir)
        print(f"✅ Zaxira yaratildi: {dest} ({dest.stat().st_size // 1024} KB)")
        print("   Tiklash: faylni data/bot.db ustiga ko'chirib, botni qayta ishga tushiring.")
        return

    pg_dump = shutil.which("pg_dump")
    dest = backup_dir / f"bot_{stamp}.dump"
    if pg_dump is None:
        print("⚠️  pg_dump topilmadi — qo'lda bajaring:")
        print(f"    pg_dump -Fc {url.render_as_string(hide_password=True)} -f {dest}")
        raise SystemExit(1)
    import os

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password
    result = subprocess.run(
        [
            pg_dump,
            "-h", url.host or "localhost",
            "-p", str(url.port or 5432),
            "-U", url.username or "",
            "-F", "c",
            "-f", str(dest),
            url.database or "",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ pg_dump xatosi:\n{result.stderr.strip()}")
        raise SystemExit(1)
    _prune_backups(backup_dir)
    print(f"✅ Zaxira yaratildi: {dest}")
    print(f"   Tiklash: pg_restore -d {url.database or '<baza>'} --clean {dest}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run.py", description="English kurs bot boshqaruvi")
    sub = parser.add_subparsers(dest="command")

    seed = sub.add_parser("seed", help="kontentni bazaga yozish")
    seed.add_argument(
        "--force",
        action="store_true",
        help="noldan qayta yozish (admin tahriri va o'quvchi natijalari o'chadi)",
    )

    sub.add_parser("stats", help="baza hisoboti")
    sub.add_parser("check", help="sozlamalarni tekshirish")
    sub.add_parser("backup", help="baza zaxira nusxasi (data/backups/)")
    sub.add_parser("bot", help="botni ishga tushirish")
    return parser


def main() -> None:
    _fix_console()
    ensure_dirs()
    setup_logging()

    parser = build_parser()
    args = parser.parse_args()
    command = args.command or "bot"

    if command == "seed":
        asyncio.run(cmd_seed(getattr(args, "force", False)))
    elif command == "stats":
        asyncio.run(cmd_stats())
    elif command == "check":
        cmd_check()
    elif command == "backup":
        cmd_backup()
    else:
        cmd_bot()


if __name__ == "__main__":
    main()
