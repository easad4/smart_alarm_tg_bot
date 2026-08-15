import logging
from datetime import date
from xml.etree import ElementTree

import aiohttp

logger = logging.getLogger(__name__)

RSS_URL = "https://www.calend.ru/rss/today-holidays.rss"

# Родительный падеж месяцев — так они пишутся в заголовках RSS calend.ru,
# например: "15 августа 2026 - День археолога"
MONTHS_GEN_RU = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


async def get_holidays(day: date = None, limit: int = 10) -> str:
    """Возвращает список праздников на сегодня по RSS-ленте calend.ru.

    Лента https://www.calend.ru/rss/today-holidays.rss содержит праздники
    "сегодня и завтра" в формате "{день} {месяц} {год} - {название}".
    Отбираем только записи, у которых дата совпадает с запрошенным днём.
    """
    day = day or date.today()
    prefix = f"{day.day} {MONTHS_GEN_RU[day.month]} {day.year} - "

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(RSS_URL, timeout=15) as resp:
                if resp.status != 200:
                    logger.warning("calend.ru RSS вернул статус %s", resp.status)
                    return "⚠️ Не удалось получить праздники с calend.ru."
                raw = await resp.text()
    except Exception as e:
        logger.warning("Ошибка запроса к calend.ru: %s", e)
        return "⚠️ Сервис праздников (calend.ru) временно недоступен."

    try:
        root = ElementTree.fromstring(raw)
    except ElementTree.ParseError as e:
        logger.warning("Не удалось разобрать RSS calend.ru: %s", e)
        return "⚠️ Не удалось разобрать ответ calend.ru."

    names = []
    for item in root.iter("item"):
        title_el = item.find("title")
        if title_el is None or not title_el.text:
            continue
        title = title_el.text.strip()
        if title.startswith(prefix):
            names.append(title[len(prefix):].strip())

    if not names:
        return "🎉 Сегодня без особых праздников — обычный отличный день!"

    names = names[:limit]
    return "🎉 Праздники сегодня (calend.ru):\n" + "\n".join(f"• {n}" for n in names)
