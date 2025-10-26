"""Inheritable base class for all collectors"""

from abc import ABC, abstractmethod
from typing import Any


class BaseProducer(ABC):
    """
    Base class for all data collectors
    """

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Method to fetch data from the source"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Method to stop the data collection"""
        pass
