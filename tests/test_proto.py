from struct import pack

from pytest import fixture, mark

from alena.proto import Command, Status, Message


@fixture(scope='function')
def socket_mock():
    class SocketMock:
        def __init__(self):
            self.data_in = None
            self.data_out = None

        def recv(self, amount):
            result = self.data_in[:amount]
            self.data_in = self.data_in[amount:]
            return result

        def sendall(self, data_out):
            self.data_out = data_out
    yield SocketMock()


@mark.parametrize('data,message',
                  [(pack('>II{}s'.format(len('test'.encode('utf8'))), Command.CS_POST_TASK_REVERSE.value, len('test'.encode('utf8')), 'test'.encode('utf8')),
                    Message(command=Command.CS_POST_TASK_REVERSE, message='test')),
                    (pack('>II{}s'.format(len('test'.encode('utf8'))), Command.CS_POST_TASK_TRANSPOSITION.value, len('test'.encode('utf8')), 'test'.encode('utf8')),
                    Message(command=Command.CS_POST_TASK_TRANSPOSITION, message='test')),
                   (pack('>II', Command.SC_POST_TASK.value, 1),
                    Message(command=Command.SC_POST_TASK, task_id=1)),
                   (pack('>II', Command.CS_GET_TASK_STATUS.value, 1),
                    Message(command=Command.CS_GET_TASK_STATUS, task_id=1)),
                   (pack('>II', Command.SC_GET_TASK_STATUS.value, Status.COMPLETED.value),
                    Message(command=Command.SC_GET_TASK_STATUS, status=Status.COMPLETED)),
                   (pack('>II', Command.CS_GET_TASK_RESULT.value, 3),
                    Message(command=Command.CS_GET_TASK_RESULT, task_id=3)),
                   (pack('>III{}s'.format(len('tset'.encode('utf8'))), Command.SC_GET_TASK_RESULT.value, Status.COMPLETED.value, len('tset'.encode('utf8')), 'tset'.encode('utf8')),
                    Message(command=Command.SC_GET_TASK_RESULT, status=Status.COMPLETED, message='tset')),
                   (pack('>III{}s'.format(len('привет'.encode('utf8'))), Command.SC_GET_TASK_RESULT.value, Status.COMPLETED.value, len('привет'.encode('utf8')), 'привет'.encode('utf8')),
                    Message(command=Command.SC_GET_TASK_RESULT, status=Status.COMPLETED, message='привет')),
                    (pack('>III{}s'.format(len(''.encode('utf8'))), Command.SC_GET_TASK_RESULT.value, Status.NOT_FOUND.value, len(''.encode('utf8')), ''.encode('utf8')),
                    Message(command=Command.SC_GET_TASK_RESULT, status=Status.NOT_FOUND, message='')),
                   ])
def test_recv(data, message, socket_mock):
    socket_mock.data_in = data
    assert Message.recv(socket_mock) == message


@mark.parametrize('message,data',
                  [(Message(command=Command.CS_POST_TASK_REVERSE, message='test'),
                    pack('>II{}s'.format(len('test'.encode('utf8'))), Command.CS_POST_TASK_REVERSE.value, len('test'.encode('utf8')), 'test'.encode('utf8'))),
                    (Message(command=Command.CS_POST_TASK_TRANSPOSITION, message='test'),
                    pack('>II{}s'.format(len('test'.encode('utf8'))), Command.CS_POST_TASK_TRANSPOSITION.value, len('test'.encode('utf8')), 'test'.encode('utf8'))),
                   (Message(command=Command.SC_POST_TASK, task_id=1),
                    pack('>II', Command.SC_POST_TASK.value, 1)),
                   (Message(command=Command.CS_GET_TASK_STATUS, task_id=2),
                    pack('>II', Command.CS_GET_TASK_STATUS.value, 2)),
                   (Message(command=Command.SC_GET_TASK_STATUS, status=Status.PROGRESS),
                    pack('>II', Command.SC_GET_TASK_STATUS.value, Status.PROGRESS.value)),
                   (Message(command=Command.CS_GET_TASK_RESULT, task_id=3),
                    pack('>II', Command.CS_GET_TASK_RESULT.value, 3)),
                   (Message(command=Command.SC_GET_TASK_RESULT, status=Status.COMPLETED, message='tset'),
                    pack('>III{}s'.format(len('tset'.encode('utf8'))), Command.SC_GET_TASK_RESULT.value, Status.COMPLETED.value, len('tset'.encode('utf8')), 'tset'.encode('utf8'))),
                   (Message(command=Command.SC_GET_TASK_RESULT, status=Status.COMPLETED, message='привет'),
                    pack('>III{}s'.format(len('привет'.encode('utf8'))), Command.SC_GET_TASK_RESULT.value, Status.COMPLETED.value, len('привет'.encode('utf8')), 'привет'.encode('utf8'))),
                   (Message(command=Command.SC_GET_TASK_RESULT, status=Status.NOT_FOUND, message=''),
                    pack('>III{}s'.format(len(''.encode('utf8'))), Command.SC_GET_TASK_RESULT.value, Status.NOT_FOUND.value, len(''.encode('utf8')), ''.encode('utf8'))),
                   ])
def test_send(message, data, socket_mock):
    message.send(socket_mock)
    assert socket_mock.data_out == data
