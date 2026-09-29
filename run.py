"""Loyiha boshqaruv CLI.

Foydalanish:
    python run.py check              # sozlamalarni tekshirish
    python run.py seed               # kontentni bazaga yozish (mavjudlariga tegmaydi)
    python run.py seed --force       # kontentni noldan qayta yozish (admin tahriri o'chadi)
    python run.py stats              # baza bo'yicha qisqa hisobot
    python run.py bot                # botni ishga tushirish (polling yoki webhook)
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.config import ensure_dirs, settings
from app.logging_setup import setup_logging


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
    print("\n=== Baza holati ===")
    for key, value in overview.items():
        print(f"  {key:12s}: {value}")


async def cmd_stats() -> None:
    from app.content.seeder import content_overview

    overview = await _with_session(content_overview)
    print("\n=== Baza holati ===")
    for key, value in overview.items():
        print(f"  {key:12s}: {value}")


def cmd_check() -> None:
    problems = settings.validate()
    print("\n=== Sozlamalar ===")
    print(f"  BOT_TOKEN        : {'✅ bor' if settings.bot_token else '❌ yo`q'}")
    print(f"  SUPERADMIN_IDS   : {settings.superadmins or '❌ yo`q'}")
    print(f"  DATABASE_URL     : {settings.database_url}")
    print(f"  Rejim            : {'webhook' if settings.use_webhook else 'polling'}")
    print(f"  AI               : {'✅ yoniq' if settings.ai_enabled else '⚪️ o`chiq (OPENAI_API_KEY yo`q)'}")
    print(f"  Redis            : {settings.redis_url or 'in-memory'}")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run.py", description="English kurs bot boshqaruvi")
    sub = parser.add_subparsers(dest="command")

    seed = sub.add_parser("seed", help="kontentni bazaga yozish")
    seed.add_argument("--force", action="store_true", help="noldan qayta yozish")

    sub.add_parser("stats", help="baza hisoboti")
    sub.add_parser("check", help="sozlamalarni tekshirish")
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
    else:
        cmd_bot()


if __name__ == "__main__":
    main()
