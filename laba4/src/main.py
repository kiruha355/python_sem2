import asyncio
import logging

from laba1.src.sources import GeneratorSource
from laba2.src.task import Task
from laba4.src.executor import AsyncExecutor
from laba4.src.handlers import LogHandler, PrintHandler
from laba4.src.queue import AsyncTaskQueue


async def fill_queue(queue: AsyncTaskQueue) -> None:
    for task in GeneratorSource(3).get_tasks():
        await queue.add(
            Task(description=str(task.payload), priority=5, payload=task.payload)
        )

    await queue.add(
        Task(description="обработать задачу", priority=1, payload=None)
    )
    await queue.add(
        Task(description="обработать задачу", priority=3, payload=None)
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

    queue = AsyncTaskQueue()
    await fill_queue(queue)

    async with AsyncExecutor(queue, PrintHandler(), LogHandler()) as executor:
        await executor.run()


if __name__ == "__main__":
    asyncio.run(main())
