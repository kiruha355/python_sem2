import logging

import pytest

from laba2.src.task import Task
from laba4.src.executor import AsyncExecutor, HIGH_PRIORITY
from laba4.src.handlers import LogHandler, PrintHandler
from laba4.src.protocol import TaskHandler
from laba4.src.queue import AsyncTaskQueue


def make_task(description: str = "test", priority: int = 5, status: str = "pending") -> Task:
    task = Task(description=description, priority=priority, payload=None)
    task.status = status
    return task


def make_executor(queue: AsyncTaskQueue, **kwargs) -> AsyncExecutor:
    return AsyncExecutor(queue, PrintHandler(), LogHandler(), **kwargs)


class TestAsyncTaskQueue:
    async def test_empty_queue(self) -> None:
        queue = AsyncTaskQueue()
        assert queue.empty()

    async def test_add_and_get(self) -> None:
        queue = AsyncTaskQueue()
        task = make_task()

        await queue.add(task)

        assert not queue.empty()
        assert await queue.get() is task
        queue.task_done()
        assert queue.empty()

    async def test_multiple_tasks_order(self) -> None:
        queue = AsyncTaskQueue()
        task1 = make_task(description="first")
        task2 = make_task(description="second")

        await queue.add(task1)
        await queue.add(task2)

        assert await queue.get() is task1
        queue.task_done()
        assert await queue.get() is task2
        queue.task_done()

    async def test_join_after_task_done(self) -> None:
        queue = AsyncTaskQueue()
        await queue.add(make_task())

        await queue.get()
        queue.task_done()
        await queue.join()

        assert queue.empty()


class TestTaskHandlerProtocol:
    def test_print_handler_matches_protocol(self) -> None:
        assert isinstance(PrintHandler(), TaskHandler)

    def test_log_handler_matches_protocol(self) -> None:
        assert isinstance(LogHandler(), TaskHandler)

    def test_invalid_high_handler_is_rejected(self) -> None:
        queue = AsyncTaskQueue()
        with pytest.raises(TypeError):
            AsyncExecutor(queue, object(), LogHandler()) 

    def test_invalid_low_handler_is_rejected(self) -> None:
        queue = AsyncTaskQueue()
        with pytest.raises(TypeError):
            AsyncExecutor(queue, PrintHandler(), object())  


class TestAsyncExecutor:
    def test_accepts_valid_handlers(self) -> None:
        queue = AsyncTaskQueue()
        executor = make_executor(queue)
        assert executor is not None

    async def test_context_manager_enters_and_exits(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        queue = AsyncTaskQueue()
        with caplog.at_level(logging.INFO):
            async with make_executor(queue):
                pass

        assert "Исполнитель запущен" in caplog.text
        assert "Исполнитель остановлен" in caplog.text

    async def test_high_priority_routed_to_print_handler(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        queue = AsyncTaskQueue()
        await queue.add(make_task(description="важная", priority=HIGH_PRIORITY))

        async with make_executor(queue) as executor:
            await executor.run()

        assert "важная" in capsys.readouterr().out

    async def test_run_processes_all_tasks(self) -> None:
        queue = AsyncTaskQueue()
        processed: list[Task] = []

        class CollectHandler:
            async def handle(self, task: Task) -> None:
                processed.append(task)

        await queue.add(make_task(description="a", priority=5))
        await queue.add(make_task(description="b", priority=1))
        await queue.add(make_task(description="c", priority=5))

        async with AsyncExecutor(queue, CollectHandler(), CollectHandler()) as executor:
            await executor.run()

        assert len(processed) == 3
        assert queue.empty()

    async def test_run_continues_after_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        queue = AsyncTaskQueue()
        processed: list[Task] = []

        class ErrorHandler:
            async def handle(self, task: Task) -> None:
                if task.description == "bad":
                    raise ValueError("ошибка")
                processed.append(task)

        await queue.add(make_task(description="good", priority=5))
        await queue.add(make_task(description="bad", priority=5))
        await queue.add(make_task(description="good", priority=5))

        with caplog.at_level(logging.ERROR):
            async with AsyncExecutor(queue, ErrorHandler(), ErrorHandler()) as executor:
                await executor.run()

        assert len(processed) == 2
        assert "Ошибка при обработке задачи" in caplog.text
        assert queue.empty()

    async def test_run_empty_queue(self) -> None:
        queue = AsyncTaskQueue()
        async with make_executor(queue) as executor:
            await executor.run()
        assert queue.empty()

    async def test_aexit_returns_false(self) -> None:
        queue = AsyncTaskQueue()
        executor = make_executor(queue)
        result = await executor.__aexit__(None, None, None)
        assert result is False


class TestHandlers:
    async def test_print_handler_runs_without_error(self) -> None:
        await PrintHandler().handle(make_task())

    async def test_log_handler_runs_without_error(self) -> None:
        await LogHandler().handle(make_task())

    async def test_print_handler_prints_description(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        await PrintHandler().handle(make_task(description="тестовая задача"))
        assert "тестовая задача" in capsys.readouterr().out

    async def test_log_handler_prints_status(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        await LogHandler().handle(make_task(status="running"))
        assert "running" in capsys.readouterr().out
