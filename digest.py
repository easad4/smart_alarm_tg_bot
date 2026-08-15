from datetime import date

from weather import get_weather
from currency import get_currency
from history import get_history_fact
from holidays import get_holidays

WEEKDAYS_RU = [
    "понедельник", "вторник", "среда", "четверг",
    "пятница", "суббота", "воскресенье",
]
MONTHS_RU = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]


async def build_digest(city: str) -> str:
    today = date.today()
    header = (
        f"☀️ Доброе утро! Сегодня {today.day} {MONTHS_RU[today.month]}, "
        f"{WEEKDAYS_RU[today.weekday()]}\n"
        "————————————————————\n"
    )

    weather_part = await get_weather(city)
    currency_part = await get_currency()
    history_part = await get_history_fact(today)
    holidays_part = await get_holidays(today)

    return "\n\n".join(
        [header + weather_part, currency_part, history_part, holidays_part]
    )
