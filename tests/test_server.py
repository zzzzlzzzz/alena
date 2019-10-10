from pytest import fixture

from alena import server
from alena.server import TCPHandler, Command, Status, task_database, task_queue, TaskType


@fixture()
def test_func():
    class FuncMock:
        def __init__(self):
            self.called = False
            self.args = None
            self.kwargs = None
            self.rv = None

        def __call__(self, *args, **kwargs):
            self.called = True
            self.args = args
            self.kwargs = kwargs
            return self.rv

    yield FuncMock()


class MessageMock:
    def __init__(self, command=None, message=None, status=None, task_id=None):
        self.command = command
        self.message = message
        self.status = status
        self.task_id = task_id


def nop(_):
    pass


def test_handle_post_task(monkeypatch):
    class MessageMock2(MessageMock):
        def send(self, s):
            assert self.task_id in task_database['task']
            assert self.task_id == task_queue.get()
            task = task_database['task'][self.task_id]
            assert task['command'] == TaskType.REVERSE
            assert task['status'] == Status.QUEUE
            assert task['message'] == 'rev'

    monkeypatch.setattr(server, 'Message', MessageMock2)
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    TCPHandler(None, None, None)._handle_post_task(TaskType.REVERSE, 'rev')
    task_database['task'].clear()


def test_handle_get_task_status(monkeypatch):
    class MessageMock2(MessageMock):
        def send(self, s):
            assert self.command == Command.SC_GET_TASK_STATUS
            assert self.status == Status.PROGRESS

    monkeypatch.setattr(server, 'Message', MessageMock2)
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    task_database['task'][1] = dict(status=Status.PROGRESS)
    TCPHandler(None, None, None)._handle_get_task_status(1)
    task_database['task'].clear()


def test_handle_get_task_status_not_found(monkeypatch):
    class MessageMock2(MessageMock):
        def send(self, s):
            assert self.command == Command.SC_GET_TASK_STATUS
            assert self.status == Status.NOT_FOUND

    monkeypatch.setattr(server, 'Message', MessageMock2)
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    TCPHandler(None, None, None)._handle_get_task_status(1)


def test_handle_get_task_result(monkeypatch):
    class MessageMock2(MessageMock):
        def send(self, s):
            assert self.command == Command.SC_GET_TASK_RESULT
            assert self.status == Status.COMPLETED
            assert self.message == 'ans'

    monkeypatch.setattr(server, 'Message', MessageMock2)
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    task_database['task'][1] = dict(status=Status.COMPLETED, message='ans')
    TCPHandler(None, None, None)._handle_get_task_result(1)
    task_database['task'].clear()


def test_handle_get_task_result_not_completed(monkeypatch):
    class MessageMock2(MessageMock):
        def send(self, s):
            assert self.command == Command.SC_GET_TASK_RESULT
            assert self.status == Status.NOT_FOUND
            assert self.message == ''

    monkeypatch.setattr(server, 'Message', MessageMock2)
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    task_database['task'][1] = dict(status=Status.PROGRESS, message='ans')
    message = MessageMock(command=Command.CS_GET_TASK_RESULT, task_id=1)
    TCPHandler(None, None, None)._handle_get_task_result(message)
    task_database['task'].clear()


def test_handle_get_task_result_not_found(monkeypatch):
    class MessageMock2(MessageMock):
        def send(self, s):
            assert self.command == Command.SC_GET_TASK_RESULT
            assert self.status == Status.NOT_FOUND
            assert self.message == ''

    monkeypatch.setattr(server, 'Message', MessageMock2)
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    TCPHandler(None, None, None)._handle_get_task_result(1)


def test_handle_message_post(monkeypatch, test_func):
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    monkeypatch.setattr(TCPHandler, '_handle_post_task', test_func)
    message = MessageMock(command=Command.CS_POST_TASK_REVERSE, message='Test')
    TCPHandler(None, None, None)._handle_message(message)
    assert test_func.called
    assert test_func.args == (TaskType.REVERSE, 'Test')
    test_func.called = False
    message = MessageMock(command=Command.CS_POST_TASK_TRANSPOSITION, message='Test')
    TCPHandler(None, None, None)._handle_message(message)
    assert test_func.called
    assert test_func.args == (TaskType.TRANSPOSITION, 'Test')


def test_handle_message_status(monkeypatch, test_func):
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    monkeypatch.setattr(TCPHandler, '_handle_get_task_status', test_func)
    message = MessageMock(command=Command.CS_GET_TASK_STATUS, task_id=1)
    TCPHandler(None, None, None)._handle_message(message)
    assert test_func.called
    assert test_func.args == (1, )


def test_handle_message_result(monkeypatch, test_func):
    monkeypatch.setattr(TCPHandler, 'handle', nop)
    monkeypatch.setattr(TCPHandler, '_handle_get_task_result', test_func)
    message = MessageMock(command=Command.CS_GET_TASK_RESULT, task_id=1)
    TCPHandler(None, None, None)._handle_message(message)
    assert test_func.called
    assert test_func.args == (1, )
