"""Reddit Producer that streams new submissions from specified subreddits"""

import logging
import os
import time
from typing import Any, Dict

import praw
from kafka import KafkaProducer

from goquant.core.kafka_client import get_kafka_producer
from goquant.producers.base import BaseProducer
from goquant.schemas import RawTextMessage, RedditPost

# from goquant.sentiment_analysis.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


class RedditProducer(BaseProducer):
    """
    Connects to the Reddit API and streams new submissions from
    a list of subreddits, publishing them to a Kafka topic.
    """

    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing RedditProducer...")
        self.producer: KafkaProducer = get_kafka_producer()
        self.assets = config.get("assets", [])
        self.general_sources = config.get("general_reddit_sources", [])
        self.reddit: praw.Reddit = self._create_reddit_client()
        self.topic = "raw_text_data"

        # Mapping from subreddit name to asset name
        self.subreddit_to_asset_map: Dict[str, str] = {}
        all_subreddits = set()

        # asset-specific subreddits
        for asset in self.assets:
            asset_name = asset["name"]
            for sub in asset.get("reddit_subreddits", []):
                sub_lower = sub.lower()
                all_subreddits.add(sub_lower)
                self.subreddit_to_asset_map[sub_lower] = asset_name

        # general-source subreddits
        for sub in self.general_sources:
            sub_lower = sub.lower()
            all_subreddits.add(sub_lower)
            self.subreddit_to_asset_map[sub_lower] = (
                "general"  # Map this subreddit to the "general" tag
            )

        self.subreddit_list = "+".join(all_subreddits)
        if not self.subreddit_list:
            logger.warning("No subreddits configured for monitoring.")
            self.subreddit = None
        else:
            logger.info("Monitoring subreddits: %s", self.subreddit_list)
            self.subreddit = self.reddit.subreddit(self.subreddit_list)

    def _create_reddit_client(self) -> praw.Reddit:
        """
        Create and return a Reddit client using PRAW.
        """
        try:
            client = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_USER_AGENT"),
                read_only=True,
            )
            logger.info("Reddit client created successfully.")
            return client
        except Exception as e:
            logger.error("Error creating Reddit client: %s", e)
            raise

    def run(self):
        """Main streaming loop that runs indefinitely"""
        if not self.subreddit:
            return

        logger.info(
            "Starting Reddit streaming for subreddit(s) : %s...", self.subreddit_list
        )
        while True:
            try:
                # skip_existing to avoid existing posts
                for post in self.subreddit.stream.submissions(skip_existing=True):
                    try:
                        asset_name = self.subreddit_to_asset_map.get(
                            post.subreddit.display_name.lower()
                        )
                        if not asset_name:
                            continue

                        reddit_post = RedditPost(
                            title=post.title,
                            score=post.score,
                            content=post.selftext,
                            comments=[],  # Avoid in realtime scenario
                            url=post.url,
                            num_comments=post.num_comments,
                            created_utc=post.created_utc,
                        )
                        # Kafka message
                        message = RawTextMessage(
                            asset_name=asset_name,
                            source="reddit",
                            timestamp_utc=post.created_utc,
                            text=post.title,
                            content=post.content,
                            metadata=reddit_post.model_dump(),
                        )

                        self.producer.send(self.topic, value=message.model_dump())
                        logger.info(
                            "REDDIT | %s | Sent post: %s", asset_name, post.title[:50]
                        )
                    except Exception as e:
                        logger.error(
                            "Error processing Reddit post with post id %s : %s",
                            post.id,
                            e,
                            exc_info=False,
                        )

            except KeyboardInterrupt:
                logger.info("Shutdown signal received.")
                break
            except Exception as e:
                logger.error("Error in Reddit streaming loop: %s retrying in 60s", e)
                time.sleep(60)  # Wait before retrying

    def close(self):
        """Shutdown..."""
        logger.info("Closing RedditProducer...")
        if self.producer:
            self.producer.flush()
            self.producer.close()
