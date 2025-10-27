import logging
from datetime import datetime

from kafka import KafkaConsumer

from goquant.consumers.base import BaseConsumer
from goquant.core.kafka_client import get_kafka_consumer
from goquant.schemas import TradeSignalMessage

logger = logging.getLogger(__name__)


class LoggingSink(BaseConsumer):
    """
    A simple consumer that subscribes to the final 'trade_signals'
    topic and logs the output in a human-readable format.
    """

    def __init__(self):
        logger.info("Initializing LoggingSink...")
        self.consumer: KafkaConsumer = get_kafka_consumer(
            topic="trade_signals", group_id="log-sinks"
        )

    def run(self):
        """Starts the main consumer loop."""
        logger.info("Starting consumer loop for topic 'trade_signals'...")
        try:
            for message in self.consumer:
                try:
                    data = TradeSignalMessage.model_validate(message.value)

                    # Log the final signal with high visibility
                    logger.warning("=" * 70)
                    logger.warning(
                        f"  FINAL TRADE SIGNAL | Asset: {data.asset_name} ({data.ticker})"
                    )
                    logger.warning(
                        f"          Timestamp: {datetime.fromtimestamp(data.timestamp_utc).isoformat()}"
                    )
                    logger.warning(
                        "             Signal: %s (Confidence: %.0f%%)",
                        data.signal,
                        data.confidence * 100,
                    )
                    logger.warning("             Reason: %s", data.reason)
                    logger.warning("        F&G Score: %.2f", data.fear_greed_score)
                    logger.warning("=" * 70)

                except Exception as e:
                    logger.error("Error processing message: %s", e, exc_info=True)

        except KeyboardInterrupt:
            logger.info("Shutdown signal received.")
        finally:
            self.close()

    def close(self):
        """Shutdown..."""
        logger.info("Closing LoggingSink.")
        if self.consumer:
            self.consumer.close()
