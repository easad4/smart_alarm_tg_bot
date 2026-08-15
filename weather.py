import aiohttp

from config import OWM_API_KEY

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

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


async def get_weather(city: str) -> str:
    """Возвращает готовую строку с погодой для города."""
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
            async with session.get(WEATHER_URL, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return f"⚠️ Не удалось получить погоду для «{city}»."
                data = await resp.json()
    except Exception:
        return "⚠️ Сервис погоды временно недоступен."

    main = data["main"]
    weather = data["weather"][0]
    wind = data.get("wind", {})
    emoji = WEATHER_EMOJI.get(weather["main"], "🌡️")

    return (
        f"{emoji} Погода в городе {city}:\n"
        f"Сейчас {main['temp']:.0f}°C, ощущается как {main['feels_like']:.0f}°C\n"
        f"{weather['description'].capitalize()}\n"
        f"Влажность: {main['humidity']}%, ветер: {wind.get('speed', 0):.0f} м/с"
    )
