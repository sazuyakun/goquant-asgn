"""A module for preprocessing text data from various sources"""

import logging
import re
from functools import lru_cache

logger = logging.getLogger(__name__)


class TextPreprocessor:
    def __init__(self):

        self.url_pattern = re.compile(r"https?://\S+|www\.\S+")
        self.mention_pattern = re.compile(r"@\w+")
        self.hashtag_pattern = re.compile(r"#\w+")
        self.ticker_pattern = re.compile(r"\$\w+")
        self.non_alphanumeric_pattern = re.compile(r"[^a-zA-Z0-9\s]")
        self.whitespace_pattern = re.compile(r"\s+")
        logger.info("TextPreprocessor initialized with regex patterns.")

    @lru_cache(maxsize=10000)
    def preprocess(self, text: str) -> str:
        """
        Preprocess the input text by removing special characters,
        converting to lowercase, and stripping extra whitespace.

        Source of the text: Reddit, News
        """
        if not isinstance(text, str) or not text:
            return ""

        text = text.lower()
        text = self.url_pattern.sub("", text)
        text = self.mention_pattern.sub("", text)
        text = self.ticker_pattern.sub("", text)  # Remove stock tickers
        # text = self.non_alphanumeric_pattern.sub("", text)
        text = self.whitespace_pattern.sub(" ", text).strip()

        return text
