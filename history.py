import logging
import random
from datetime import date

import aiohttp

logger = logging.getLogger(__name__)

URL_TEMPLATE = "https://ru.wikipedia.org/api/rest_v1/feed/onthisday/events/{mm}/{dd}"

# ВАЖНО: у Wikimedia жёсткая политика User-Agent — запрос без него
# или с общим/пустым значением (например, просто "SmartAlarmBot/1.0")
# отклоняется с ошибкой 403. Нужно указать имя приложения и контакт
# (сайт, email или ссылку на репозиторий). Замените на свои данные.
# Подробнее: https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
HEADERS = {
    "User-Agent": (
        "SmartAlarmBot/1.0 "
        "(https://github.com/yourname/smart-alarm-bot; contact@example.com)"
    )
}


async def get_history_fact(day: date = None) -> str:
    """Возвращает случайный исторический факт этого дня по данным Wikipedia."""
    day = day or date.today()
    url = URL_TEMPLATE.format(mm=f"{day.month:02d}", dd=f"{day.day:02d}")

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    logger.warning(
                        "Wikipedia onthisday вернул статус %s для %s",
                        resp.status, url,
                    )
                    return "⚠️ Не удалось получить исторический факт (Wikipedia)."
                # content_type=None — на случай если сервер вернёт
                # некорректный/нестандартный Content-Type для JSON
                data = await resp.json(content_type=None)
    except Exception as e:
        logger.warning("Ошибка запроса к Wikipedia: %s", e)
        return "⚠️ Сервис исторических фактов временно недоступен."

    events = data.get("events", [])
    if not events:
        return "Сегодня без особых исторических находок 🤷"

    event = random.choice(events)
    year = event.get("year", "?")
    text = event.get("text", "")
    return f"📜 Этот день в истории ({year}):\n{text}"
