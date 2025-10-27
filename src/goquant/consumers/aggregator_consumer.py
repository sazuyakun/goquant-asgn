"""Aggregator Consumer: Aggregates sentiment and market data to compute Fear & Greed Index."""

import logging
import time
from collections import deque
from typing import Any, Deque, Dict, Optional, Tuple

from kafka import KafkaConsumer, KafkaProducer

from goquant.consumers.base import BaseConsumer
from goquant.core.kafka_client import get_kafka_consumer, get_kafka_producer
from goquant.schemas import (
    AggregatedMetricsMessage,
    AnalyzedSentimentMessage,
    RawMarketMessage,
)

logger = logging.getLogger(__name__)


class AssetAggregator:
    """
    Manages the state (data windows) for a single asset.
    This class contains the core financial and behavioral logic.
    """

    def __init__(self, asset_name: str, ticker: str):
        self.asset_name = asset_name
        self.ticker = ticker

        # Windows to store (timestamp, value) tuples
        # Analysis Timeframes
        self.sentiment_window: Deque[Tuple[float, float]] = deque()
        self.price_window: Deque[Tuple[float, float]] = deque()

        self.current_price = 0.0
        self.current_volume = 0.0

        # State for velocity calculation
        self.last_sentiment_1min = 0.0

    def add_sentiment(self, timestamp: float, score: float):
        """Adds a new sentiment data point."""
        self.sentiment_window.append((timestamp, score))

    def add_market_data(self, timestamp: float, price: float, volume: float):
        """Adds a new market data point."""
        self.price_window.append((timestamp, price))
        self.current_price = price
        self.current_volume = volume

    def _prune_window(self, window: Deque, max_age_seconds: int) -> None:
        """Removes old data from a window based on current time."""
        now = time.time()
        while window and window[0][0] < (now - max_age_seconds):
            window.popleft()

    def _calculate_avg(self, window: Deque) -> Optional[float]:
        """Calculates average of a value window."""
        if not window:
            return None
        return sum(item[1] for item in window) / len(window)

    def _calculate_pct_change(self, window: Deque) -> Optional[float]:
        """Calculates percent change of a value window."""
        if len(window) < 2:
            return None
        oldest_price = window[0][1]
        latest_price = window[-1][1]
        if oldest_price == 0:
            return None
        return ((latest_price - oldest_price) / oldest_price) * 100

    def aggregate(self) -> AggregatedMetricsMessage:
        """
        Calculates all metrics and the Fear & Greed Index.
        This is the core implementation of:
        - Backend Component 3: Fear & greed index calculation
        """
        now = time.time()

        # - Prune all windows to 15 minutes max
        self._prune_window(self.sentiment_window, 15 * 60)
        self._prune_window(self.price_window, 15 * 60)

        # - Helper to filter window by time
        def filter_window(window, seconds):
            return deque(item for item in window if item[0] >= (now - seconds))

        # - Calculate metrics
        # Multi-timeframe trend detection
        sent_1min = self._calculate_avg(filter_window(self.sentiment_window, 60))
        sent_5min = self._calculate_avg(filter_window(self.sentiment_window, 300))
        sent_15min = self._calculate_avg(self.sentiment_window)

        price_1min_pct = self._calculate_pct_change(
            filter_window(self.price_window, 60)
        )
        price_5min_pct = self._calculate_pct_change(
            filter_window(self.price_window, 300)
        )

        # Implements Sentiment momentum
        velocity = None
        if sent_1min is not None:
            if self.last_sentiment_1min != 0:
                velocity = sent_1min - self.last_sentiment_1min
            self.last_sentiment_1min = sent_1min

        # - Calculate Fear & Greed Index (0-100)

        # Sentiment (50% weight) - (scale -1..1 to 0..100)
        sent_score = 50
        if sent_5min is not None:
            sent_score = (sent_5min + 1) * 50

        # Price Momentum (30% weight) - (scale -5%..5% to 0..100)
        # Fund flow correlation
        momentum_score = 50
        if price_5min_pct is not None:
            clamped_pct = max(-5, min(5, price_5min_pct))  # Cap at +/- 5%
            momentum_score = (clamped_pct + 5) * 10

        # Sentiment Velocity (20% weight) - (scale -0.5..0.5 to 0..100)
        velocity_score = 50
        if velocity is not None:
            clamped_vel = max(-0.5, min(0.5, velocity))  # Cap change
            velocity_score = (clamped_vel + 0.5) * 100

        # Final Weighted Score
        fear_greed_score = (
            (sent_score * 0.5) + (momentum_score * 0.3) + (velocity_score * 0.2)
        )

        return AggregatedMetricsMessage(
            asset_name=self.asset_name,
            ticker=self.ticker,
            timestamp_utc=now,
            sentiment_1min_avg=sent_1min,
            sentiment_5min_avg=sent_5min,
            sentiment_15min_avg=sent_15min,
            sentiment_velocity=velocity,
            price=self.current_price,
            volume=self.current_volume,
            price_change_1min_pct=price_1min_pct,
            price_change_5min_pct=price_5min_pct,
            fear_greed_score=fear_greed_score,
        )


class AggregatorConsumer(BaseConsumer):
    """
    Consumes from 'analyzed_sentiment' AND 'raw_market_data',
    aggregates data in-memory, and produces to 'aggregated_metrics'.
    This is a STATEFUL service.
    """

    PUBLISH_INTERVAL_SECONDS = 5  # Publish new F&G index every 5s

    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing AggregatorConsumer...")
        self.consumer: KafkaConsumer = get_kafka_consumer(
            # Subscribe to multiple topics
            topic=[
                "analyzed_sentiment",
                "raw_market_data",
            ],
            group_id="aggregators",
        )
        self.assets = config.get("assets", [])
        self.producer: KafkaProducer = get_kafka_producer()
        self.out_topic = "aggregated_metrics"

        # This holds the state (the AssetAggregator object) for each asset
        self.asset_aggregators: Dict[str, AssetAggregator] = {}

        # Map tickers back to asset names from config
        self.ticker_to_asset_name: Dict[str, str] = {}
        for asset in self.assets:
            self.ticker_to_asset_name[asset["ticker"]] = asset["name"]
            self.asset_aggregators[asset["name"]] = AssetAggregator(
                asset["name"], asset["ticker"]
            )

        self.last_publish_time = 0.0

    def run(self):
        """Starts the main consumer loop."""
        logger.info("Starting AggregatorConsumer loop...")
        try:
            for message in self.consumer:
                now = time.time()
                try:
                    # --- Route Incoming Data to Correct Asset ---
                    if message.topic == "analyzed_sentiment":
                        data = AnalyzedSentimentMessage.model_validate(message.value)
                        if data.asset_name in self.asset_aggregators:
                            self.asset_aggregators[data.asset_name].add_sentiment(
                                data.timestamp_utc, data.sentiment_score
                            )

                    elif message.topic == "raw_market_data":
                        data = RawMarketMessage.model_validate(message.value)
                        asset_name = self.ticker_to_asset_name.get(data.ticker)
                        if asset_name and asset_name in self.asset_aggregators:
                            self.asset_aggregators[asset_name].add_market_data(
                                data.timestamp_utc, data.price, data.volume
                            )

                    # --- Publish Aggregations on a Timer ---
                    # This ensures a steady stream of F&G scores, not just on new data
                    if (now - self.last_publish_time) > self.PUBLISH_INTERVAL_SECONDS:
                        self.last_publish_time = now

                        for asset_name, aggregator in self.asset_aggregators.items():
                            # if aggregator.current_price == 0.0:
                            #     continue  # Don't publish if no market data yet

                            metrics_message = aggregator.aggregate()
                            self.producer.send(
                                self.out_topic, value=metrics_message.model_dump()
                            )
                            logger.info(
                                f"AGGREGATOR | {asset_name: <8} | F&G Score: {metrics_message.fear_greed_score:.2f}"
                            )

                except Exception as e:
                    logger.error("Error processing message: %s", e, exc_info=True)

        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
        finally:
            self.close()

    def close(self):
        """Shutdown..."""
        logger.info("Closing AggregatorConsumer.")
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
