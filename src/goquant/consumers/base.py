"""Inheritable base class for all consumers"""

from abc import ABC, abstractmethod
from typing import Any


class BaseConsumer(ABC):
    """
    Base class for all kafka consumers
    """

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
