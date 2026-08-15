import asyncio
import logging
from datetime import datetime

import pytz
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, DEFAULT_CITY, DEFAULT_TIME, TIMEZONE
from digest import build_digest
import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart_alarm_bot")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

HELP_TEXT = (
    "🤖 Я «Интеллектуальный будильник».\n\n"
    "Каждое утро присылаю сводку: погода, курс валют, "
    "исторический факт дня и праздники.\n\n"
    "Команды:\n"
    "/start — подписаться на утреннюю рассылку\n"
    "/city <город> — установить город для погоды (сейчас: {city})\n"
    "/time <ЧЧ:ММ> — установить время рассылки (сейчас: {time})\n"
    "/now — прислать сводку прямо сейчас\n"
    "/stop — отписаться от рассылки"
)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await storage.upsert_user(
        message.chat.id, city=DEFAULT_CITY, time=DEFAULT_TIME, active=True
    )
    await message.answer(
        "Привет! Ты подписался на утреннюю сводку 🎉\n\n"
        + HELP_TEXT.format(city=DEFAULT_CITY, time=DEFAULT_TIME)
    )


@dp.message(Command("city"))
async def cmd_city(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажи город, например: /city Санкт-Петербург")
        return
    city = parts[1].strip()
    await storage.upsert_user(message.chat.id, city=city)
    await message.answer(f"Готово! Город для погоды: {city}")


@dp.message(Command("time"))
async def cmd_time(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Укажи время в формате ЧЧ:ММ, например: /time 07:30")
        return
    time_str = parts[1].strip()
    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await message.answer("Неверный формат. Пример: /time 07:30")
        return
    await storage.upsert_user(message.chat.id, time=time_str)
    await message.answer(f"Готово! Буду присылать сводку в {time_str}")


@dp.message(Command("now"))
async def cmd_now(message: Message):
    user = await storage.get_user(message.chat.id)
    city = (user or {}).get("city", DEFAULT_CITY)
    await message.answer("Собираю сводку… ⏳")
    text = await build_digest(city)
    await message.answer(text)


@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    await storage.upsert_user(message.chat.id, active=False)
    await message.answer("Ты отписан от рассылки. Вернуться можно командой /start")


@dp.message(Command("help"))
async def cmd_help(message: Message):
    user = await storage.get_user(message.chat.id) or {}
    await message.answer(
        HELP_TEXT.format(
            city=user.get("city", DEFAULT_CITY),
            time=user.get("time", DEFAULT_TIME),
        )
    )


async def check_and_send():
    """Запускается каждую минуту: сверяет время у каждого пользователя."""
    tz = pytz.timezone(TIMEZONE)
    now_str = datetime.now(tz).strftime("%H:%M")

    users = await storage.get_all_users()
    for chat_id, user in users.items():
        if not user.get("active", True):
            continue
        if user.get("time", DEFAULT_TIME) != now_str:
            continue
        try:
            text = await build_digest(user.get("city", DEFAULT_CITY))
            await bot.send_message(int(chat_id), text)
        except Exception as e:
            logger.warning("Не удалось отправить сообщение %s: %s", chat_id, e)


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в .env")

    scheduler.add_job(check_and_send, "cron", second=0)  # проверка каждую минуту
    scheduler.start()
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
