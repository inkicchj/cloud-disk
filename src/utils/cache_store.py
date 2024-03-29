from typing import Optional, Any

from caches import Cache


class MemCache:
    cache: Optional[Cache] = None

    @classmethod
    async def _get_cache(cls):
        if cls.cache and cls.cache.is_connected:
            return cls.cache

        cls.cache = Cache("locmem://null")
        await cls._connect()
        return cls.cache

    @classmethod
    async def _connect(cls):
        if cls.cache and not cls.cache.is_connected:
            await cls.cache.connect()

    @classmethod
    async def initialize(cls):
        await cls._get_cache()

    @classmethod
    async def release(cls):
        if cls.cache:
            await cls.cache.clear()
            await cls.cache.disconnect()
        cls.cache = None

    @classmethod
    async def set_data(cls, k: str, v: Any, ttl: Optional[int] = None):
        cache: Cache = await cls._get_cache()
        await cache.set(key=k, value=v, ttl=ttl)

    @classmethod
    async def get_data(cls, k: str):
        cache: Cache = await cls._get_cache()
        result = await cache.get(key=k)
        return result

    @classmethod
    async def del_data(cls, k: str):
        cache: Cache = await cls._get_cache()
        await cache.delete(key=k)
