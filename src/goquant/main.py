from goquant.data_collectors import MarketDataCollector, NewsCollector, RedditCollector

reddit_collector = RedditCollector()
news_collector = NewsCollector()
market_data_collector = MarketDataCollector()

# print(reddit_collector.fetch_data(query="cryptocurrency", limit=5)[0].title)
# fetched_news = news_collector.fetch_data(query="cryptocurrency", page_size=10)
# print(fetched_news.articles)

print(market_data_collector.fetch_data(ticker="BTC-USD"))
