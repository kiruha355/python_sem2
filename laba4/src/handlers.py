import asyncio
from laba2.src.task import Task


class PrintHandler:
    """Для печати описания задачи"""

    async def handle(self, task: Task) -> None:
        await asyncio.sleep(0.1)  
        print(f"обработана: [{task.id}] {task.description} приоритет={task.priority}")


class LogHandler:
    """Для логирования id задачи"""

    async def handle(self, task: Task) -> None:
        await asyncio.sleep(0.05) 
        print(f"log: id={task.id} status={task.status} priority={task.priority}")