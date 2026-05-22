import asyncio

from laba2.src.task import Task


class AsyncTaskQueue:
    """Асинхронная очередь задач."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Task] = asyncio.Queue()

    async def add(self, task: Task) -> None:
        await self._queue.put(task)

    async def get(self) -> Task:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    async def join(self) -> None:
        await self._queue.join()

    def empty(self) -> bool:
        return self._queue.empty()
