from time import sleep
from enum import Enum


class TaskType(Enum):
    REVERSE = 1
    TRANSPOSITION = 2


def worker_reverse(data: str) -> str:
    """Reverse string

    :param data: Source string
    :return: Reversed string
    """
    sleep(3)
    return data[::-1]


def worker_transposition(data: str) -> str:
    """Transposition string

    :param data: Source string
    :return: Transposed string
    """
    sleep(7)
    last_letter = ''
    if len(data) % 2:
        last_letter = data[-1]
        data = data[:-1]
    return ''.join(map(lambda _: '{}{}'.format(_[1], _[0]), zip(data[::2], data[1::2]))) + last_letter


worker_table = {
    TaskType.REVERSE: worker_reverse,
    TaskType.TRANSPOSITION: worker_transposition,
}