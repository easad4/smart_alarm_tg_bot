import aiohttp

CBR_URL = "https://www.cbr-xml-daily.ru/daily_json.js"


async def get_currency() -> str:
    """Возвращает курсы USD и EUR по данным ЦБ РФ."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(CBR_URL, timeout=10) as resp:
                if resp.status != 200:
                    return "⚠️ Не удалось получить курсы валют."
                data = await resp.json(content_type=None)
    except Exception:
        return "⚠️ Сервис курсов валют временно недоступен."

    valute = data.get("Valute", {})
    usd = valute.get("USD", {})
    eur = valute.get("EUR", {})

    def fmt(v: dict) -> str:
        value = v.get("Value")
        prev = v.get("Previous")
        if value is None or prev is None:
            return "н/д"
        diff = value - prev
        arrow = "▲" if diff > 0 else ("▼" if diff < 0 else "→")
        return f"{value:.2f} ₽ ({arrow}{abs(diff):.2f})"

    return (
        "💱 Курс валют (ЦБ РФ):\n"
        f"USD: {fmt(usd)}\n"
        f"EUR: {fmt(eur)}"
    )
