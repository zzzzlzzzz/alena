import logging
from argparse import ArgumentParser, Namespace
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep
from contextlib import closing

from .proto import Message, Command, Status


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
TIMEOUT = 3


def connect(args: 'Namespace') -> 'socket':
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(TIMEOUT)
    s.connect((args.address, args.port))
    return s


def send_task(args: 'Namespace', s: 'socket') -> None:
    if args.reverse:
        Message(command=Command.CS_POST_TASK_REVERSE, message=args.message).send(s)
    elif args.transposition:
        Message(command=Command.CS_POST_TASK_TRANSPOSITION, message=args.message).send(s)


def post_task_simple(args: 'Namespace') -> None:
    with closing(connect(args)) as s:
        send_task(args, s)
        task_id = Message.recv(s).task_id
    logging.info('Monitoring task with task_id {}'.format(task_id))
    while True:
        with closing(connect(args)) as s:
            Message(command=Command.CS_GET_TASK_STATUS, task_id=task_id).send(s)
            status = Message.recv(s).status
        if status == Status.NOT_FOUND:
            logging.info('Task with task_id {} not found'.format(task_id))
            return
        elif status == Status.QUEUE:
            logging.info('Task with task_id {} now in queue'.format(task_id))
        elif status == Status.PROGRESS:
            logging.info('Task with task_id {} now in progress'.format(task_id))
        elif status == Status.COMPLETED:
            logging.info('Task with task_id {} completed'.format(task_id))
            with closing(connect(args)) as s:
                Message(command=Command.CS_GET_TASK_RESULT, task_id=task_id).send(s)
                result = Message.recv(s)
            if result.status == Status.NOT_FOUND:
                logging.info('Result for task with task_id {} not found'.format(task_id))
            else:
                logging.info('Result for task with task_id {} is {}'.format(task_id, result.message))
            return
        sleep(1)


def post_task_packet(args: 'Namespace') -> None:
    with closing(connect(args)) as s:
        send_task(args, s)
        task_id = Message.recv(s).task_id
        logging.info('New task have task_id {}'.format(task_id))


def post_task(args: 'Namespace') -> None:
    """Process post new task"""
    if args.simple:
        post_task_simple(args)
    elif args.packet:
        post_task_packet(args)
    else:
        raise ValueError()


def status_task(args: 'Namespace') -> None:
    statuses = {
        Status.NOT_FOUND: 'Task with task_id {} NOT FOUND',
        Status.QUEUE: 'Task with task_id {} in QUEUE',
        Status.PROGRESS: 'Task with task_id {} in PROGRESS',
        Status.COMPLETED: 'Task with task_id {} COMPLETED',
    }
    with closing(connect(args)) as s:
        Message(command=Command.CS_GET_TASK_STATUS, task_id=args.task_id).send(s)
        status = Message.recv(s).status
        logging.info(statuses[status].format(args.task_id))


def result_task(args: 'Namespace') -> None:
    with closing(connect(args)) as s:
        Message(command=Command.CS_GET_TASK_RESULT, task_id=args.task_id).send(s)
        result = Message.recv(s)
        if result.status == Status.NOT_FOUND:
            logging.info('Result for task with task_id {} NOT FOUND'.format(args.task_id))
        else:
            logging.info('Result for task with task_id {} is {}'.format(args.task_id, result.message))


def main() -> None:
    """Show menu to user"""
    parser = ArgumentParser()

    parser.add_argument('address', help='Server IP address', metavar='IP')
    parser.add_argument('port', type=int, help='Server port', metavar='PORT')

    subparsers = parser.add_subparsers(help='Action')
    subparsers.required = True
    subparsers.metavar = 'ACTION'

    parser_post_task = subparsers.add_parser('post', help='Post new tast')
    parser_post_task.set_defaults(func=post_task)
    parser_post_task.add_argument('message', help='Message for processing', metavar='MSG')
    group_mode = parser_post_task.add_mutually_exclusive_group(required=True)
    group_mode.add_argument('--simple', action='store_true', help='Post task in simple mode')
    group_mode.add_argument('--packet', action='store_true', help='Post task in packet mode')
    group_type = parser_post_task.add_mutually_exclusive_group(required=True)
    group_type.add_argument('--reverse', action='store_true', help='Post reverse task')
    group_type.add_argument('--transposition', action='store_true', help='Post transposition task')

    parser_status_task = subparsers.add_parser('status', help='Get tast status')
    parser_status_task.set_defaults(func=status_task)
    parser_status_task.add_argument('task_id', type=int, help='Task ID for request', metavar='TASK_ID')

    parser_result_task = subparsers.add_parser('result', help='Get task result')
    parser_result_task.set_defaults(func=result_task)
    parser_result_task.add_argument('task_id', type=int, help='Task ID for request', metavar='TASK_ID')

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception:
        logging.exception('main')


if __name__ == '__main__':
    main()
