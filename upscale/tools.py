from functools import wraps
from typing import Callable


def singleton(fabric_function: Callable) -> Callable:

    singleton_obj = None
    ready = False

    @wraps(fabric_function)
    def new_fabric(*args, **kwargs):
        nonlocal singleton_obj, ready

        if ready:
            return singleton_obj

        singleton_obj = fabric_function(*args, **kwargs)
        ready = True
        return singleton_obj

    return new_fabric
