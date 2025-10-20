"""Api endpoint to collect data from Newapi.org"""

import os

import requests
from dotenv import load_dotenv

from goquant.core.logging import logger
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
        if not self.api_key:
            raise ValueError("NEWSAPI_API_KEY environment variable not set")
        self.base_url = "https://newsapi.org/v2/everything"

    def fetch_data(self, query="all", page_size=10) -> NewsApiResponse:
        """
        Fetch news articles based on a query.
        """
        params = {
            "q": query,
            "apiKey": self.api_key,
            "pageSize": page_size,
        }

        try:
            logger.info("Fetching news data for query: %s", query)
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            logger.info("News data fetched successfully.")
            return NewsApiResponse.model_validate(response.json())
        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred: %s - %s", http_err, response.text)
        except requests.exceptions.ConnectionError as conn_err:
            logger.error("Connection error occurred: %s", conn_err)
        except requests.exceptions.Timeout as timeout_err:
            logger.error("Timeout error occurred: %s", timeout_err)
        except requests.exceptions.RequestException as req_err:
            logger.error("An unexpected request error occurred: %s", req_err)

        # Return a default empty response on failure
        return NewsApiResponse(status="error", totalResults=0, articles=[])
