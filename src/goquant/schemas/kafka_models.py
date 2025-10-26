from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RawTextMessage(BaseModel):
    """
    Schema for messages sent to the 'raw_text_data' topic.
    This is the output of the News/Reddit producers.
    """

    asset_name: str  # e.g., "Bitcoin", "Tesla"
    source: str  # e.g., "reddit", "news"
    timestamp_utc: float  # UNIX timestamp
    text: str  # The title or main text
    content: Optional[str] = None  # The body or description
    metadata: Dict[str, Any]  # Full original object (e.g., RedditPost)


class RawMarketMessage(BaseModel):
    """
    Schema for messages sent to the 'raw_market_data' topic.
    """

    ticker: str  # e.g., "BTC-USD", "TSLA"
    timestamp_utc: float  # UNIX timestamp
    price: float  # Current price
    volume: float  # Volume for the period


class AnalyzedSentimentMessage(BaseModel):
    """
    Schema for messages sent to the 'analyzed_sentiment' topic.
    """

    asset_name: str  # e.g., "Bitcoin", "Tesla"
    source: str  # e.g., "reddit", "news"
    timestamp_utc: float  # UNIX timestamp
    sentiment_score: float  # Score from -1.0 (neg) to 1.0 (pos)
    sentiment_probs: List[float]  # [pos, neg, neutral]
    metadata: Dict[str, Any]  # Original metadata


class AggregatedMetricsMessage(BaseModel):
    """
    Schema for 'aggregated_metrics' topic.
    This IS the "Fear & Greed" index for an asset.
    Maps to Output Param 1 (Sentiment momentum) and 3 (Correlation).
    """

    asset_name: str
    ticker: str
    timestamp_utc: float

    # Sentiment Metrics
    sentiment_1min_avg: Optional[float] = None
    sentiment_5min_avg: Optional[float] = None
    sentiment_15min_avg: Optional[float] = None
    sentiment_velocity: Optional[float] = None  # Change in sentiment

    # Market Metrics
    price: float
    volume: float
    price_change_1min_pct: Optional[float] = None
    price_change_5min_pct: Optional[float] = None

    # Fear & Greed Index
    fear_greed_score: float  # The final calculated index (0-100)


class TradeSignalMessage(BaseModel):
    """
    Schema for 'trade_signals' topic.
    Maps directly to Output Parameter 2: Trade Signals.
    """

    asset_name: str
    ticker: str
    timestamp_utc: float
    signal: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0.0 to 1.0
    reason: str  # e.g., "High sentiment, strong price momentum"
    fear_greed_score: float  # The score that triggered the signal
