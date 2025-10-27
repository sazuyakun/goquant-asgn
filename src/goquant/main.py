"""Main entry point for launching producers and consumers"""

import argparse
import logging
import sys

# from goquant.consumers.aggregator_consumer import AggregatorConsumer
# from goquant.consumers.sentiment_consumer import SentimentConsumer
from goquant.consumers import (
    AggregatorConsumer,
    LoggingSink,
    SentimentConsumer,
    SignalConsumer,
)
from goquant.core.config import load_config
from goquant.core.logging_config import setup_logging
from goquant.producers.market_data_producer import MarketDataProducer
from goquant.producers.news_producer import NewsProducer
from goquant.producers.reddit_producer import RedditProducer

# from goquant.consumers.signal_consumer import SignalConsumer
# from goquant.consumers.logging_sink import LoggingSink

# Get a logger for the main entry point
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for launching producers and consumers.
    This centralized launcher allows managing all microservices
    from one script, simplifying deployment and process management.
    """
    setup_logging()

    # loading configuration...
    try:
        config = load_config()
        logger.info("Configuration 'config/targets.yml' loaded.")
    except FileNotFoundError as e:
        logger.error("FATAL: %s. Please ensure 'config/targets.yml' exists.", e)
        sys.exit(1)
    except Exception as e:
        logger.error("FATAL: Error loading config: %s", e)
        sys.exit(1)

    # cli argument parsing
    parser = argparse.ArgumentParser(description="Fear & Greed Sentiment Engine")
    subparsers = parser.add_subparsers(dest="service_type", required=True)

    # Producer Commands
    producer_parser = subparsers.add_parser("producer", help="Run a data producer")
    producer_subparsers = producer_parser.add_subparsers(
        dest="producer_name", required=True
    )
    producer_subparsers.add_parser("reddit", help="Run the Reddit streaming producer")
    producer_subparsers.add_parser("news", help="Run the News polling producer")
    producer_subparsers.add_parser(
        "market", help="Run the Market Data polling producer"
    )

    # Consumer Commands
    consumer_parser = subparsers.add_parser("consumer", help="Run a data consumer")
    consumer_subparsers = consumer_parser.add_subparsers(
        dest="consumer_name", required=True
    )
    consumer_subparsers.add_parser(
        "sentiment", help="Run the sentiment analysis consumer"
    )
    consumer_subparsers.add_parser(
        "aggregator", help="Run the F&G index aggregation consumer"
    )
    consumer_subparsers.add_parser(
        "signal", help="Run the trade signal generation consumer"
    )
    consumer_subparsers.add_parser("logger")  # Logs final signals

    args = parser.parse_args()

    service = None

    try:
        if args.service_type == "producer":
            assets = config.get("assets", [])
            if not assets:
                logger.warning(
                    "No assets found in 'config/targets.yml'. Producers will exit."
                )
                sys.exit(0)

            if args.producer_name == "reddit":
                service = RedditProducer(config)
            elif args.producer_name == "news":
                service = NewsProducer(config)
            elif args.producer_name == "market":
                service = MarketDataProducer(config)

        elif args.service_type == "consumer":
            if args.consumer_name == "sentiment":
                service = SentimentConsumer(config)
            elif args.consumer_name == "aggregator":
                service = AggregatorConsumer(config)
            elif args.consumer_name == "signal":
                service = SignalConsumer()
            elif args.consumer_name == "logger":
                service = LoggingSink()

        # --- Service Execution ---
        if service:
            logger.info("Starting service...")
            service.run()
        else:
            parser.print_help()

    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Exiting service gracefully.")
    except Exception as e:
        logger.critical("Unhandled exception in service: %s", e, exc_info=True)
    finally:
        if service:
            service.close()


if __name__ == "__main__":
    main()

# """This is the main script of the entire app"""
#
# import time
#
# from goquant.core.engine import IngestionEngine, SentimentEngine
#
# start_time = time.time()
# print("Starting data ingestion...")
# ingestor = IngestionEngine()
# QUERY = "Tesla"
# TICKER = "NVDA"
#
# ingestion_result = ingestor.run(
#     query=QUERY, ticker=TICKER, limit=5, comment_limit=10, page_size=5
# )
# # print(result)
# # print("\n-----------------------\n")
# # print(f"Reddit:\n{result['reddit']}")
# # print("\n-----------------------\n")
# # print(f"News:\n{result['news']}")
# # print("\n-----------------------\n")
# # print(f"Market Data:\n{result['market']}")
#
# end_time = time.time()
# print(f"Data ingestion execution time: {end_time - start_time} seconds")
#
#
# start_time = time.time()
# print("\nStarting sentiment analysis...")
# sentiment_analyser = SentimentEngine()
#
# sentiment_result = sentiment_analyser.run(ingestion_result)
# print(sentiment_result)
# end_time = time.time()
# print(f"Sentiment analysis execution time: {end_time - start_time} seconds")
