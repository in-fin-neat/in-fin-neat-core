from typing import Any, Callable
import logging


LOGGER = logging.getLogger(__name__)


def log_wrapper(func: Callable, *args: Any, **kwargs: Any) -> Any:
    LOGGER.info(f"calling {func.__name__} with {kwargs}")
    response = func(*args, **kwargs)
    LOGGER.info(f"response from {func.__name__} is {response}")
    return response
