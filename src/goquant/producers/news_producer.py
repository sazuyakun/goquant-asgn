"""News Producer to fetch articles from NewsAPI and publish to Kafka."""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict

import requests
from kafka import KafkaProducer

from goquant.core.kafka_client import get_kafka_producer
from goquant.producers.base import BaseProducer
from goquant.schemas import NewsApiResponse, RawTextMessage

logger = logging.getLogger(__name__)


class NewsProducer(BaseProducer):
    """
    Fetches news articles from NewsAPI for a list of queries
    and publishes them to a Kafka topic. Runs on a timer.
    """

    BASE_URL = "https://newsapi.org/v2/everything"
    FETCH_INTERVAL_SECONDS = 300  # 5 minutes

    def __init__(self, config: Dict[str, Any]):

        self.producer: KafkaProducer = get_kafka_producer()
        self.assets = config.get("assets", [])
        self.api_key = os.getenv("NEWSAPI_API_KEY")
        if not self.api_key:
            logger.error("NEWSAPI_API_KEY environment variable not set")
            raise ValueError("NEWSAPI_API_KEY environment variable not set")

        self.topic = "raw_text_data"

        self.seen_article_urls: set[str] = set()

        self.query_map = []
        for asset in self.assets:
            asset_name = asset["name"]
            for query in asset.get("news_queries", []):
                self.query_map.append({"asset_name": asset_name, "query": query})

        if not self.query_map:
            logger.warning(
                "No news queries configured for monitoring. No 'news_queries' defined in config"
            )

    def fetch_articles_for_query(self, asset_name: str, query: str) -> None:
        """Fetches articles for a specific query"""
        params = {
            "q": query,
            "apiKey": self.api_key,
            "pageSize": 20,
            "sortBy": "publishedAt",
            "language": "en",
        }

        try:
            logger.info("Fetching news data for query: %s", query)
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            logger.info("News data fetched successfully.")
            news_data = NewsApiResponse.model_validate(response.json())

            for article in news_data.articles:
                if article.url in self.seen_article_urls:
                    continue  # Skip already seen articles

                self.seen_article_urls.add(article.url)

                # Timestamp to UNIX
                timestamp_utc = (
                    datetime.fromisoformat(article.publishedAt)
                    .replace(tzinfo=timezone.utc)
                    .timestamp()
                )

                message = RawTextMessage(
                    asset_name=asset_name,
                    source="news",
                    timestamp_utc=timestamp_utc,
                    text=article.title,
                    content=article.description,
                    metadata=article.model_dump(),
                )

                self.producer.send(self.topic, value=message.model_dump(mode="json"))
                logger.info(
                    "NEWS | %s | Sent article: %s", asset_name, article.title[:50]
                )

        except requests.exceptions.HTTPError as http_err:
            logger.error("HTTP error occurred: %s - %s", http_err, response.text)
        except requests.exceptions.ConnectionError as conn_err:
            logger.error("Connection error occurred: %s", conn_err)
        except requests.exceptions.Timeout as timeout_err:
            logger.error("Timeout error occurred: %s", timeout_err)
        except requests.exceptions.RequestException as req_err:
            logger.error("An unexpected request error occurred: %s", req_err)
        except Exception as e:
            logger.error("Error fetching articles for query %s: %s", query, e)

    def run(self):
        """Main loop to fetch news articles at regular intervals"""
        if not self.query_map:
            return

        logger.info("Starting News Producer...")
        while True:
            try:
                start_time = time.time()
                logger.info("Fetching news articles for all queries...")

                for item in self.query_map:
                    self.fetch_articles_for_query(item["asset_name"], item["query"])
                    time.sleep(2)  # Stagger API Reqs

                # Wait for the remaining interval
                elapsed_time = time.time() - start_time
                wait_time = max(0, self.FETCH_INTERVAL_SECONDS - elapsed_time)
                logger.info("Sleeping for %s seconds before next fetch...", wait_time)
                time.sleep(wait_time)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received.")
                break
            except Exception as e:
                logger.error("Error in News Producer loop: %s retrying in 60s", e)
                time.sleep(60)  # Wait before retrying

    def close(self):
        """Shutdown..."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
