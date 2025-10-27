"""Sentiment Analysis Consumer Module"""

import logging
from typing import Any, Dict, List, Set

from kafka import KafkaConsumer, KafkaProducer

from goquant.consumers.base import BaseConsumer
from goquant.core.kafka_client import get_kafka_consumer, get_kafka_producer
from goquant.schemas import AnalyzedSentimentMessage, RawTextMessage
from goquant.sentiment_analysis.onnx_finbert import OnnxFinBert
from goquant.sentiment_analysis.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


class SentimentConsumer(BaseConsumer):
    """
    Consumes from 'raw_text_data', analyzes sentiment,
    and produces to 'analyzed_sentiment'.
    """

    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing SentimentConsumer...")
        self.consumer: KafkaConsumer = get_kafka_consumer(
            topic="raw_text_data", group_id="sentiment-analyzers"
        )
        self.producer: KafkaProducer = get_kafka_producer()
        self.in_topic = "raw_text_data"
        self.out_topic = "analyzed_sentiment"

        logger.info("Loading sentiment analysis model...")
        self.model = OnnxFinBert()
        self.preprocessor = TextPreprocessor()

        # Build NER keyword to asset name map
        self.assets = config.get("assets", [])
        self.keyword_to_asset_map: Dict[str, str] = {}
        for asset in self.assets:
            asset_name = asset["name"]
            for keyword in asset.get("keywords", []):
                self.keyword_to_asset_map[keyword.lower()] = asset_name
        logger.info(
            f"NER keyword map built with {len(self.keyword_to_asset_map)} keywords."
        )

        logger.info("SentimentConsumer ready.")

    def _perform_ner(self, text: str) -> Set[str]:
        """
        Performs simple, fast keyword-based NER on a string.
        Returns a set of unique asset names found in the text.
        """
        found_assets = set()
        text_lower = text.lower().split()
        for word in text_lower:
            # Clean punctuation (like "tsla." -> "tsla")
            cleaned_word = word.strip(".,!?:;()\"'")
            if cleaned_word in self.keyword_to_asset_map:
                found_assets.add(self.keyword_to_asset_map[cleaned_word])
        return found_assets

    def run(self):
        """Runs the sentiment analysis consumer loop"""
        try:
            for message in self.consumer:
                try:
                    data = RawTextMessage.model_validate(message.value)

                    # Preprocess text
                    prep_text = self.preprocessor.preprocess(data.text)
                    prep_content = self.preprocessor.preprocess(data.content)

                    text_to_analyze = [t for t in [prep_text, prep_content] if t]

                    if not text_to_analyze:
                        logger.warning(
                            "Skipping message, no text found. Asset: %s",
                            data.asset_name,
                        )
                        continue

                    # Sentiment analysis
                    sentiments = self.model.predict(text_to_analyze)
                    if not sentiments:
                        logger.warning(
                            "Model returned no sentiment. Asset: %s", data.asset_name
                        )
                        continue

                    # Average Scores : [pos, neg, neutral]
                    avg_probs = [sum(col) / len(col) for col in zip(*sentiments)]

                    sentiment_score = float(avg_probs[0] - avg_probs[1])  # pos - neg

                    # NER
                    assets_to_publish_for = set()

                    if data.asset_name == "general":
                        # This is from r/investing etc.
                        # We MUST perform NER to find assets.
                        found_in_title = self._perform_ner(prep_text)
                        found_in_content = self._perform_ner(prep_content)
                        assets_to_publish_for = found_in_title.union(found_in_content)
                        if not assets_to_publish_for:
                            logger.info(
                                f"GENERAL | No assets found in: {data.text[:40]}..."
                            )
                            continue  # No tracked assets, skip.
                    else:
                        # This is from r/bitcoin etc.
                        # We trust the tag.
                        assets_to_publish_for.add(data.asset_name)

                    # Results
                    for asset in assets_to_publish_for:
                        output_message = AnalyzedSentimentMessage(
                            asset_name=asset,
                            source=data.source,
                            timestamp_utc=data.timestamp_utc,
                            sentiment_score=sentiment_score,
                            sentiment_probs=avg_probs,
                            metadata=data.metadata,
                        )

                        self.producer.send(
                            self.out_topic, value=output_message.model_dump()
                        )
                        logger.info(
                            "SENTIMENT | %-10s | Score: %.3f | %.40s...",
                            asset,
                            sentiment_score,
                            data.text,
                        )

                except Exception as e:
                    logger.error("Error processing message: %s", e)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
        finally:
            self.close()

    def close(self):
        """Shutdown..."""
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.close()
