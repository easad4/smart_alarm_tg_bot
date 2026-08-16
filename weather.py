from datetime import datetime, timedelta, timezone

import aiohttp

from config import OWM_API_KEY

# Бесплатный эндпоинт прогноза с шагом 3 часа на 5 дней вперёд.
# Не требует платной подписки/привязки карты (в отличие от One Call API 3.0).
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

WEATHER_EMOJI = {
    "Clear": "☀️",
    "Clouds": "☁️",
    "Rain": "🌧️",
    "Drizzle": "🌦️",
    "Thunderstorm": "⛈️",
    "Snow": "❄️",
    "Mist": "🌫️",
    "Fog": "🌫️",
    "Haze": "🌫️",
}

# Целевые часы (по местному времени города), для которых показываем
# отдельные точки прогноза. Реальные тайм-слоты в ответе API идут
# с шагом 3 часа (00, 03, 06, 09, 12, 15, 18, 21) — для каждого
# целевого часа берём ближайший доступный слот.
TIME_SLOTS = [
    ("🌅 Утро", 9),
    ("🌞 День", 15),
    ("🌆 Вечер", 21),
]
NIGHT_LABEL = "🌙 Ночь"
# Насколько далеко (в часах) от полуночи разрешаем искать слот для "ночи".
# Ночь технически приходится на начало следующих суток (00:00–03:00),
# поэтому ищем не только среди сегодняшних точек.
NIGHT_SEARCH_WINDOW_HOURS = 9


async def get_weather(city: str) -> str:
    """Возвращает прогноз погоды на сегодня: диапазон температур
    и отдельные точки на утро/день/вечер.
    """
    if not OWM_API_KEY:
        return "⚠️ Не задан ключ OpenWeatherMap (OWM_API_KEY в .env)."

    params = {
        "q": city,
        "appid": OWM_API_KEY,
        "units": "metric",
        "lang": "ru",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FORECAST_URL, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return f"⚠️ Не удалось получить прогноз погоды для «{city}»."
                data = await resp.json()
    except Exception:
        return "⚠️ Сервис погоды временно недоступен."

    items = data.get("list", [])
    if not items:
        return f"⚠️ Нет данных о погоде для «{city}»."

    # Смещение локального времени города от UTC, в секундах
    tz_offset = data.get("city", {}).get("timezone", 0)

    def local_dt(item: dict) -> datetime:
        # Возвращаем "наивный" datetime (без tzinfo): смещение уже учтено
        # вручную через tz_offset, а naive-объекты проще сравнивать
        # и вычитать друг из друга ниже (для поиска ночного слота).
        return (
            datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            + timedelta(seconds=tz_offset)
        ).replace(tzinfo=None)

    now_utc = datetime.now(timezone.utc)
    today_local = (now_utc + timedelta(seconds=tz_offset)).date()
    today_items = [it for it in items if local_dt(it).date() == today_local]

    label_date = today_local
    is_today = True
    if not today_items:
        # Если прогноза на оставшуюся часть сегодняшнего дня уже нет
        # (например, бот запущен поздним вечером) — берём ближайший
        # доступный день и явно указываем его дату в сообщении.
        label_date = local_dt(items[0]).date()
        today_items = [it for it in items if local_dt(it).date() == label_date]
        is_today = False

    temps = [it["main"]["temp"] for it in today_items]
    temp_min, temp_max = min(temps), max(temps)

    title = "на сегодня" if is_today else f"на {label_date.strftime('%d.%m')}"
    lines = [
        f"🌤️ Прогноз погоды в городе {city} {title}:",
        f"Диапазон: от {temp_min:.0f}°C до {temp_max:.0f}°C",
        "",
    ]

    for label, target_hour in TIME_SLOTS:
        closest = min(today_items, key=lambda it: abs(local_dt(it).hour - target_hour))
        weather = closest["weather"][0]
        emoji = WEATHER_EMOJI.get(weather["main"], "🌡️")
        temp = closest["main"]["temp"]
        time_str = local_dt(closest).strftime("%H:%M")
        lines.append(
            f"{label} ({time_str}): {emoji} {temp:.0f}°C, {weather['description']}"
        )

    # "Ночь" технически приходится на начало следующих суток (00:00–03:00),
    # поэтому ищем ближайший слот к полуночи среди ВСЕХ точек прогноза,
    # а не только среди сегодняшних.
    midnight_next = datetime.combine(label_date, datetime.min.time()) + timedelta(
        days=1
    )
    night_candidates = [
        it
        for it in items
        if abs((local_dt(it) - midnight_next).total_seconds())
        <= NIGHT_SEARCH_WINDOW_HOURS * 3600
    ]
    if night_candidates:
        closest = min(
            night_candidates,
            key=lambda it: abs((local_dt(it) - midnight_next).total_seconds()),
        )
        weather = closest["weather"][0]
        emoji = WEATHER_EMOJI.get(weather["main"], "🌡️")
        temp = closest["main"]["temp"]
        time_str = local_dt(closest).strftime("%H:%M")
        lines.append(
            f"{NIGHT_LABEL} ({time_str}): {emoji} {temp:.0f}°C, {weather['description']}"
        )

    return "\n".join(lines)
