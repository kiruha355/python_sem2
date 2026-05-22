from typing import Protocol, runtime_checkable
from laba2.src.task import Task


@runtime_checkable
class TaskHandler(Protocol):
    """Контракт обработчика задач"""

    async def handle(self, task: Task) -> None:
        """Обработка задачи"""
        ...