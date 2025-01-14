import pickle
from synchronicity import Synchronizer


s = Synchronizer()

@s
class PicklableClass:
    async def f(self, x):
        return x**2


def test_pickle():
    obj = PicklableClass()
    assert obj.f(42) == 1764
    data = pickle.dumps(obj)
    obj2 = pickle.loads(data)
    assert obj2.f(43) == 1849


def test_pickle_synchronizer():
    pickle.dumps(s)
