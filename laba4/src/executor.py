import asyncio
import logging
from types import TracebackType
from typing import Self

from laba2.src.task import Task
from laba4.src.protocol import TaskHandler
from laba4.src.queue import AsyncTaskQueue

HIGH_PRIORITY = 5


class AsyncExecutor:
    """Асинхронный исполнитель задач"""

    def __init__(
        self,
        queue: AsyncTaskQueue,
        high_priority_handler: TaskHandler,
        low_priority_handler: TaskHandler,
        logger: logging.Logger | None = None,
    ) -> None:
        for handler in (high_priority_handler, low_priority_handler):
            if not isinstance(handler, TaskHandler):
                raise TypeError(
                    f"{handler.__class__.__name__} "
                    "не реализует контракт TaskHandler"
                )
        self._queue = queue
        self._high = high_priority_handler
        self._low = low_priority_handler
        self._logger = logger or logging.getLogger(__name__)

    async def __aenter__(self) -> Self:
        self._logger.info("Исполнитель запущен")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        if exc_val is not None:
            self._logger.exception(
                "Исполнитель завершился с ошибкой",
                exc_info=(exc_type, exc_val, exc_tb),
            )
        self._logger.info("Исполнитель остановлен")
        return False

    async def _process(self, task: Task) -> None:           #создание корутины 
        handler = self._high if task.priority >= HIGH_PRIORITY else self._low
        try:
            await handler.handle(task)
        except Exception:
            self._logger.exception("Ошибка при обработке задачи %s", task.id)
        finally:
            self._queue.task_done()

    async def run(self) -> None:
        coroutines = []
        while not self._queue.empty():
            task = await self._queue.get()
            coroutines.append(self._process(task))
        await asyncio.gather(*coroutines)
