"""A module for preprocessing text data from various sources"""

import re
from functools import lru_cache


class TextPreprocessor:
    def __init__(self):
        self.url_pattern = re.compile(r"https?://\S+|www\.\S+")
        self.mention_pattern = re.compile(r"@\w+")
        self.hashtag_pattern = re.compile(r"#\w+")
        self.ticker_pattern = re.compile(r"\$\w+")
        self.non_alphanumeric_pattern = re.compile(r"[^a-zA-Z0-9\s]")
        self.whitespace_pattern = re.compile(r"\s+")

    @lru_cache(maxsize=10000)
    def preprocess(self, text: str) -> str:
        """
        Preprocess the input text by removing special characters,
        converting to lowercase, and stripping extra whitespace.

        Source of the text: Reddit, News
        """
        text = text.lower()
        text = self.url_pattern.sub("", text)  # Remove the urls
        text = self.mention_pattern.sub("", text)  # Remove mentions
        # text = self.non_alphanumeric_pattern.sub("", text)
        text = self.whitespace_pattern.sub(" ", text).strip()

        return text
