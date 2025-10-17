"""Api endpoint to collect data from Newapi.org"""

import os

import requests
from dotenv import load_dotenv

from goquant.data_collectors.base import BaseCollector
from goquant.data_collectors.models import NewsApiResponse

load_dotenv()

NEWS_API_KEY = os.getenv("NEWSAPI_API_KEY")


class NewsCollector(BaseCollector):
    """
    Collector for News data.
    """

    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_API_KEY")

    def fetch_data(self, query="all", page_size=10) -> NewsApiResponse:
        """
        Fetch news articles based on a query.
        """
        url = f"https://newsapi.org/v2/everything?q={query}&apiKey={self.api_key}&pageSize={page_size}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return NewsApiResponse.model_validate(response.json())
