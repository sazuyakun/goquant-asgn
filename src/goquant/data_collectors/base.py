"""Inheritable base class for all collectors"""

from abc import ABC, abstractmethod
from typing import Any


class BaseCollector(ABC):
    """
    Base class for all data collectors
    """

    @abstractmethod
    def fetch_data(self, *args, **kwargs) -> Any:
        """Method to fetch data from the source"""
        pass
