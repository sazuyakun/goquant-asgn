"""Main data ingestion engine"""

import concurrent.futures as cf

from goquant.core.logging import logger
from goquant.data_collectors import MarketDataCollector, NewsCollector, RedditCollector


class IngestionEngine:
    def __init__(self):
        self.reddit_collector = RedditCollector()
        self.news_collector = NewsCollector()
        self.market_data_collector = MarketDataCollector()

    def run(self, query: str = "bitcoin", ticker="BTC-USD"):
        """
        Runs a single cycle of data ingestion from all sources
        """
        logger.info("Starting new ingestion cycle for query: %s", query)
        with cf.ThreadPoolExecutor(max_workers=3) as executor:
            # Reddit collector
            future_reddit = executor.submit(
                self.reddit_collector.fetch_data,
                query=query,
                limit=5,
            )
            # News collector
            future_news = executor.submit(
                self.news_collector.fetch_data, query=query, page_size=10
            )
            # Market data collector
            future_market = executor.submit(
                self.market_data_collector.fetch_data,
                ticker=ticker,
                period="1mo",
                interval="1d",
            )

            reddit_data = future_reddit.result()
            news_data = future_news.result()
            market_data = future_market.result()

            return {"reddit": reddit_data, "news": news_data, "market": market_data}
