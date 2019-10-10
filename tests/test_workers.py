from pytest import mark


from alena.workers import worker_reverse, worker_transposition
from alena import workers


@mark.parametrize('source,result', [('test', 'tset'),
                                    ('reversed', 'desrever'), ])
def test_worker_reverse(monkeypatch, source, result):
    def sleep_mock(*_):
        pass
    monkeypatch.setattr(workers, 'sleep', sleep_mock)
    assert worker_reverse(source) == result


@mark.parametrize('source,result', [('abcdef', 'badcfe'),
                                    ('qwert', 'wqret')])
def test_worker_transposition(monkeypatch, source, result):
    def sleep_mock(*_):
        pass
    monkeypatch.setattr(workers, 'sleep', sleep_mock)
    assert worker_transposition(source) == result
