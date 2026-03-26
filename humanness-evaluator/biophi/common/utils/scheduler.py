from typing import Tuple

from abc import ABC, abstractmethod
import uuid

class TaskNotFoundError(Exception):
    pass


class Scheduler(ABC):

    @abstractmethod
    def get_result(self, task_id, index=None, timeout=15):
        pass

    @abstractmethod
    def get_result_task_id(self, task_id, index):
        pass

    @abstractmethod
    def get_results(self, task_id, timeout=15):
        pass

    @abstractmethod
    def get_results_len(self, task_id):
        pass

    @abstractmethod
    def are_results_ready(self, task_id):
        pass

    @abstractmethod
    def get_results_progress(self, task_id) -> Tuple[int, int, int]:
        pass

    @abstractmethod
    def schedule_task(self, fun, *args, **kwargs):
        pass

    @abstractmethod
    def schedule_tasks(self, fun, inputs):
        pass




class SimpleInMemoryScheduler(Scheduler):
    results = {}

    def save_result(self, result):
        task_id = None
        while task_id is None or task_id in self.results:
            task_id = uuid.uuid4().hex
        self.results[task_id] = result
        return task_id

    def get_result(self, task_id, index=None, timeout=15):
        if task_id not in self.results:
            raise TaskNotFoundError(task_id)
        if index is not None:
            assert int(index) > 0, f'Index is 1-indexed, got {index}'
            return self.get_result(self.results[task_id][int(index)-1])
        return self.results[task_id]

    def get_result_task_id(self, task_id, index):
        task_ids = self.get_result(task_id)
        return task_ids[int(index)-1]

    def get_results(self, task_id, timeout=15):
        task_ids = self.get_result(task_id)
        return [self.get_result(i) for i in task_ids]

    def get_results_len(self, task_id):
        return len(self.get_result(task_id))

    def are_results_ready(self, task_id):
        return task_id in self.results

    def get_results_progress(self, task_id) -> Tuple[int, int, int]:
        # This should never be called because tasks are always ready
        raise NotImplementedError()

    def schedule_task(self, fun, *args, **kwargs):
        return self.save_result(fun(*args, **kwargs))

    def schedule_tasks(self, fun, inputs):
        task_ids = []
        for kwargs in inputs:
            task_ids.append(self.save_result(fun(**kwargs)))
        return self.save_result(task_ids)


class NotInitializedScheduler(Scheduler):
    def throw(self):
        raise NotImplementedError('Scheduler not initialized')

    def get_result_task_id(self, task_id, index):
        self.throw()

    def get_results(self, task_id, timeout=15):
        self.throw()

    def are_results_ready(self, task_id):
        self.throw()

    def get_results_progress(self, task_id):
        self.throw()

    def schedule_task(self, fun, *args, **kwargs):
        self.throw()

    def schedule_tasks(self, fun, inputs):
        self.throw()

    def get_result(self, task_id, index=None, timeout=15):
        self.throw()
    
    def get_results_len(self, task_id):
        self.throw()



class SchedulerProxy:
    wrapped = NotInitializedScheduler()

    def __getattr__(self, attr):
        return getattr(self.wrapped, attr)


scheduler: Scheduler = SchedulerProxy()


def use_scheduler(name):
    global scheduler
    if name == 'simple':
        scheduler.wrapped = SimpleInMemoryScheduler()
    else:
        raise ValueError(f"Unsupported scheduler: {name}")