import asyncio

async def with_asyncio_thread_async(func):
  return await asyncio.to_thread(func)