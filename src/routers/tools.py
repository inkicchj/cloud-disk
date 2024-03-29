from src.utils.cache_store import MemCache


async def cancel_task(session_id):
    record_task = await MemCache.get_data(f"upload_{session_id}")
    if record_task is not None:
        await MemCache.del_data(f"upload_{session_id}")