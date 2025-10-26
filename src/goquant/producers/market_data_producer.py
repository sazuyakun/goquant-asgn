import logging
import time
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf
from kafka import KafkaProducer

from goquant.core.kafka_client import get_kafka_producer
from goquant.producers.base import BaseProducer
from goquant.schemas import MarketDataPoint, RawMarketMessage

logger = logging.getLogger(__name__)


class MarketDataProducer(BaseProducer):
    """
    Fetches real-time market data from yfinance for a list of tickers
    and publishes them to a Kafka topic. Runs on a timer.
    """

    FETCH_INTERVAL_SECONDS = 15

    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing MarketDataProducer...")
        self.producer: KafkaProducer = get_kafka_producer()
        self.assets = config.get("assets", [])
        self.topic = "raw_market_data"

        self.tickers = list(
            set([asset["ticker"] for asset in self.assets if "ticker" in asset])
        )
        if not self.tickers:
            logger.warning("No tickers configured for monitoring.")
        else:
            logger.info("Monitoring tickers: %s", ", ".join(self.tickers))
            self.yf_tickers = yf.Tickers(" ".join(self.tickers))

    def run(self):
        """Runs the market producer in a polling loop"""
        if not self.tickers:
            return

        logger.info("Starting MarketDataProducer loop...")
        while True:
            try:
                start_time = time.time()

                # 1-minute interval data for the last day
                hist = self.yf_tickers.history(period="1d", interval="1m")

                if hist.empty:
                    logger.warning("No market data fetched from yfinance.")
                    time.sleep(self.FETCH_INTERVAL_SECONDS)
                    continue

                for ticker in self.tickers:
                    try:
                        last_close = hist["Close"][ticker].iloc[-1]
                        last_volume = hist["Volume"][ticker].iloc[-1]

                        if pd.isna(last_close) or pd.isna(last_volume):
                            logger.warning(f"NaN data for {ticker}, skipping.")
                            continue

                        timestamp_utc = hist.index[-1].timestamp()

                        message = RawMarketMessage(
                            ticker=ticker,
                            timestamp_utc=timestamp_utc,
                            price=float(last_close),
                            volume=int(last_volume),
                        )
                        self.producer.send(self.topic, value=message.model_dump())
                        logger.info(
                            "MARKET | %s | Sent price: %.2f", ticker, last_close
                        )

                    except Exception as e:
                        logger.error(f"Failed to process data for ticker {ticker}: {e}")

                elapsed_time = time.time() - start_time
                wait_time = max(0, self.FETCH_INTERVAL_SECONDS - elapsed_time)
                time.sleep(wait_time)
            except KeyboardInterrupt:
                logger.info("Shutdown signal received.")
                break
            except Exception as e:
                logger.error(
                    "Unexpected error in MarketDataProducer main loop: %s, waiting for 60s",
                    e,
                )
                time.sleep(60)  # Wait before retrying

    def close(self):
        """Shutdown..."""
        if self.producer:
            self.producer.flush()
            self.producer.close()
