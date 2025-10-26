from abc import ABC, abstractmethod
from typing import Any


class BaseSentimentAnalyzer(ABC):
    """
    Base class for all sentiment analyzers
    """

    @abstractmethod
    def predict(self, *args, **kwargs) -> Any:
        """Analyze the sentiment of the given text and return 'positive', 'negative', or 'neutral'."""
        pass
