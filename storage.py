import json
import os
import asyncio

from config import USERS_FILE

_lock = asyncio.Lock()


def _load() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict) -> None:
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def get_all_users() -> dict:
    async with _lock:
        return _load()


async def get_user(chat_id: int):
    async with _lock:
        return _load().get(str(chat_id))


async def upsert_user(chat_id: int, **fields) -> None:
    async with _lock:
        data = _load()
        user = data.get(str(chat_id), {})
        user.update(fields)
        data[str(chat_id)] = user
        _save(data)


async def remove_user(chat_id: int) -> None:
    async with _lock:
        data = _load()
        data.pop(str(chat_id), None)
        _save(data)
