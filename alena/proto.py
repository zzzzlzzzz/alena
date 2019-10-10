from enum import Enum
from socket import socket
from struct import pack, unpack, error
from typing import Optional


"""
1.

C->S
CS_POST_TASK
- message
S->C
SC_POST_TASK
- task_id

2.

C->S
CS_GET_TASK_STATUS
- task_id
S->C
SC_GET_TASK_STATUS
- status

3.

C->S
CS_GET_TASK_RESULT
- task_id
S->C
SC_GET_TASK_RESULT
- message

"""


class Command(Enum):
    CS_POST_TASK_REVERSE = 0
    CS_POST_TASK_TRANSPOSITION = 1
    SC_POST_TASK = 2
    CS_GET_TASK_STATUS = 3
    SC_GET_TASK_STATUS = 4
    CS_GET_TASK_RESULT = 5
    SC_GET_TASK_RESULT = 6


class Status(Enum):
    QUEUE = 0
    PROGRESS = 1
    COMPLETED = 2
    NOT_FOUND = 3


class Message:
    """Protocol message for send over network"""
    MAX_LENGTH = 256

    def __init__(self, command: Optional['Command'] = None, message: Optional[str] = None,
                 task_id: Optional[int] = None, status: Optional['Status'] = None):
        self.command = command
        self.message = message
        self.task_id = task_id
        self.status = status

    @staticmethod
    def _recv_bytes(s: 'socket', n: int) -> bytes:
        """Receive n bytes from socket

        :param s: Socket for receiving
        :param n: Count of bytes
        :return: Received data
        """
        data = bytes()
        while len(data) < n:
            packet = s.recv(n - len(data))
            if not packet:
                raise ValueError()
            data += packet
        return data

    @staticmethod
    def recv(s: 'socket') -> 'Message':
        """Read message from socket and return

        :param s: Socket for receiving
        :return: Message
        """
        try:
            command, = unpack('>I', Message._recv_bytes(s, 4))
            command = Command(command)
            if any((command == Command.CS_POST_TASK_REVERSE,
                    command == Command.CS_POST_TASK_TRANSPOSITION)):
                length, = unpack('>I', Message._recv_bytes(s, 4))
                if length > Message.MAX_LENGTH:
                    raise ValueError()
                message = Message._recv_bytes(s, length).decode('utf8')
                return Message(command=command, message=message)
            elif command == Command.SC_POST_TASK:
                task_id, = unpack('>I', Message._recv_bytes(s, 4))
                return Message(command=command, task_id=task_id)
            elif command == Command.CS_GET_TASK_STATUS:
                task_id, = unpack('>I', Message._recv_bytes(s, 4))
                return Message(command=command, task_id=task_id)
            elif command == Command.SC_GET_TASK_STATUS:
                status, = unpack('>I', Message._recv_bytes(s, 4))
                status = Status(status)
                return Message(command=command, status=status)
            elif command == Command.CS_GET_TASK_RESULT:
                task_id, = unpack('>I', Message._recv_bytes(s, 4))
                return Message(command=command, task_id=task_id)
            elif command == Command.SC_GET_TASK_RESULT:
                status, length = unpack('>II', Message._recv_bytes(s, 8))
                status = Status(status)
                if length > Message.MAX_LENGTH:
                    raise ValueError()
                message = Message._recv_bytes(s, length).decode('utf8') if length else ''
                return Message(command=command, status=status, message=message)
            else:
                raise ValueError()
        except error:
            raise ValueError()

    def send(self, s: 'socket') -> None:
        """
        Write message to socket

        :param s: Socket for sending
        :return: None
        """
        if any((self.command == Command.CS_POST_TASK_REVERSE,
                self.command == Command.CS_POST_TASK_TRANSPOSITION)):
            message = self.message.encode('utf8')
            packet = pack('>II{}s'.format(len(message)), self.command.value, len(message), message)
        elif self.command == Command.SC_POST_TASK:
            packet = pack('>II', self.command.value, self.task_id)
        elif self.command == Command.CS_GET_TASK_STATUS:
            packet = pack('>II', self.command.value, self.task_id)
        elif self.command == Command.SC_GET_TASK_STATUS:
            packet = pack('>II', self.command.value, self.status.value)
        elif self.command == Command.CS_GET_TASK_RESULT:
            packet = pack('>II', self.command.value, self.task_id)
        elif self.command == Command.SC_GET_TASK_RESULT:
            message = self.message.encode('utf8')
            packet = pack('>III{}s'.format(len(message)), self.command.value, self.status.value, len(message), message)
        else:
            raise ValueError()
        s.sendall(packet)

    def __eq__(self, other: 'Message') -> bool:
        return all((self.command == other.command,
                    self.message == other.message,
                    self.task_id == other.task_id,
                    self.status == other.status))
