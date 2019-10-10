import logging
from argparse import ArgumentParser
from socketserver import TCPServer, BaseRequestHandler
from contextlib import suppress
from queue import Queue
from threading import Thread

from .proto import Command, Status, Message
from .workers import TaskType, worker_table


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
task_database = dict(last_task_index=0, task=dict())    # Best choice - use real database (e.g. PostgreSQL)
task_queue = Queue()                                    # Best choice - use real message broker (e.g. RabbitMQ)


def worker() -> None:
    """Worker thread"""
    while True:
        task_id = task_queue.get()
        task = task_database['task'][task_id]
        task['status'] = Status.PROGRESS
        logging.info('WORKER/PROCESS/{}'.format(task_id))
        task['message'] = worker_table[task['command']](task['message'])
        task['status'] = Status.COMPLETED
        logging.info('WORKER/COMPLETED/{}'.format(task_id))


class TCPHandler(BaseRequestHandler):
    TIMEOUT = 3

    def _handle_post_task(self, task_type: 'TaskType', data: str) -> None:
        logging.info('POST_TASK/{}/{}'.format(task_type.name, data))
        task_id = task_database['last_task_index']
        task_database['task'][task_id] = dict(command=task_type, status=Status.QUEUE, message=data)
        task_database['last_task_index'] += 1
        task_queue.put_nowait(task_id)
        Message(command=Command.SC_POST_TASK, task_id=task_id).send(self.request)

    def _handle_get_task_status(self, task_id: int) -> None:
        logging.info('GET_STATUS/{}'.format(task_id))
        try:
            task = task_database['task'][task_id]
            Message(command=Command.SC_GET_TASK_STATUS, status=task['status']).send(self.request)
        except KeyError:
            Message(command=Command.SC_GET_TASK_STATUS, status=Status.NOT_FOUND).send(self.request)

    def _handle_get_task_result(self, task_id: int) -> None:
        logging.info('GET_RESULT/{}'.format(task_id))
        try:
            task = task_database['task'][task_id]
            if task['status'] != Status.COMPLETED:
                raise ValueError()
            Message(command=Command.SC_GET_TASK_RESULT, status=task['status'], message=task['message']).send(self.request)
        except (KeyError, ValueError):
            Message(command=Command.SC_GET_TASK_RESULT, status=Status.NOT_FOUND, message='').send(self.request)

    def _handle_message(self, message: 'Message') -> None:
        if message.command == Command.CS_POST_TASK_REVERSE:
            self._handle_post_task(TaskType.REVERSE, message.message)
        elif message.command == Command.CS_POST_TASK_TRANSPOSITION:
            self._handle_post_task(TaskType.TRANSPOSITION, message.message)
        elif message.command == Command.CS_GET_TASK_STATUS:
            self._handle_get_task_status(message.task_id)
        elif message.command == Command.CS_GET_TASK_RESULT:
            self._handle_get_task_result(message.task_id)

    def handle(self) -> None:
        self.request.settimeout(self.TIMEOUT)
        with suppress(ValueError, OSError):
            self._handle_message(Message.recv(self.request))


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument('bind_addr', help='Bind IP address (127.0.0.1 for local; 0.0.0.0 for public)',
                        metavar='BIND_ADDR')
    parser.add_argument('bind_port', type=int, help='Bind port', metavar='BIND_PORT')
    args = parser.parse_args()

    worker_thread = Thread(target=worker)
    worker_thread.daemon = True
    worker_thread.start()

    with TCPServer((args.bind_addr, args.bind_port), TCPHandler) as server:
        try:
            server.serve_forever()
        finally:
            server.server_close()


if __name__ == '__main__':
    main()
