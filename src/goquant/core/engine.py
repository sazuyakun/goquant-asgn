"""Main data ingestion engine"""

import concurrent.futures as cf
from typing import Dict

from goquant.core.logging import logger
from goquant.data_collectors import MarketDataCollector, NewsCollector, RedditCollector
from goquant.sentiment_analysis.onnx_finbert import OnnxFinBert


class IngestionEngine:
    def __init__(self):
        self.reddit_collector = RedditCollector()
        self.news_collector = NewsCollector()
        self.market_data_collector = MarketDataCollector()

    def preprocess_text(self, reddit_data, news_data):
        with cf.ThreadPoolExecutor(max_workers=2) as executor:
            future_reddit = executor.submit(
                self.reddit_collector.preprocess_data, reddit_data
            )
            future_news = executor.submit(
                self.news_collector.preprocess_data, news_data
            )

            preprocessed_reddit = future_reddit.result()
            preprocessed_news = future_news.result()

            return preprocessed_reddit, preprocessed_news

    def run(
        self,
        query: str = "bitcoin",
        ticker: str = "BTC-USD",
        limit: int = 1,
        comment_limit: int = 5,
        page_size: int = 1,
    ):
        """
        Runs a single cycle of data ingestion from all sources
        """
        logger.info("Starting new ingestion cycle for query: %s", query)
        with cf.ThreadPoolExecutor(max_workers=3) as executor:
            # Reddit collector
            future_reddit = executor.submit(
                self.reddit_collector.fetch_data,
                query=query,
                limit=limit,
                comment_limit=comment_limit,
            )
            # News collector
            future_news = executor.submit(
                self.news_collector.fetch_data, query=query, page_size=page_size
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

        reddit_data, news_data = self.preprocess_text(reddit_data, news_data)
        return {"reddit": reddit_data, "news": news_data, "market": market_data}


class SentimentEngine:
    def __init__(self):
        self.model = OnnxFinBert()

    def _analyze_reddit_sentiment(self, reddit_data):
        """
        Analyzes sentiment for Reddit data.
        """
        texts = []
        for post in reddit_data:
            texts.append(post.title)
            # if post.content:
            #     texts.append(post.content)
            if post.comments:
                for comment in post.comments:
                    texts.append(comment.comment)

        sentiments = self.model.predict(texts)
        return sentiments

    def _analyze_news_sentiment(self, news_data):
        """
        Analyzes sentiment for News data.
        """
        texts = []
        for article in news_data.articles:
            texts.append(article.title)
            if article.description:
                texts.append(article.description)
            # if article.content:
            #     texts.append(article.content)

        sentiments = self.model.predict(texts)
        return sentiments

    def run(self, data: Dict):
        """
        Analyzes sentiment for Reddit and News data.
        """
        # reddit_sentiments = self._analyze_reddit_sentiment(data["reddit"])
        # news_sentiments = self._analyze_news_sentiment(data["news"])
        # return {
        #     "reddit_sentiments": reddit_sentiments,
        #     "news_sentiments": news_sentiments,
        # }
        with cf.ThreadPoolExecutor(max_workers=2) as executor:
            future_reddit = executor.submit(
                self._analyze_reddit_sentiment, data["reddit"]
            )
            future_news = executor.submit(self._analyze_news_sentiment, data["news"])

            reddit_sentiments = future_reddit.result()
            news_sentiments = future_news.result()

            return {
                "reddit_sentiments": reddit_sentiments,
                "news_sentiments": news_sentiments,
            }
