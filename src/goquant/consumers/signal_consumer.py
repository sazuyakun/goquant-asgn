"""Signal Consumer Module."""

import logging
import time
from typing import Dict

from kafka import KafkaConsumer, KafkaProducer

from goquant.consumers.base import BaseConsumer
from goquant.core.kafka_client import get_kafka_consumer, get_kafka_producer
from goquant.schemas import AggregatedMetricsMessage, TradeSignalMessage

logger = logging.getLogger(__name__)


class SignalConsumer(BaseConsumer):
    """
    Consumes from 'aggregated_metrics', applies trading logic,
    and produces to 'trade_signals'.
    This is the final "Signal Generation" step.
    """

    # Cooldown per asset to avoid spamming signals
    COOLDOWN_SECONDS = 300  # 5 minutes

    def __init__(self):
        logger.info("Initializing SignalConsumer...")
        self.consumer: KafkaConsumer = get_kafka_consumer(
            topic="aggregated_metrics",
            group_id="signal-generators",
            auto_offset_reset="latest",
        )
        self.producer: KafkaProducer = get_kafka_producer()
        self.out_topic = "trade_signals"

        # State: track last signal time per asset
        self.last_signal_time: Dict[str, float] = {}

    def run(self):
        """Starts the main consumer loop."""
        logger.info("Starting consumer loop for topic 'aggregated_metrics'...")
        try:
            for message in self.consumer:
                now = time.time()
                try:
                    data = AggregatedMetricsMessage.model_validate(message.value)

                    # Check cooldown
                    # last_time = self.last_signal_time.get(data.asset_name, 0)
                    # if (now - last_time) < self.COOLDOWN_SECONDS:
                    #     continue  # In cooldown, skip logic

                    # --- Trading Logic (Implementation of Behavioral Finance) ---
                    # This is where your custom strategies are implemented.

                    signal = "HOLD"
                    confidence = 0.0
                    reason = "Neutral"

                    # --- STRATEGY 1: CONTRARIAN BUY ---
                    # Logic: Extreme Fear (market over-sold) + sentiment is
                    # starting to recover (positive velocity).
                    if (
                        data.fear_greed_score < 20
                        and data.sentiment_velocity is not None
                        and data.sentiment_velocity > 0.1
                    ):
                        signal = "BUY"
                        confidence = 0.75
                        reason = "Contrarian BUY: Extreme Fear (<20) + Rising Sentiment Velocity"

                    # --- STRATEGY 2: CONTRARIAN SELL ---
                    # Logic: Extreme Greed (market over-bought) + price is
                    # starting to drop (negative momentum).
                    elif (
                        data.fear_greed_score > 85
                        and data.price_change_1min_pct is not None
                        and data.price_change_1min_pct < -0.2
                    ):
                        signal = "SELL"
                        confidence = 0.80
                        reason = "Contrarian SELL: Extreme Greed (>85) + Negative Price Momentum"

                    # --- STRATEGY 3: TREND-FOLLOWING BUY ---
                    # Logic: Strong Greed + Strong positive sentiment + Strong
                    # price momentum. (Riding the wave)
                    elif (
                        data.fear_greed_score > 70
                        and data.sentiment_5min_avg is not None
                        and data.sentiment_5min_avg > 0.3
                        and data.price_change_5min_pct is not None
                        and data.price_change_5min_pct > 0.5
                    ):
                        signal = "BUY"
                        confidence = 0.60
                        reason = (
                            "Trend BUY: Strong Greed (>70) + Positive Sentiment & Price"
                        )

                    # --- End of Trading Logic ---

                    # if signal != "HOLD":
                    output_message = TradeSignalMessage(
                        asset_name=data.asset_name,
                        ticker=data.ticker,
                        timestamp_utc=now,
                        signal=signal,
                        confidence=confidence,
                        reason=reason,
                        fear_greed_score=data.fear_greed_score,
                    )

                    self.producer.send(
                        self.out_topic, value=output_message.model_dump()
                    )
                    self.last_signal_time[data.asset_name] = now  # Update cooldown

                    if signal != "HOLD":
                        logger.warning(
                            "!!! SIGNAL | %s | %s | Conf: %.2f | %s",
                            data.asset_name,
                            signal,
                            confidence,
                            reason,
                        )
                    else:
                        logger.info(
                            "No trade signal for %s. FG Score: %d",
                            data.asset_name,
                            data.fear_greed_score,
                        )

                except Exception as e:
                    logger.error("Error processing message: %s", e, exc_info=True)

        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
        finally:
            self.close()

    def close(self):
        """Shutdown..."""
        logger.info("Closing SignalConsumer.")
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
            self.producer.close()
