try:
    import common.interfaces as interfaces
except ModuleNotFoundError:
    print('common package not in python path or dependencies not installed')


class Observer(interfaces.Callable):
    def __init__(
        self,
        name: str,
        callback: str,
    ):
        self.name = name
        super(Observer, self).__init__(callback=callback)
